from config.settings import loaded_config
from integrations.base_client import BaseAPIClient, AuthMethod
from plans.schemas import PlanSchema
from utils.common import UserData


class PaddleClient(BaseAPIClient):

    def __init__(self):
        super().__init__(
            base_url=loaded_config.paddle_api_base_url,
            api_secret=loaded_config.paddle_api_secret,
            auth_method=AuthMethod.BEARER
        )

    async def create_transaction(self, plan_details, subscription_details, subscription_id, user_data: UserData):
        body = {
            "items": [{
                "price_id": plan_details.psp_price_id,
                "quantity": 1
            }],
            "customer": {
                "email": user_data.email
            },
            "custom_data": {
                "plan_id": str(plan_details.id),
                "subscription_id": str(subscription_id)
            }
        }
        return await self._make_request("POST", "/transactions", body)

    async def create_plan(self, plan_details: PlanSchema):
        product_payload = {
            "name": plan_details.name,
            "tax_category": "digital-goods",
            "description": plan_details.description
        }
        product = await self._make_request("POST", "/products", product_payload)

        price_payload = {
            "name": plan_details.name,
            "product_id": product["data"]["id"],
            "description": plan_details.description,
            "unit_price": {
                "amount": plan_details.amount,
                "currency_code": "USD"
            },
            "billing_cycle": {
                "interval": "day",
                "frequency": 1
            },
            "tax_mode": "account_setting",
            "quantity": {
                "minimum": 1,
                "maximum": 1
            }
        }
        price = await self._make_request("POST", "/prices", price_payload)
        return {
            "product_id": product["data"]["id"],
            "price_id": price["data"]["id"]
        }

    async def get_transaction_invoice(self, transaction_id: str):
        return await self._make_request("GET", f"/transactions/{transaction_id}/invoice")

    async def get_subscription_details(self, subscription_id: str):
        return await self._make_request("GET", f"/subscriptions/{subscription_id}")

    async def end_subscription(self, subscription_id):
        effective_from = "immediately" if loaded_config.subscription_cancellation_at == "immediately" \
            else "next_billing_period"
        payload = {
            "effective_from": effective_from
        }

        return await self._make_request("POST", f"/subscriptions/{subscription_id}/cancel", payload)
