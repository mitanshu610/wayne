import asyncio
import time
from datetime import datetime
from fastapi import HTTPException, status

from config.logging import logger
from config.settings import loaded_config
from integrations.paddle_client import PaddleClient
from integrations.razorpay_client import RazorpayClient
from invoices.dao import InvoicesDAO
from payments.dao import PaymentsDAO
from payments.models import PaymentStatus, Subscriptions, PSPName
from plans.dao import PlansDAO
from rule_engine.dao import RulesDAO
from rule_engine.services import RulesService
from utils.connection_handler import ConnectionHandler
from utils.date_helper import DateHelper
from utils.redis_client import RedisClient
from clerk_integration.helpers import ClerkHelper
from webhooks.constants import TransactionPaymentStatus
from webhooks.dao import WebhookDAO


class WebhookService:
    def __init__(self, connection_handler: ConnectionHandler = None):
        self.connection_handler = connection_handler
        self.payments_dao = PaymentsDAO(session=connection_handler.session)
        self.invoices_dao = InvoicesDAO(session=connection_handler.session)
        self.webhook_dao = WebhookDAO(session=connection_handler.session)
        self.rules_service = RulesService(connection_handler=connection_handler)
        self.date_helper = DateHelper()
        self.razorpay_client = RazorpayClient()
        self.redis_client = RedisClient()

    async def handle_subscription_activated(self, payload):
        """Handle the 'subscription.activated' webhook event."""
        try:
            subscription_data = payload.get("payload", {}).get("subscription", {}).get("entity", {})
            subscription_id = subscription_data.get("id")
            subscription = await self.payments_dao.get_subscription_by_razorpay_id(subscription_id)

            if not subscription:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Subscription not found for the webhook")

            basic_subscription_of_user = await self.payments_dao.get_current_user_basic_subscription(
                subscription.user_id, subscription.org_id)
            if basic_subscription_of_user:
                basic_subscription_of_user.is_active = False
                basic_subscription_of_user.status = "cancelled"
                await self.payments_dao.update_subscription(basic_subscription_of_user)

            invoice_by_subscription = await self.invoices_dao.get_latest_invoice_by_subscription_id(
                str(subscription.id))
            if invoice_by_subscription:
                next_due_date = subscription_data.get("current_end")
                await self.invoices_dao.update_invoice_status(
                    invoice_id=invoice_by_subscription.psp_invoice_id,
                    status="paid",
                    next_due_date=next_due_date
                )

        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error("Error handling subscription.activated webhook: %s", str(e))
            raise e

    async def handle_payment_event(self, payload):
        """Handle the 'payment.captured' and 'payment.failed' webhook events."""
        try:
            created_at = payload.get("created_at")
            payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
            payment_id = payment_data.get("id")
            invoice_id = payment_data.get("invoice_id")
            amount = payment_data.get("amount")
            currency = payment_data.get("currency")
            payment_status = payment_data.get("status")

            invoice_details = await self.razorpay_client.get_invoice_details(invoice_id)
            subscription_id = invoice_details.get("subscription_id")
            subscription = await self.payments_dao.get_subscription_by_razorpay_id(subscription_id)

            if not subscription:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail=f"Subscription with ID {subscription_id} not found")

            user_id = subscription.user_id
            org_id = subscription.org_id
            subscription_details = await self.razorpay_client.get_subscription_details(subscription.psp_subscription_id)

            if payment_status == PaymentStatus.CAPTURED.value:
                await self.invoices_dao.create_invoice(
                    subscription.id,
                    invoice_id,
                    int(float(invoice_details["amount"]) / 100),
                    invoice_details["currency"],
                    invoice_details["status"],
                    subscription_details["current_end"],
                    user_id,
                    org_id,
                    invoice_details["short_url"]
                )

            await self.webhook_dao.record_payment_details(user_id, org_id, subscription.id, created_at, amount,
                                                          currency, payment_id, payment_status)

        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error("Error handling payment event webhook: %s", str(e))
            raise e

    async def handle_subscription_cancelled(self, payload):
        """Handle the 'subscription.cancelled' webhook event."""
        try:
            end_date = int(time.time())
            subscription_data = payload.get("payload", {}).get("subscription", {}).get("entity", {})
            subscription_id = subscription_data.get("id")
            subscription = await self.payments_dao.get_subscription_by_razorpay_id(subscription_id)

            if not subscription:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail=f"Subscription with ID {subscription_id} not found")

            subscription.end_date = end_date
            subscription.is_active = False
            subscription.status = subscription_data.get("status", "cancelled")
            await self.payments_dao.update_subscription(subscription)
            await self.rules_service.delete_plan_related_keys(subscription.user_id, subscription.org_id)
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error("Error handling subscription.cancelled webhook: %s", str(e))
            raise e

    async def handle_invoice_paid(self, payload):
        """Handle the 'invoice.paid' webhook event."""
        try:
            invoice_data = payload.get("payload", {}).get("invoice", {}).get("entity", {})
            invoice_id = invoice_data.get("id")
            subscription_id = invoice_data.get("subscription_id")
            invoice_status = invoice_data.get("status")

            subscription = await self.payments_dao.get_subscription_by_razorpay_id(subscription_id)
            subscription_details = await self.razorpay_client.get_subscription_details(subscription.psp_subscription_id)

            if not subscription:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail=f"Subscription with ID {subscription_id} not found")
            for attempt in range(5):
                try:
                    invoice = await self.invoices_dao.get_invoice_by_psp_id(invoice_id)
                    if invoice:
                        break
                    await asyncio.sleep(1)
                except Exception:
                    await asyncio.sleep(1)
            await self.invoices_dao.update_invoice_status(
                invoice_id=invoice_id,
                status=invoice_status,
                next_due_date=subscription_details["current_end"]
            )
            subscription.status = "active"
            subscription.is_active = True
            await self.payments_dao.update_subscription(subscription)
            logger.info("Invoice marked as paid")
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error("Error handling invoice.paid webhook: %s", str(e))
            raise e

    async def handle_invoice_expired(self, payload):
        """
        Handle the 'invoice.expired' webhook event.

        This function processes the invoice expiration payload and cancels the associated subscription via Razorpay API.

        :param payload: The webhook payload containing invoice details.
        """
        invoice_data = payload.get("payload", {}).get("invoice", {}).get("entity", {})
        invoice_id = invoice_data.get("id")
        subscription_id = invoice_data.get("subscription_id")

        subscription = await self.payments_dao.get_subscription_by_razorpay_id(subscription_id)

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription with ID {subscription_id} not found"
            )

        try:
            razorpay_response = await self.razorpay_client.end_subscription(subscription_id)
            logger.info(f"Subscription {subscription_id} cancelled via Razorpay due to invoice expiration.")
            await self.invoices_dao.update_invoice_status(invoice_id, "failed", None)
            subscription.end_date = int(time.time())
            subscription.status = razorpay_response.get("status", "cancelled")
            await self.payments_dao.update_subscription(subscription)
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error("Error cancelling subscription %s via Razorpay: %s", str(subscription_id), str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to cancel subscription {subscription_id} via Razorpay due to invoice expiration."
            )


