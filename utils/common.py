import typing
import functools

import sentry_sdk
from fastapi import HTTPException
from pydantic import Field, BaseModel
from starlette.requests import Request

from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from fastapi import status

from config.settings import loaded_config
from utils.exceptions import SessionExpiredException
from utils.serializers import ResponseData
from clerk_integration.utils import UserData

from config.logging import logger, get_call_stack


class LogData(BaseModel):
    error_type: str = Field(..., description="Type of the exception encountered")
    message: str = Field(..., description="Error message")
    detail: typing.Optional[str] = Field(None, description="Additional details about the error")
    function: str = Field(..., description="Function where the error occurred")


async def get_user_data_from_request(request: Request):
    try:
        user_data: UserData = await loaded_config.clerk_auth_helper.get_user_data_from_clerk(request)
        return user_data
    except Exception as e:
        try:
            user_data: UserData = request.state.user_data
            return user_data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": SessionExpiredException.DEFAULT_MESSAGE,
                    "message": SessionExpiredException.DEFAULT_MESSAGE,
                    "code": SessionExpiredException.ERROR_CODE
                }
            ) from e


def handle_exceptions(
    generic_message: str = "An unexpected error occurred",
    exception_classes: typing.Union[typing.List[typing.Type[Exception]], tuple] = None
):
    """
    Decorator for structured logging + Sentry + error response formatting.

    - Logs all exceptions
    - Sends unhandled errors to Sentry
    - Lets FastAPI handle HTTPException but logs it
    """
    exception_classes = tuple(exception_classes or ())

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)

            except HTTPException as http_exc:
                logger.exception(
                    "HTTPException raised",
                    error_type=http_exc.__class__.__name__,
                    message=http_exc.detail,
                    status_code=http_exc.status_code,
                    function=func.__name__
                )
                raise
            except exception_classes as e:
                try:
                    log_data = LogData(
                        error_type=e.__class__.__name__,
                        message=getattr(e, "message", str(e)),
                        detail=getattr(e, "detail", str(e)),
                        function=func.__name__
                    )
                    logger.exception("Handled exception", log=log_data.model_dump())
                except Exception as log_err:
                    logger.error("Error during structured log creation", error=str(log_err))

                response_data = ResponseData.model_construct(success=False)
                response_data.message = getattr(e, "message", str(e))
                response_data.errors = [getattr(e, "detail", str(e))]

                return JSONResponse(
                    status_code=getattr(e, "status_code", status.HTTP_400_BAD_REQUEST),
                    content=jsonable_encoder(response_data)
                )

            # Unhandled/Unexpected exception — log and send to Sentry
            except Exception as e:
                sentry_sdk.capture_exception(e)

                logger.exception(
                    "Unhandled exception occurred",
                    error_type=type(e).__name__,
                    message=str(e),
                    function=func.__name__
                )

                response_data = ResponseData.model_construct(success=False)
                response_data.message = generic_message
                response_data.errors = [str(e)]

                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content=jsonable_encoder(response_data)
                )

        return wrapper

    return decorator