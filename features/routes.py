from fastapi import APIRouter
from app.routing import CustomRequestRoute
from features.views import (
    create_feature, update_feature, delete_feature, get_all_features, get_features_for_plan,
    add_feature_to_plan, remove_feature_from_plan, get_features_by_service
)


router = APIRouter(route_class=CustomRequestRoute)

router.add_api_route(
    "/features",
    endpoint=get_all_features,
    tags=["Features"],
    description="Get all the features",
    methods=["GET"]
)

router.add_api_route(
    "/features",
    endpoint=create_feature,
    tags=["Features"],
    description="Create a new feature",
    methods=["POST"]
)

router.add_api_route(
    "/features/{feature_id}",
    endpoint=update_feature,
    tags=["Features"],
    description="Update existing feature",
    methods=["PUT"]
)

router.add_api_route(
    "/features/{feature_id}",
    endpoint=delete_feature,
    tags=["Features"],
    description="Remove existing feature",
    methods=["DELETE"]
)

router.add_api_route(
    "/plans/{plan_id}/features",
    endpoint=get_features_for_plan,
    tags=["Plan - Features"],
    description="Get features for a plan",
    methods=["GET"]
)

router.add_api_route(
    "/plans/{plan_id}/features/{feature_id}",
    endpoint=add_feature_to_plan,
    tags=["Plan - Features"],
    description="Add a feature to a specific plan",
    methods=["POST"]
)

router.add_api_route(
    "/plans/{plan_id}/features/{feature_id}",
    endpoint=remove_feature_from_plan,
    tags=["Plan - Features"],
    description="Remove feature from a specific plan",
    methods=["DELETE"]
)

router.add_api_route(
    "/features/service/{service_name}",
    endpoint=get_features_by_service,
    tags=["Plan - Features"],
    description="Get all features by service",
    methods=["GET"]
)