from fastapi import APIRouter, Depends
from app.routing import CustomRequestRoute
from rule_engine.views import (
    get_plan_specific_rules,
    add_rule_to_plan,
    create_rule,
    remove_rule_from_plan,
    get_rules_with_conditions
)
from utils.common import get_user_data_from_request

router = APIRouter(route_class=CustomRequestRoute, prefix="/rules", dependencies=[Depends(get_user_data_from_request)])


router.add_api_route(
    "/plans/{plan_id}",
    endpoint=get_plan_specific_rules,
    tags=["Plan Rules"],
    description="Get rules for the plan",
    methods=["GET"]
)

router.add_api_route(
    "/{rule_id}/plans/{plan_id}",
    endpoint=add_rule_to_plan,
    tags=["Plan Rules"],
    description="Add rule to a plan",
    methods=["POST"]
)

router.add_api_route(
    "/",
    endpoint=create_rule,
    tags=["Plan Rules"],
    description="Create rule for a plan",
    methods=["POST"]
)

router.add_api_route(
    "/{rule_id}/plans/{plan_id}",
    endpoint=remove_rule_from_plan,
    tags=["Plan Rules"],
    description="Remove rule from a plan",
    methods=["DELETE"]
)

router.add_api_route(
    "/{service_slug}/plans/{plan_id}",
    endpoint=get_rules_with_conditions,
    tags=["Plan Rules"],
    description="Get rules with conditions based on service and plan",
    methods=["GET"]
)
