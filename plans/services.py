from fastapi import status

from config.logging import logger
from coupons.context import CouponContext
from integrations.paddle_client import PaddleClient
from integrations.razorpay_client import RazorpayClient
from payments.exceptions import PaymentError
from payments.models import ProviderName
from plans.dao import PlansDAO, PlanCouponsDAO
from plans.exceptions import CouponUsageLimitExceededError, InvalidCouponDetailsError, PlanServiceError
from plans.schemas import PlanSchema, PlanUpdateSchema, PlanCouponSchema
from utils.connection_handler import ConnectionHandler


class PlansService:
    def __init__(self, connection_handler: ConnectionHandler = None):
        self.connection_handler = connection_handler
        self.plans_dao = PlansDAO(session=connection_handler.session)
        self.plan_coupons_dao = PlanCouponsDAO(session=connection_handler.session)
        self.razorpay_client = RazorpayClient()
        self.paddle_client = PaddleClient()

    async def get_all_plans(self):
        """Retrieve all plans using DAO."""
        return await self.plans_dao.get_all_plans()

    async def get_plan_by_id(self, plan_id: str):
        """Retrieve a specific plan by ID using DAO."""
        return await self.plans_dao.get_plan_by_id(plan_id)

    async def create_plan(self, plan_details: PlanSchema, psp_name: ProviderName):
        if psp_name == ProviderName.RAZORPAY:
            return await self.create_plan_razorpay(plan_details)
        elif psp_name == ProviderName.PADDLE:
            return await self.create_plan_paddle(plan_details)

    async def create_plan_razorpay(self, plan_details: PlanSchema):
        """Create a new plan."""
        # async with self.connection_handler.session.begin():
        try:
            if int(plan_details.amount) == 0:
                return await self.plans_dao.create_plan(plan_details, None)

            razorpay_plan_details = await self.razorpay_client.create_plan(plan_details)
            return await self.plans_dao.create_plan(plan_details, razorpay_plan_details["id"])
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error("Error creating plan: %s", str(e))
            raise PlanServiceError(detail="Unable to create plan. Verify if plan exists.")

    async def create_plan_paddle(self, plan_details: PlanSchema):
        """Create a new plan."""
        try:
            if int(plan_details.amount) == 0:
                return await self.plans_dao.create_plan(plan_details, psp_plan_id=None, psp_price_id=None)

            paddle_plan_details = await self.paddle_client.create_plan(plan_details)
            return await self.plans_dao.create_plan(
                plan_details=plan_details,
                psp_plan_id=paddle_plan_details["product_id"],
                psp_price_id=paddle_plan_details["price_id"]
            )
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error("Error creating plan: %s", str(e))
            raise PlanServiceError(detail="Unable to create plan. Verify if plan exists.")

    async def update_plan(self, plan_id: str, plan_details: PlanUpdateSchema):
        """Update an existing plan using DAO."""
        # async with self.connection_handler.session.begin():
        try:
            return await self.plans_dao.update_plan(plan_id, plan_details)
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error("Error updating plan %s: %s", plan_id, str(e))
            raise PlanServiceError(detail=str(e))

    async def delete_plan(self, plan_id: str):
        """Delete a plan using DAO."""
        try:
            await self.plans_dao.delete_plan(plan_id)
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error("Error deleting plan %s: %s", plan_id, str(e))
            raise PlanServiceError(detail=str(e))

    async def create_discounted_plan_if_needed(self, plan, discount_amount, coupon_id, coupon):
        """
        Create a new discounted plan if a discount is applied.
        """
        try:
            if discount_amount > 0:
                final_amount = max(0, float(plan.amount) - discount_amount)
                plan_schema_instance = PlanSchema(
                    name=f"{plan.name} (Discounted)",
                    amount=str(int(final_amount)),
                    currency=plan.currency,
                    billing_cycle=plan.billing_cycle,
                    description=plan.description or "Discounted Plan",
                    meta_data={"coupon_code": coupon_id},
                    is_custom=False
                )
                discounted_plan_response = await self.razorpay_client.create_plan(plan_schema_instance)
                new_discounted_plan = await self.plans_dao.create_internal_plan(
                    original_plan_id=plan.id,
                    razorpay_plan_id=discounted_plan_response['id'],
                    amount=final_amount,
                    metadata={
                        'coupon_code': coupon.code if coupon else None,
                        'is_internal': True
                    },
                )

                if coupon:
                    await self.plan_coupons_dao.update_coupon_plan_id(coupon, new_plan_id=new_discounted_plan.id)
                return new_discounted_plan
            return plan
        except Exception as e:
            await self.connection_handler.session.rollback()
            logger.error("Error while creating discounted plan: %s", str(e))
            raise PlanServiceError(detail=str(e))


class PlanCouponsService:
    def __init__(self, connection_handler: ConnectionHandler = None):
        self.connection_handler = connection_handler
        self.plan_coupons_dao = PlanCouponsDAO(session=connection_handler.session)
        self.plans_dao = PlansDAO(session=connection_handler.session)

    async def create_plan_coupon(self, coupon_details: PlanCouponSchema):
        """
        Create a coupon for a plan in the local DB (and optionally in an external service).
        """
        new_coupon = await self.plan_coupons_dao.create_plan_coupon(coupon_details, coupon_details.end_date)
        return new_coupon

    async def get_coupons_by_plan(self, plan_id: str):
        """
        Retrieve all coupons for a given plan ID.
        """
        coupons = await self.plan_coupons_dao.get_coupons_by_plan(plan_id)
        return coupons

    async def deactivate_coupon(self, coupon_id: str):
        """
        Deactivate a coupon (e.g., set `is_active=False`).
        """
        updated_coupon = await self.plan_coupons_dao.deactivate_coupon(coupon_id)
        return updated_coupon

    async def get_all_coupons(self):
        coupons = await self.plan_coupons_dao.get_all_coupons(True)
        return coupons

    async def validate_and_apply_coupon(self, coupon_id: str, plan_amount: float, current_time):
        """
        Validate the coupon and apply the discount using the Strategy Pattern.

        :param coupon_id: The coupon code.
        :param plan_amount: The original plan price.
        :param current_time: Current timestamp.
        :return: Tuple of discount amount and the validated coupon.
        """
        if not coupon_id:
            return 0.0, None

        coupon = await self.plan_coupons_dao.get_coupon_by_id(coupon_id)
        if not coupon:
            raise PaymentError("Invalid coupon code", status_code=status.HTTP_400_BAD_REQUEST)

        if not coupon.is_active or (coupon.end_date and coupon.end_date < current_time):
            raise InvalidCouponDetailsError("Coupon is expired or inactive")

        if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
            raise CouponUsageLimitExceededError()

        context = CouponContext(coupon.discount_type)
        discount_amount = context.apply_coupon(plan_amount, coupon.discount_value)

        return min(discount_amount, plan_amount), coupon

    async def increment_coupon_usage(self, coupon_id: str):
        """
        Increment the usage count of a coupon.

        :param coupon_id: The ID of the coupon.
        """
        await self.plan_coupons_dao.increment_coupon_usage(coupon_id)
