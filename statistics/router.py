from fastapi import APIRouter

from app.routing import CustomRequestRoute
from statistics.views import get_service_usage_stats

statistics_router_v1 = APIRouter(route_class=CustomRequestRoute, prefix='/statistics')

statistics_router_v1.add_api_route('/usage', methods=['GET'], endpoint=get_service_usage_stats)
