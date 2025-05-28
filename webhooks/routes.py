from fastapi import APIRouter
from app.routing import CustomRequestRoute
from webhooks.views import capture_razorpay_webhook, capture_paddle_webhook

router = APIRouter(route_class=CustomRequestRoute, prefix="/webhook")

router.add_api_route(
    "/razorpay/capture",
    endpoint=capture_razorpay_webhook,
    methods=["POST"],
    tags=["Webhooks"],
    description="Capture Razorpay webhook events"
)

router.add_api_route(
    "/paddle/capture",
    endpoint=capture_paddle_webhook,
    methods=["POST"],
    tags=["Webhooks"],
    description="Capture Razorpay webhook events"
)
