from typing import Optional

import uuid6
from fastapi import status
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from config.logging import logger
from payments.exceptions import PaymentError
from plans.exceptions import (
    PlanNotFoundError,
    CouponNotFoundError,
    PlanServiceError, DuplicateCouponError
)
from plans.models import Plan, PlanCoupon
from plans.schemas import PlanSchema, PlanUpdateSchema, PlanCouponSchema
from prometheus.metrics import DB_QUERY_LATENCY
from utils.decorators import latency


class PlansDAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    @latency(metric=DB_QUERY_LATENCY)
    async def get_all_plans(self):
        """Retrieve all plans."""
        try:
            result = await self.session.execute(
                select(Plan).where(
                    (Plan.meta_data['is_internal'].as_boolean() == False) | (Plan.meta_data['is_internal'].is_(None))
                )
            )
            plans = result.scalars().all()
            return plans
        except Exception as e:
            logger.error("Error retrieving plans: %s", str(e))
            raise PlanServiceError(detail=str(e))

    @latency(metric=DB_QUERY_LATENCY)
    async def get_plan_by_id(self, plan_id):
        """Retrieve a specific plan by ID."""
        try:
            result = await self.session.execute(
                select(Plan).filter(Plan.id == plan_id)
            )
            plan = result.scalars().first()
            if not plan:
                raise PlanNotFoundError(plan_id)
            return plan
        except PlanNotFoundError:
            raise
        except Exception as e:
            logger.error("Error retrieving plan with ID %s: %s", str(plan_id), str(e))
            raise PlanServiceError(detail=str(e))

    @latency(metric=DB_QUERY_LATENCY)
    async def create_plan(self, plan_details: PlanSchema, psp_plan_id: str | None, psp_price_id: str = None):
        """Create a new plan."""
        try:
            new_plan_id = uuid6.uuid6()
            new_plan = Plan(
                id=new_plan_id,
                psp_plan_id=psp_plan_id,
                psp_price_id=psp_price_id,
                **plan_details.dict()
            )
            self.session.add(new_plan)
            await self.session.commit()
            await self.session.refresh(new_plan)
            logger.info("Plan created successfully with ID: %s", str(new_plan_id))
            return new_plan
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Database error while creating plan: %s", str(e))
            raise PlanServiceError(detail=str(e))
        except Exception as e:
            await self.session.rollback()
            logger.error("Unexpected error while creating plan: %s", str(e))
            raise PlanServiceError(detail=str(e))

    @latency(metric=DB_QUERY_LATENCY)
    async def update_plan(self, plan_id: str, plan_details: PlanUpdateSchema):
        """Update an existing plan."""
        try:
            result = await self.session.execute(
                select(Plan).filter(Plan.id == plan_id)
            )
            plan = result.scalars().first()
            if not plan:
                raise PlanNotFoundError(plan_id)

            for key, value in plan_details.dict(exclude_unset=True).items():
                setattr(plan, key, value)

            await self.session.commit()
            logger.info("Plan updated successfully with ID: %s", str(plan_id))
            return plan
        except PlanNotFoundError:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error("Error updating plan with ID %s: %s", str(plan_id), str(e))
            raise PlanServiceError(detail=str(e))

    @latency(metric=DB_QUERY_LATENCY)
    async def delete_plan(self, plan_id: str):
        """Delete a plan."""
        try:
            result = await self.session.execute(
                select(Plan).filter(Plan.id == plan_id)
            )
            plan = result.scalars().first()
            if not plan:
                raise PlanNotFoundError(plan_id)

            await self.session.delete(plan)
            await self.session.commit()
            logger.info("Plan deleted successfully with ID: %s", str(plan_id))
        except PlanNotFoundError:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error("Error deleting plan with ID %s: %s", str(plan_id), str(e))
            raise PlanServiceError()

    async def create_internal_plan(self, original_plan_id: str, razorpay_plan_id, amount: float, metadata: dict):
        """
        Create internal plan for discounted prices
        """
        new_plan_id = uuid6.uuid6()
        new_plan = Plan(
            id=new_plan_id,
            name=f"Internal Plan for {original_plan_id}",
            amount=str(amount),
            currency="INR",
            billing_cycle="monthly",
            razorpay_plan_id=razorpay_plan_id,
            is_custom=False,
            meta_data=metadata,
        )
        self.session.add(new_plan)
        await self.session.commit()
        return new_plan

    @latency(metric=DB_QUERY_LATENCY)
    async def get_plan_by_slug(self, slug: str):
        """
        Retrieve a specific plan by slug.
        Raises PlanNotFoundError if no plan is found.
        """
        try:
            result = await self.session.execute(
                select(Plan).filter(Plan.slug == slug)
            )
            plan = result.scalars().first()
            if not plan:
                raise PlanNotFoundError(slug)
            return plan
        except PlanNotFoundError:
            raise
        except Exception as e:
            logger.error("Error retrieving plan with slug %s: %s", str(slug), str(e))
            raise PlanServiceError(detail=str(e))


class PlanCouponsDAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    @latency(metric=DB_QUERY_LATENCY)
    async def create_plan_coupon(self, coupon_details: PlanCouponSchema, calculated_end_date):
        """Create a new coupon for a plan."""
        try:
            new_coupon_id = uuid6.uuid6()
            new_coupon = PlanCoupon(
                id=new_coupon_id,
                end_date=calculated_end_date,
                usage_limit=coupon_details.usage_limit,
                discount_value=coupon_details.discount_value,
                discount_type=coupon_details.discount_type,
                code=coupon_details.code
            )
            self.session.add(new_coupon)
            await self.session.commit()
            await self.session.refresh(new_coupon)
            logger.info("Coupon created successfully with ID: %s", str(new_coupon_id))
            return new_coupon
        except IntegrityError:
            await self.session.rollback()
            logger.error("Duplicate coupon code already exists")
            raise DuplicateCouponError()
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error("Database error while creating coupon: %s", str(e))
            raise PlanServiceError(detail=str(e))
        except Exception as e:
            await self.session.rollback()
            logger.error("Unexpected error while creating coupon: %s", str(e))
            raise PlanServiceError(detail=str(e))

    @latency(metric=DB_QUERY_LATENCY)
    async def get_coupons_by_plan(self, plan_id: str):
        """Retrieve all active coupons for a specific plan."""
        try:
            result = await self.session.execute(
                select(PlanCoupon).filter(
                    PlanCoupon.plan_id == plan_id,
                    PlanCoupon.is_active == True
                )
            )
            coupons = result.scalars().all()
            return coupons
        except Exception as e:
            logger.error("Error retrieving coupons for plan %s: %s", str(plan_id), str(e))
            raise PlanServiceError(detail=str(e))

    @latency(metric=DB_QUERY_LATENCY)
    async def get_coupon_by_id(self, coupon_id: str):
        """
        Retrieve a specific coupon by ID.
        Raises CouponNotFoundError if no coupon is found.
        """
        try:
            result = await self.session.execute(
                select(PlanCoupon).filter(PlanCoupon.id == coupon_id, PlanCoupon.is_active == True)
            )
            coupon = result.scalars().first()
            if not coupon:
                raise CouponNotFoundError(coupon_id)
            return coupon
        except CouponNotFoundError:
            raise
        except Exception as e:
            logger.error("Error retrieving coupon with ID %s: %s", str(coupon_id), str(e))
            raise PlanServiceError(detail=str(e))

    @latency(metric=DB_QUERY_LATENCY)
    async def deactivate_coupon(self, coupon_id: str):
        """
        Deactivate a coupon (set is_active=False).
        Returns the updated coupon.
        """
        try:
            coupon = await self.get_coupon_by_id(coupon_id)
            coupon.is_active = False
            await self.session.commit()
            await self.session.refresh(coupon)
            logger.info("Coupon deactivated successfully with ID: %s", str(coupon_id))
            return coupon
        except CouponNotFoundError:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error("Error deactivating coupon %s: %s", str(coupon_id), str(e))
            raise PlanServiceError(detail=str(e))

    @latency(metric=DB_QUERY_LATENCY)
    async def get_all_coupons(self, is_active: Optional[bool] = None):
        """
        Retrieve all coupons from the database.
        Optionally filter by their active status.
        """
        try:
            query = select(PlanCoupon)
            if is_active is not None:
                query = query.filter(PlanCoupon.is_active == is_active)

            result = await self.session.execute(query)
            coupons = result.scalars().all()
            logger.info("Retrieved %d coupons", len(coupons))
            return coupons
        except Exception as e:
            logger.error("Error retrieving coupons: %s", str(e))
            raise PlanServiceError(detail=str(e))

    @latency(metric=DB_QUERY_LATENCY)
    async def increment_coupon_usage(self, coupon_id: str):
        """
        Increment the usage count of a coupon.
        """
        try:
            await self.session.execute(
                update(PlanCoupon)
                .where(PlanCoupon.id == coupon_id)
                .values(usage_count=PlanCoupon.usage_count + 1)
            )
            await self.session.commit()
            logger.info("Coupon usage incremented for coupon_id: %s", str(coupon_id))
        except Exception as e:
            logger.error("Failed to increment coupon usage for coupon_id: %s - %s", str(coupon_id), str(e))
            raise PaymentError(
                message="Failed to update coupon usage.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @latency(metric=DB_QUERY_LATENCY)
    async def update_coupon_plan_id(self, coupon, new_plan_id: str):
        """
        Update the coupon's plan_id with the newly created discounted plan ID.
        """
        try:
            coupon.plan_id = new_plan_id
            self.session.add(coupon)
            await self.session.commit()
            logger.info("Updated coupon %s with new plan ID: %s", str(coupon.id), str(new_plan_id))
        except Exception as e:
            logger.error("Failed to update coupon %s with new plan ID: %s", str(coupon.id), str(e))
            raise PaymentError(
                message="Failed to update coupon with new plan ID.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
