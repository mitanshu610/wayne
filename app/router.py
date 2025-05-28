from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from config.settings import loaded_config

from payments.routes import router as payments_router
from plans.routes import router as plans_router
from features.routes import router as features_router
from statistics.router import statistics_router_v1
from webhooks.routes import router as webhook_router
from invoices.routes import router as invoices_router
from rule_engine.routes import router as rules_router
from prometheus.metrics import REGISTRY

from app.routing import CustomRequestRoute
from starlette.responses import Response


async def healthz():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True})


api_router = APIRouter()

""" all version v1.0 routes """
api_router_v1 = APIRouter(prefix='/v1.0', route_class=CustomRequestRoute)

if loaded_config.server_type == "public":
    api_router_v1.include_router(payments_router)
    api_router_v1.include_router(plans_router)
    api_router_v1.include_router(features_router)
    api_router_v1.include_router(invoices_router)
    api_router_v1.include_router(rules_router)
    api_router_v1.include_router(statistics_router_v1)
elif loaded_config.server_type == "webhook":
    api_router_v1.include_router(webhook_router)
else:
    """ all common routes """

""" health check routes """
api_router_healthz = APIRouter()
api_router_healthz.add_api_route("/_healthz", methods=['GET'], endpoint=healthz, include_in_schema=False)
api_router_healthz.add_api_route("/_readyz", methods=['GET'], endpoint=healthz, include_in_schema=False)

api_router.include_router(api_router_healthz)
api_router.include_router(api_router_v1)


