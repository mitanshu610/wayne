from statistics.services import StatisticsService
from utils.common import get_user_data_from_request, handle_exceptions
from fastapi import Depends
from clerk_integration.utils import UserData

from utils.connection_handler import get_connection_handler_for_app


@handle_exceptions("Failed to create subscription for the selected plan.")
async def get_service_usage_stats(
        user_data: UserData = Depends(get_user_data_from_request),
        connection_handler = Depends(get_connection_handler_for_app)
):
    statistics_service = StatisticsService(connection_handler)
    return await statistics_service.get_service_usage_stats(user_data=user_data)
