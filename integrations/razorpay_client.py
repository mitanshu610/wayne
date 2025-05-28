from datetime import datetime, timedelta, timezone
from config.settings import loaded_config
from integrations.base_client import BaseAPIClient
from clerk_integration.utils import UserData
from utils.date_helper import DateHelper


class RazorpayClient(BaseAPIClient):
    """
    A client to interact with Razorpay APIs.
    """
    def __init__(self, api_secret: str = None):
        super().__init__(
            base_url=loaded_config.razorpay_api_base_url,
            api_secret=api_secret or loaded_config.razorpay_api_secret
        )

    async def create_subscription(self, plan_id: str, total_count: int = 100, quantity: int = 1, notify: bool = True):
        """
        Create a subscription.
        """
        body = {
            "plan_id": plan_id,
            "total_count": total_count,
            "quantity": quantity,
            "customer_notify": int(notify)
        }
        return await self._make_request("POST", "/subscriptions", body)

    async def end_subscription(self, subscription_id: str, cancel_at_end: bool = True):
        """
        Cancel a subscription.
        """
        body = {"cancel_at_cycle_end": cancel_at_end}
        return await self._make_request("POST", f"/subscriptions/{subscription_id}/cancel", body)

    async def create_plan(self, plan_details):
        """
        Create a plan.
        """
        body = {
            "period": plan_details.billing_cycle.lower(),
            "interval": 1,
            "item": {
                "name": plan_details.name,
                "amount": int(plan_details.amount),
                "currency": plan_details.currency,
                "description": plan_details.description or "",
            }
        }
        return await self._make_request("POST", "/plans", body)

    async def get_invoice_details(self, invoice_id: str):
        """
        Fetch invoice details.
        """
        return await self._make_request("GET", f"/invoices/{invoice_id}")

    async def issue_invoice(self, invoice_id: str):
        """
        Issue an invoice.
        """
        return await self._make_request("POST", f"/invoices/{invoice_id}/issue")

    async def draft_invoice(self, customer_id, plan_name, plan_amount, plan_currency, plan_description):
        """
        Draft an invoice.
        """
        body = {
            "type": "invoice",
            "date": DateHelper.convert_date_to_epoch(),
            "customer_id": customer_id,
            "line_items": [{
                "name": plan_name,
                "description": plan_description,
                "amount": plan_amount,
                "currency": plan_currency
            }],
            "expire_by": DateHelper.convert_date_to_epoch(datetime.now(timezone.utc) + timedelta(days=2)),
            "draft": 1
        }
        return await self._make_request("POST", "/invoices", body)

    async def create_customer(self, user_data: UserData):
        """
        Create customer on razorpay
        """
        customer_payload = {
            "name": user_data.firstName + " " + user_data.lastName,
            "email": user_data.email,
            "fail_existing": 0
        }
        return await self._make_request("POST", "/customers", customer_payload)

    async def get_payment_downtimes(self):
        """
        Get downtimes of the payments gateways
        """
        return await self._make_request("GET", "/payments/downtimes")

    async def get_subscription_details(self, subscription_id):
        """
        Get downtimes of the payments gateways
        """
        return await self._make_request("GET", f"/subscriptions/{subscription_id}")