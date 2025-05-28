from typing import Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute

from config.logging import logger
from utils.common import get_user_data_from_request


class CustomRequestRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                # as we need user details to apply ratelimit on api calls: Refer RateLimiter class
                if user_data := await get_user_data_from_request(request):
                    request.state.user_data = user_data
            except Exception as e:
                logger.info(f"get_user_data_from_request in custom_route_handler failed with error: {e}")
            return await original_route_handler(request)

        return custom_route_handler


def sanitize_label(value):
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if not isinstance(value, str):
        value = str(value)
    return value.encode("utf-8", errors="replace").decode("utf-8", errors="replace")


def log_api_requests_to_gcp(request_data, response_data, consumed_time):
    api_logs = {
        "status": response_data['status_code'],
        'consumed_time': consumed_time or 0,
        'request': request_data,
        'response': response_data
    }
    if response_data['status_code'] == 200:
        logger.info(api_logs)
    else:
        logger.error(api_logs)
