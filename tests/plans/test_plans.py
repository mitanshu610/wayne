from unittest.mock import AsyncMock
import pytest

from payments.models import ProviderName
from plans.schemas import PlanSchema, PlanUpdateSchema
from plans.services import PlansService


@pytest.mark.asyncio
async def test_get_all_plans(mock_connection_handler):
    plans_service = PlansService(mock_connection_handler)
    plans_service.plans_dao.get_all_plans = AsyncMock(return_value=["plan1", "plan2"])

    plans = await plans_service.get_all_plans()

    assert plans == ["plan1", "plan2"]
    plans_service.plans_dao.get_all_plans.assert_called_once()


@pytest.mark.asyncio
async def test_get_plan_by_id(mock_connection_handler):
    plans_service = PlansService(mock_connection_handler)
    plans_service.plans_dao.get_plan_by_id = AsyncMock(return_value={"id": "plan_123"})

    plan = await plans_service.get_plan_by_id("plan_123")

    assert plan["id"] == "plan_123"
    plans_service.plans_dao.get_plan_by_id.assert_called_once_with("plan_123")


@pytest.mark.asyncio
async def test_create_plan_with_amount(mock_connection_handler):
    plans_service = PlansService(mock_connection_handler)
    plan_details = PlanSchema(name="Test Plan", amount="100", currency="INR", billing_cycle="monthly")
    plans_service.razorpay_client.create_plan = AsyncMock(return_value={"id": "razorpay_plan_123"})
    plans_service.plans_dao.create_plan = AsyncMock(return_value={"id": "plan_123"})

    plan = await plans_service.create_plan(plan_details, ProviderName.RAZORPAY)

    assert plan["id"] == "plan_123"
    plans_service.razorpay_client.create_plan.assert_called_once_with(plan_details)
    plans_service.plans_dao.create_plan.assert_called_once()


@pytest.mark.asyncio
async def test_create_plan_with_zero_amount(mock_connection_handler):
    plans_service = PlansService(mock_connection_handler)
    plan_details = PlanSchema(name="Free Plan", amount="0", currency="INR", billing_cycle="monthly")
    plans_service.plans_dao.create_plan = AsyncMock(return_value={"id": "plan_123"})

    plan = await plans_service.create_plan(plan_details, ProviderName.RAZORPAY)

    assert plan["id"] == "plan_123"
    plans_service.plans_dao.create_plan.assert_called_once_with(plan_details, None)


@pytest.mark.asyncio
async def test_update_plan(mock_connection_handler):
    plans_service = PlansService(mock_connection_handler)
    plan_details = PlanUpdateSchema(name="Updated Plan")
    plans_service.plans_dao.update_plan = AsyncMock(return_value={"id": "plan_123"})

    updated_plan = await plans_service.update_plan("plan_123", plan_details)

    assert updated_plan["id"] == "plan_123"
    plans_service.plans_dao.update_plan.assert_called_once_with("plan_123", plan_details)
