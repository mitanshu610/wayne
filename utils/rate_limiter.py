from fastapi import Request
from slowapi import Limiter

from config.settings import loaded_config
from utils.common import UserData


def get_rate_limiter_key(request: Request):
    user_data: UserData = request.state.user_data
    return f"rate_limit:{user_data.userId}:{user_data.orgId}"


class RateLimiter:
    def __init__(self):
        """
        Initialize the rate limiter using Redis.
        """
        self.limiter = Limiter(
            key_func=get_rate_limiter_key,
            storage_uri=loaded_config.redis_payments_url,
        )
        self.default_limit = "15/minute"

    def limit(self, limit: str = None):
        """
        Decorator to apply rate limiting to an endpoint.

        :param limit: Custom rate limit (e.g., "10/minute"), defaults to class-level setting
        """
        return self.limiter.limit(limit or self.default_limit)


user_rate_limiter = RateLimiter()
