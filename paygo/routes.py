from fastapi import APIRouter
from app.routing import CustomRequestRoute
from paygo.views import create_paygo_order


router = APIRouter(route_class=CustomRequestRoute, prefix="/paygo")

router.add_api_route(
    "/orders",
    endpoint=create_paygo_order,
    tags=["PAYGO"],
    description="Create a PAYGO order",
    methods=["POST"]
)