class PaddleWebhookService:
    def __init__(self, connection_handler: ConnectionHandler = None):
        self.connection_handler = connection_handler
        self.payments_dao = PaymentsDAO(session=connection_handler.session)
        self.invoices_dao = InvoicesDAO(session=connection_handler.session)
        self.webhook_dao = WebhookDAO(session=connection_handler.session)
        self.rules_service = RulesService(connection_handler=connection_handler)
        self.plans_dao = PlansDAO(session=connection_handler.session)
        self.paddle_client = PaddleClient()

    async def handle_transaction_completed_failed(self, event):
        try:
            invoice_url = ""
            next_due = None
            data = event.get("data")
            custom_data = data.get("custom_data")
            is_payment_successful = data["payments"][0]["status"] == TransactionPaymentStatus.CAPTURED

            if custom_data and custom_data["subscription_id"]:
                subscription: Subscriptions = await self.payments_dao.get_subscription_by_id(
                    subscription_id=custom_data["subscription_id"])
                subscription.psp_subscription_id = data.get("subscription_id")
            else:
                subscription: Subscriptions = await self.payments_dao.get_subscription_by_psp_subscription_id(
                    psp_subscription_id=data.get("subscription_id"))
            subscription.is_active = is_payment_successful
            subscription.status = "active" if is_payment_successful else "failed"
            await self.payments_dao.update_subscription(subscription=subscription)

            invoice_retries = 3
            while invoice_retries > 0:
                if data.get("invoice_id"):
                    try:
                        invoice = await self.paddle_client.get_transaction_invoice(transaction_id=data["id"])
                        invoice_url = invoice.get("data").get("url") if invoice and invoice.get("data") else ""
                        break
                    except Exception as exp:
                        logger.info(f"Failed to get invoice for transaction: {data['id']}")

            if data["billing_period"]:
                dt = datetime.strptime(data["billing_period"]["ends_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
                next_due = dt.timestamp()

            await self.invoices_dao.create_invoice(
                subscription_id=subscription.id,
                invoice_id=data.get("invoice_id"),
                amount=subscription.amount,
                currency=subscription.currency,
                status="paid" if is_payment_successful else "failed",
                next_due=next_due,
                user_id=subscription.user_id,
                org_id=subscription.org_id,
                short_url=invoice_url,
                transaction_id=data["id"],
                psp_name=PSPName.PADDLE.name
            )

            dt = datetime.strptime(data["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
            await self.webhook_dao.record_payment_details(
                user_id=subscription.user_id,
                org_id=subscription.org_id,
                subscription_id=subscription.id,
                amount=subscription.amount,
                currency=subscription.currency,
                payment_id=data.get("id"),
                payment_status=PaymentStatus.CAPTURED if is_payment_successful else PaymentStatus.FAILED,
                created_at=dt.timestamp(),
                psp_name=PSPName.PADDLE
            )
            if not is_payment_successful:
                logger.info(
                    f"Payment attempt is not successful for transaction {data.get('id')} "
                    f"and psp_subscription {data.get('subscription_id')}")

            clerk_helper = ClerkHelper(loaded_config.clerk_secret_key)
            if is_payment_successful:
                active_plan = await self.plans_dao.get_plan_by_id(subscription.plan_id)
                if subscription.org_id:
                    await clerk_helper.update_organization_metadata(subscription.org_id, public_metadata={
                        "subscription": {
                            "active_plan_id": subscription.plan_id,
                            "active_plan_slug": active_plan.slug
                        }
                    })
                else:
                    await clerk_helper.update_user_metadata(subscription.user_id, public_metadata={
                        "subscription": {
                            "active_plan_id": subscription.plan_id,
                            "active_plan_slug": active_plan.slug
                        }
                    })
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error("Error handling transaction.complete webhook: %s", str(e))
            raise e

    async def handle_subscription_cancelled(self, event):
        """Handle the 'subscription.cancelled' webhook event."""
        try:
            end_date = int(time.time())
            subscription_data = event.get("data")
            subscription_id = subscription_data.get("id")
            subscription = await self.payments_dao.get_subscription_by_psp_subscription_id(subscription_id)

            if not subscription:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail=f"Subscription with ID {subscription_id} not found")

            clerk_helper = ClerkHelper(loaded_config.clerk_secret_key)
            if subscription.org_id:
                await clerk_helper.update_organization_metadata(subscription.org_id, public_metadata={
                    "subscription": {
                        "active_plan_id": None,
                        "active_plan_slug": None
                    }
                })
            else:
                await clerk_helper.update_user_metadata(subscription.user_id, public_metadata={
                    "subscription": {
                        "active_plan_id": None,
                        "active_plan_slug": None
                    }
                })

            subscription.end_date = end_date
            subscription.is_active = False
            subscription.status = "cancelled"
            await self.payments_dao.update_subscription(subscription)
            await self.rules_service.delete_plan_related_keys(subscription.user_id, subscription.org_id)
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error("Error handling subscription.cancelled webhook: %s", str(e))
            raise e
