from fastapi import APIRouter
from app.routing import CustomRequestRoute
from refunds.views import (get_refund_details, initiate_refund,
                           get_all_refunds_org, get_all_refund_requests,
                           create_refund_request, update_refund_request)

router = APIRouter(route_class=CustomRequestRoute, prefix="/refunds")

router.add_api_route(
    "/details/{refund_id}",
    endpoint=get_refund_details,
    tags=["Refunds"],
    description="Get details of a refund",
    methods=["GET"]
)

router.add_api_route(
    "/initiate",
    endpoint=initiate_refund,
    tags=["Refunds"],
    description="Initiate a refund",
    methods=["POST"]
)

router.add_api_route(
    "/org",
    endpoint=get_all_refunds_org,
    tags=["Refunds"],
    description="Get all refunds of org",
    methods=["GET"]
)

router.add_api_route(
    "/requests/raise",
    endpoint=create_refund_request,
    tags=["Request Refund"],
    description="Raise refund request",
    methods=["POST"]
)


router.add_api_route(
    "/requests",
    endpoint=get_all_refund_requests,
    tags=["Request Refund"],
    description="Get all refund requests",
    methods=["GET"]
)


router.add_api_route(
    "/requests/update",
    endpoint=update_refund_request,
    tags=["Request Refund"],
    description="Update a refund request by ID",
    methods=["PUT"]
)