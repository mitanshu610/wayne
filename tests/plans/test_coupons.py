from unittest.mock import MagicMock, AsyncMock

import pytest

from plans.exceptions import InvalidCouponDetailsError, CouponUsageLimitExceededError
from plans.schemas import DiscountType
from plans.services import PlanCouponsService, PlansService


@pytest.mark.asyncio
async def test_validate_and_apply_coupon(mock_connection_handler):
    coupon_service = PlanCouponsService(mock_connection_handler)

    # Create a mock coupon with explicit attribute values
    coupon = MagicMock()
    coupon.is_active = True
    coupon.discount_type = DiscountType.FLAT.value
    coupon.discount_value = 50
    coupon.usage_limit = 5
    coupon.usage_count = 3
    coupon.end_date = "2025-01-30T00:00:00Z"

    coupon_service.plan_coupons_dao.get_coupon_by_id = AsyncMock(return_value=coupon)

    discount, validated_coupon = await coupon_service.validate_and_apply_coupon("coupon_123", 200,
                                                                                "2025-01-28T00:00:00Z")

    assert discount == 50
    assert validated_coupon == coupon
    coupon_service.plan_coupons_dao.get_coupon_by_id.assert_called_once_with("coupon_123")


@pytest.mark.asyncio
async def test_validate_coupon_expired(mock_connection_handler):
    coupon_service = PlanCouponsService(mock_connection_handler)
    expired_coupon = MagicMock(is_active=False, end_date="2025-01-01T00:00:00Z")
    coupon_service.plan_coupons_dao.get_coupon_by_id = AsyncMock(return_value=expired_coupon)

    with pytest.raises(InvalidCouponDetailsError):
        await coupon_service.validate_and_apply_coupon("coupon_123", 200, "2025-01-28T00:00:00Z")


@pytest.mark.asyncio
async def test_validate_coupon_usage_limit_exceeded(mock_connection_handler):
    coupon_service = PlanCouponsService(mock_connection_handler)

    coupon = MagicMock()
    coupon.is_active = True
    coupon.usage_limit = 5
    coupon.usage_count = 5
    coupon.end_date = "2025-01-30T00:00:00Z"

    coupon_service.plan_coupons_dao.get_coupon_by_id = AsyncMock(return_value=coupon)

    with pytest.raises(CouponUsageLimitExceededError):
        await coupon_service.validate_and_apply_coupon("coupon_123", 200, "2025-01-28T00:00:00Z")


@pytest.mark.asyncio
async def test_create_discounted_plan_if_needed_with_discount(mock_connection_handler):
    plans_service = PlansService(mock_connection_handler)

    plans_service.razorpay_client.create_plan = AsyncMock(return_value={"id": "razorpay_plan_123"})

    new_discounted_plan = MagicMock()
    new_discounted_plan.id = "discounted_plan_123"
    plans_service.plans_dao.create_internal_plan = AsyncMock(return_value=new_discounted_plan)

    plans_service.plan_coupons_dao.update_coupon_plan_id = AsyncMock()

    plan = MagicMock()
    plan.id = "plan_123"
    plan.amount = "200"
    plan.currency = "INR"
    plan.billing_cycle = "monthly"
    plan.description = "Test Plan"

    coupon = MagicMock()
    coupon.code = "COUPON123"

    discounted_plan = await plans_service.create_discounted_plan_if_needed(plan, 50, "coupon_123", coupon)

    assert discounted_plan.id == "discounted_plan_123"
    plans_service.razorpay_client.create_plan.assert_called_once()
    plans_service.plans_dao.create_internal_plan.assert_called_once()
    plans_service.plan_coupons_dao.update_coupon_plan_id.assert_called_once_with(coupon,
                                                                                 new_plan_id="discounted_plan_123")


@pytest.mark.asyncio
async def test_create_discounted_plan_if_needed_without_discount(mock_connection_handler):
    plans_service = PlansService(mock_connection_handler)
    plan = MagicMock(amount="200", currency="INR", billing_cycle="monthly")

    discounted_plan = await plans_service.create_discounted_plan_if_needed(plan, 0, None, None)

    assert discounted_plan == plan