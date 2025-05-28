import time
from datetime import datetime

from fastapi import status

from config.logging import logger
from config.settings import loaded_config
from integrations.paddle_client import PaddleClient
from integrations.razorpay_client import RazorpayClient
from payments.dao import PaymentsDAO
from payments.exceptions import (
    PaymentError,
    SubscriptionNotFoundError
)
from payments.models import BillingCycle, ProviderName, PSPName
from payments.schemas import CreateSubscription, PlanSlugs
from plans.dao import PlansDAO
from plans.services import PlanCouponsService, PlansService
from utils.common import UserData
from utils.connection_handler import ConnectionHandler
from utils.redis_client import RedisClient


class PaymentsService:

    def __init__(self, connection_handler: ConnectionHandler = None):
        self.connection_handler = connection_handler
        self.payments_dao = PaymentsDAO(session=connection_handler.session)
        self.plans_dao = PlansDAO(session=connection_handler.session)
        self.coupon_service = PlanCouponsService(connection_handler)
        self.plans_service = PlansService(connection_handler)
        self.razorpay_client = RazorpayClient()
        self.paddle_client = PaddleClient()
        self.redis_client = RedisClient()

    async def delete_subscription_idempotency(self, user_data: UserData):
        """
        Ensure idempotency using Redis to avoid duplicate subscriptions.
        """
        idempotency_key = f"subscription_idempotency_org:{user_data.userId}:{user_data.orgId}"
        if await self.redis_client.exists_key(idempotency_key):
            await self.redis_client.delete_key(idempotency_key)

    async def _ensure_customer_exists(self, user_data: UserData):
        """
        Ensure the customer exists in the database. If not, create a new customer via Razorpay
        and store it in the database.
        """
        customer = await self.payments_dao.get_customer_by_user_and_org_id(user_data.userId, user_data.orgId)
        if not customer:
            razorpay_customer = await self.razorpay_client.create_customer(user_data)
            customer = await self.payments_dao.create_customer(user_data, razorpay_customer, "Razorpay")
        return customer

    async def create_subscription(self, subscription_details: CreateSubscription, user_data: UserData,
                                  psp_name: ProviderName):
        if psp_name == ProviderName.RAZORPAY:
            return await self.create_subscription_razorpay(subscription_details, user_data)
        elif psp_name == ProviderName.PADDLE:
            return await self.create_subscription_paddle(subscription_details, user_data)

    async def create_subscription_razorpay(self, subscription_details: CreateSubscription, user_data: UserData):
        start_date = int(time.time())

        try:
            existing_subscription = await self.payments_dao.get_subscriptions_by_user_and_org_id(
                user_data.userId, user_data.orgId
            )

            if existing_subscription:
                plan = await self.plans_dao.get_plan_by_id(existing_subscription.plan_id)
                if existing_subscription and plan.slug != PlanSlugs.BASIC.value:
                    raise PaymentError("Subscription for the organisation is already active",
                                       status_code=status.HTTP_409_CONFLICT)
                else:
                    existing_subscription.status = "cancelled"
                    existing_subscription.is_active = False
                    await self.payments_dao.update_subscription(existing_subscription)

            plan = await self.plans_dao.get_plan_by_id(subscription_details.plan_id)

            has_trial = await self.payments_dao.has_user_taken_trial(user_data.userId, user_data.orgId)
            if plan.slug == PlanSlugs.BASIC.value and not has_trial:
                logger.info("Granting 14-day trial of Pro Plan")

                pro_plan = await self.plans_dao.get_plan_by_slug(PlanSlugs.PRO_MONTHLY.value)
                trial_end_date = start_date + loaded_config.trial_expiration_time
                subscription_details.is_active = True
                trial_subscription = await self.payments_dao.save_subscription(
                    subscription_details, pro_plan, start_date, {"id": None, "status": "trial"}, user_data,
                    is_trial=True,
                )
                await self.payments_dao.schedule_downgrade_to_basic(user_data.userId, user_data.orgId, trial_end_date)
                return trial_subscription

            if plan.is_custom:
                raise PaymentError("Custom plans are not supported for automated subscriptions",
                                   status_code=status.HTTP_400_BAD_REQUEST)

            # Use strategy-based coupon system
            discount_amount, coupon = await self.coupon_service.validate_and_apply_coupon(
                subscription_details.coupon_id, float(plan.amount), start_date
            )

            final_plan = await self.plans_service.create_discounted_plan_if_needed(
                plan, discount_amount, subscription_details.coupon_id, coupon
            )
            plan_total_count = 30 if plan.billing_cycle == "monthly" else 3

            if int(plan.amount) > 0:
                subscription_response = await self.razorpay_client.create_subscription(
                    final_plan.razorpay_plan_id, total_count=plan_total_count
                )
                subscription = await self.payments_dao.save_subscription(
                    subscription_details, final_plan, start_date, subscription_response, user_data
                )
                subscription.update({
                    "psp_client_token": loaded_config.razorpay_api_key
                })
            else:
                subscription_details.is_active = True
                subscription = await self.payments_dao.save_subscription(
                    subscription_details, final_plan, start_date, {"id": None, "status": "active"}, user_data
                )
            if coupon:
                await self.coupon_service.increment_coupon_usage(coupon.id)

            logger.info("Subscription created successfully for user")
            return subscription

        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error("Error during subscription creation: %s", str(e))
            raise e

    async def create_subscription_paddle(self, subscription_details: CreateSubscription, user_data: UserData):
        start_date = int(time.time())
        try:
            existing_subscription = await self.payments_dao.get_subscriptions_by_user_and_org_id(
                user_data.userId, user_data.orgId
            )

            if existing_subscription:
                plan = await self.plans_dao.get_plan_by_id(existing_subscription.plan_id)
                if subscription_details.plan_id == plan.id:
                    raise PaymentError(f"{plan.name} subscription is already active")
                if existing_subscription and plan.slug != PlanSlugs.BASIC.value:
                    raise PaymentError("Subscription for the organisation is already active",
                                       status_code=status.HTTP_409_CONFLICT)
                else:
                    existing_subscription.status = "cancelled"
                    existing_subscription.is_active = False
                    await self.payments_dao.update_subscription(existing_subscription)

            plan = await self.plans_dao.get_plan_by_id(plan_id=subscription_details.plan_id)

            has_trial = await self.payments_dao.has_user_taken_trial(user_data.userId, user_data.orgId)
            if plan.slug == PlanSlugs.BASIC.value and not has_trial:
                logger.info("Granting 14-day trial of Pro Plan")

                pro_plan = await self.plans_dao.get_plan_by_slug(PlanSlugs.PRO_MONTHLY.value)
                trial_end_date = start_date + loaded_config.trial_expiration_time
                subscription_details.is_active = True
                trial_subscription = await self.payments_dao.save_subscription(
                    subscription_details, pro_plan, start_date, {"id": None, "status": "trial"}, user_data,
                    is_trial=True,
                )
                await self.payments_dao.schedule_downgrade_to_basic(user_data.userId, user_data.orgId, trial_end_date)
                return trial_subscription

            if plan.is_custom:
                raise PaymentError("Custom plans are not supported for automated subscriptions",
                                   status_code=status.HTTP_400_BAD_REQUEST)

            if int(plan.amount) > 0:
                subscription_details.is_active = False
                subscription = await self.payments_dao.save_subscription(
                    subscription_details, plan, start_date, {"id": None, "status": "draft"}, user_data
                )
                transaction = await self.paddle_client.create_transaction(
                    plan_details=plan,
                    subscription_details=subscription_details,
                    subscription_id=subscription["id"],
                    user_data=user_data
                )
                subscription.update({
                    "transaction_id": transaction["data"]["id"],
                    "psp_client_token": loaded_config.paddle_client_token
                })
                return subscription
            else:
                subscription_details.is_active = True
                subscription = await self.payments_dao.save_subscription(
                    subscription_details, plan, start_date, {"id": None, "status": "active"}, user_data
                )
                return subscription
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error("Error during subscription creation: %s", str(e))
            raise e

    async def get_subscription_by_id(self, subscription_id: str):
        """
        Retrieve subscription details by subscription ID.
        :param subscription_id: The ID of the subscription.
        """
        subscription = await self.payments_dao.get_subscription_by_id(subscription_id)
        if not subscription:
            raise SubscriptionNotFoundError()
        return subscription

    async def get_subscriptions_by_user_org(self, user_id, org_id, first_name, last_name):
        """
        Retrieve subscriptions for a specific user and organization.
        :param user_id: User ID.
        :param org_id: Organization ID.
        """
        subscription = await self.payments_dao.get_subscriptions_by_user_and_org_id(user_id, org_id)
        if not subscription:
            plan_details = await self.plans_dao.get_plan_by_id(loaded_config.fallback_plan_id)
            return {
                "amount": plan_details.amount,
                "billing_cycle": BillingCycle(plan_details.billing_cycle),
                "plan_name": plan_details.name,
                "plan_description": plan_details.description
            }

        plan_details = await self.plans_dao.get_plan_by_id(subscription.plan_id)
        if not plan_details:
            raise PaymentError(
                message="Plan details not found for the subscription",
                status_code=status.HTTP_404_NOT_FOUND
            )

        if plan_details.slug != PlanSlugs.BASIC.value:
            if subscription.psp_name == PSPName.PADDLE:
                paddle_subscription = await self.paddle_client.get_subscription_details(
                    subscription_id=subscription.psp_subscription_id)

                current_start = current_end = None
                if current_billing_period := paddle_subscription["data"]["current_billing_period"]:
                    current_start = datetime.strptime(current_billing_period["starts_at"],
                                                      "%Y-%m-%dT%H:%M:%S.%fZ").timestamp() if current_billing_period.get(
                        "starts_at") else None
                    current_end = datetime.strptime(current_billing_period["ends_at"],
                                                    "%Y-%m-%dT%H:%M:%S.%fZ").timestamp() if current_billing_period.get(
                        "ends_at") else None
                subscription_details = {
                    "current_start": current_start,
                    "current_end": current_end,
                    "cancel_at_cycle_end": subscription.cancel_at_cycle_end
                }
            else:
                subscription_details = await self.razorpay_client.get_subscription_details(
                    subscription.psp_subscription_id)
                subscription_details["cancel_at_cycle_end"] = subscription.cancel_at_cycle_end
        else:
            subscription_details = subscription.to_dict()

        subscription_with_plan_details = {
            **subscription_details,
            "amount": subscription.amount,
            "billing_cycle": BillingCycle(subscription.billing_cycle),
            "plan_name": plan_details.name,
            "plan_description": plan_details.description
        }

        subscription_with_plan_details["amount"] = int(float(subscription_with_plan_details["amount"]) / 100)

        return subscription_with_plan_details

    async def unsubscribe(self, user_id: int, org_id: int):
        """
        Unsubscribe plan from payment service provider
        :param user_id: User id
        :param org_id: organisation id
        """
        try:
            subscription_details = await self.payments_dao.get_subscriptions_by_user_and_org_id(user_id, org_id)
            if not subscription_details:
                raise SubscriptionNotFoundError()

            if int(subscription_details.amount) == 0:
                subscription_details.is_active = False
                subscription_details.status = "cancelled"
            else:
                if subscription_details.psp_name == PSPName.PADDLE:
                    await self.paddle_client.end_subscription(subscription_details.psp_subscription_id)
                    subscription_details.cancel_at_cycle_end = True
                elif subscription_details.psp_name == PSPName.RAZORPAY:
                    await self.razorpay_client.end_subscription(subscription_details.psp_subscription_id)
                    subscription_details.cancel_at_cycle_end = True
                else:
                    return None

            await self.payments_dao.update_subscription(subscription_details)
            return int(subscription_details.amount) == 0
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error("Error during unsubscribe process for user: %s ", str(e))
            raise e

    async def upgrade_subscription(self, subscription_details: CreateSubscription, user_data: UserData):
        """
        Upgrade the user's subscription by canceling the current subscription and creating a new one.
        :param subscription_details: Details of the new subscription plan.
        :param user_data: User data containing user ID and organization ID.
        """
        try:
            current_subscription = await self.payments_dao.get_subscriptions_by_user_and_org_id(user_data.userId,
                                                                                                user_data.orgId)
            if not current_subscription:
                raise SubscriptionNotFoundError()

            if int(current_subscription.amount) > 0:
                await self.razorpay_client.end_subscription(current_subscription.psp_subscription_id,
                                                            cancel_at_end=False)

            current_subscription.is_active = False
            await self.payments_dao.update_subscription(current_subscription)
            new_subscription = await self.create_subscription_razorpay(subscription_details, user_data)

            logger.info("Subscription upgraded successfully for user: %s", str(user_data.userId))
            return new_subscription

        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error("Error during subscription upgrade: %s", str(e))
            raise e
