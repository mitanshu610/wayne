from fastapi import APIRouter
from fastapi.params import Depends

from app.routing import CustomRequestRoute
from plans.views import (create_plan, update_plan, delete_plan, get_all_plans,
                         create_plan_coupon, deactivate_coupon,
                         get_coupons_by_plan, get_all_coupons)
from utils.common import get_user_data_from_request

router = APIRouter(route_class=CustomRequestRoute, dependencies=[Depends(get_user_data_from_request)])

router.add_api_route(
    "/plans",
    endpoint=get_all_plans,
    tags=["Plans & Subscriptions"],
    description="Get the available plan/s. Pass 'plan_id' as a query parameter to fetch a specific plan.",
    methods=["GET"]
)

router.add_api_route(
    "/{psp_name}/plans",
    endpoint=create_plan,
    tags=["Plans & Subscriptions"],
    description="Create a new plan",
    methods=["POST"]
)

router.add_api_route(
    "/plans/{plan_id}",
    endpoint=update_plan,
    tags=["Plans & Subscriptions"],
    description="Update existing plan",
    methods=["PUT"]
)

router.add_api_route(
    "/plans/{plan_id}",
    endpoint=delete_plan,
    tags=["Plans & Subscriptions"],
    description="Remove existing plan",
    methods=["DELETE"]
)

router.add_api_route(
    "/coupons",
    endpoint=create_plan_coupon,
    tags=["Plan Coupons"],
    description="Create a Coupon for plan",
    methods=["POST"]
)

router.add_api_route(
    "/plans/{plan_id}/coupons",
    endpoint=get_coupons_by_plan,
    tags=["Plan Coupons"],
    description="Get coupons for a specific plan",
    methods=["GET"]
)

router.add_api_route(
    "/coupons/{coupon_id}/deactivate",
    endpoint=deactivate_coupon,
    tags=["Plan Coupons"],
    description="Deactivate a coupon",
    methods=["PUT"]
)

router.add_api_route(
    "/coupons",
    endpoint=get_all_coupons,
    tags=["Plan Coupons"],
    description="Get all coupons",
    methods=["GET"]
)

