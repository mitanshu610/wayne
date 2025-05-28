from fastapi import APIRouter
from fastapi.params import Depends

from app.routing import CustomRequestRoute
from payments.views import (
    get_subscriptions, get_payment_downtimes, upgrade_subscription, create_subscription, cancel_subscription
)
from utils.common import get_user_data_from_request

router = APIRouter(route_class=CustomRequestRoute, prefix="/payments")

router.add_api_route(
    "/{psp_name}/subscribe",
    endpoint=create_subscription,
    tags=["Payments"],
    description="Initialize payment gateway",
    methods=["POST"]
)

router.add_api_route(
    "/unsubscribe",
    endpoint=cancel_subscription,
    tags=["Payments"],
    description="Unsubscribe",
    methods=["POST"]
)

router.add_api_route(
    "/subscriptions",
    endpoint=get_subscriptions,
    tags=["Payment"],
    description="Get user org specific subscription",
    methods=["GET"]
)

router.add_api_route(
    "/downtime",
    endpoint=get_payment_downtimes,
    tags=["Payment"],
    description="Get downtime of payments",
    methods=["GET"],
    dependencies=[Depends(get_user_data_from_request)]
)

router.add_api_route(
    "/subscriptions/upgrade",
    endpoint=upgrade_subscription,
    tags=["Payment"],
    description="Get downtime of payments",
    methods=["POST"]
)
