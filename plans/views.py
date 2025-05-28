from typing import Optional

from fastapi import Depends, Query

from payments.models import ProviderName
from payments.schemas import PlanSlugs
from plans.exceptions import PlanError
from plans.schemas import PlanSchema, PlanUpdateSchema, PlanCouponSchema
from plans.services import PlansService, PlanCouponsService
from utils.common import handle_exceptions
from utils.connection_handler import get_connection_handler_for_app, ConnectionHandler
from utils.serializers import ResponseData


@handle_exceptions("Failed to fetch plans", [PlanError])
async def get_all_plans(
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
        plan_id: Optional[str] = Query(None, description="Plan ID to fetch specific plan"),
):
    response_data = ResponseData.construct(success=True)
    plans_service = PlansService(connection_handler=connection_handler)
    if plan_id:
        plans = await plans_service.get_plan_by_id(plan_id)
    else:
        plans = await plans_service.get_all_plans()
    response_data.data = plans
    return response_data


@handle_exceptions("Failed to create plan", [PlanError])
async def create_plan(
        psp_name: ProviderName,
        plan_details: PlanSchema,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    plan_slugs = [plan_slug.value for plan_slug in PlanSlugs]
    if plan_details.slug not in plan_slugs:
        response_data.success = False
        response_data.errors = [f"Plan must be from {plan_slugs}"]
        return response_data

    plans_service = PlansService(connection_handler=connection_handler)
    new_plan = await plans_service.create_plan(plan_details, psp_name)
    response_data.data = new_plan.to_dict()
    return response_data


@handle_exceptions("Failed to update plan", [PlanError])
async def update_plan(
        plan_id: str,
        plan_details: PlanUpdateSchema,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    plans_service = PlansService(connection_handler=connection_handler)
    updated_plan = await plans_service.update_plan(plan_id, plan_details)
    response_data.data = updated_plan
    return response_data


@handle_exceptions("Failed to delete plan", [PlanError])
async def delete_plan(
        plan_id: str,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    plans_service = PlansService(connection_handler=connection_handler)
    await plans_service.delete_plan(plan_id)
    response_data.message = "Plan deleted successfully"
    return response_data


@handle_exceptions("Failed to create coupon", [PlanError])
async def create_plan_coupon(
        coupon_details: PlanCouponSchema,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    plan_coupons_service = PlanCouponsService(connection_handler=connection_handler)
    new_coupon = await plan_coupons_service.create_plan_coupon(coupon_details)
    response_data.data = new_coupon
    return response_data


@handle_exceptions("Failed to fetch coupons for plan", [PlanError])
async def get_coupons_by_plan(
        plan_id: str,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    plan_coupons_service = PlanCouponsService(connection_handler=connection_handler)
    coupons = await plan_coupons_service.get_coupons_by_plan(plan_id)
    response_data.data = coupons
    return response_data


@handle_exceptions("Failed to deactivate coupon", [PlanError])
async def deactivate_coupon(
        coupon_id: str,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    plan_coupons_service = PlanCouponsService(connection_handler=connection_handler)
    updated_coupon = await plan_coupons_service.deactivate_coupon(coupon_id)
    response_data.data = updated_coupon
    response_data.message = f"Coupon {coupon_id} deactivated successfully."
    return response_data


@handle_exceptions("Failed to fetch all coupons", [PlanError])
async def get_all_coupons(
        coupon_id: str,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    response_data = ResponseData.construct(success=True)
    plan_coupons_service = PlanCouponsService(connection_handler=connection_handler)
    updated_coupon = await plan_coupons_service.get_all_coupons()
    response_data.data = updated_coupon
    response_data.message = f"Coupon {coupon_id} deactivated successfully."
    return response_data
