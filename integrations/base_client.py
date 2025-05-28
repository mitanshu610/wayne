import asyncio
from enum import Enum

import httpx

from config.logging import logger


class AuthMethod(str, Enum):
    BASIC = "Basic"
    BEARER = "Bearer"


class BaseAPIClient:
    """
    Base class for API clients to handle common operations.
    """

    def __init__(self, base_url: str, api_secret: str, auth_method: AuthMethod = AuthMethod.BASIC):
        self.base_url = base_url
        self.api_secret = api_secret
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"{auth_method} {self.api_secret}"
        }

    async def _make_request(self, method: str, endpoint: str, json: dict = None, retries: int = 3,
                            backoff_factor: float = 1.5):
        """
        Makes an HTTP request with retry logic.

        :param method: HTTP method (e.g., GET, POST).
        :param endpoint: API endpoint.
        :param json: JSON payload for the request.
        :param retries: Number of retry attempts.
        :param backoff_factor: Time in seconds to wait between retries.
        """
        url = f"{self.base_url}{endpoint}"
        attempt = 0

        while attempt < retries:
            attempt += 1
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(method, url, headers=self.headers, json=json)

                if response.status_code in (200, 201, 202):
                    if attempt > 1:
                        logger.info(
                            "API call succeeded on retry %d: %s %s",
                            attempt, method, url
                        )
                    else:
                        logger.debug(
                            "API call succeeded: %s %s",
                            method, url
                        )
                    return response.json()

                logger.error(
                    "API call failed: %s %s [Status Code: %d] Response: %s",
                    method, url, response.status_code, response.text
                )
                raise ValueError(f"API call failed: {response.text}")

            except httpx.RequestError as exc:
                if attempt < retries:
                    wait_time = backoff_factor * (2 ** (attempt - 1))
                    logger.warning(
                        "Request error during API call: %s %s. Attempt %d/%d. Retrying in %.2f seconds. Error: %s",
                        method, url, attempt, retries, wait_time, str(exc)
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        "Exhausted all retries for API call: %s %s. Error: %s",
                        method, url, str(exc)
                    )
                    raise exc
