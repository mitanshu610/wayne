from fastapi import Depends, status, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from integrations.razorpay_client import RazorpayClient
from config.settings import loaded_config
from payments.exceptions import PaymentError
from payments.models import ProviderName
from payments.schemas import CreateSubscription
from payments.services import PaymentsService
from plans.exceptions import PlanError
from utils.common import get_user_data_from_request, UserData
from utils.common import handle_exceptions
from utils.connection_handler import get_connection_handler_for_app, ConnectionHandler
from utils.rate_limiter import user_rate_limiter
from utils.serializers import ResponseData
# from clerk_integration.utils import UserDataHanlder


@user_rate_limiter.limit()
@handle_exceptions("Failed to create subscription for the selected plan.", exception_classes=[PaymentError, PlanError])
async def create_subscription(
        request: Request,
        psp_name: ProviderName,
        order_details: CreateSubscription,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
        user_data: UserData = Depends(get_user_data_from_request)
):
    """
    Create a Razorpay subscription.

    Only users with the role 'org-owner' and email ending with 'gofynd.com' are allowed.
    """
    # Validate user permissions and email domain.
    if user_data.orgId and user_data.roleSlug != "org:admin":
        response_data = ResponseData.model_construct(success=False)
        response_data.message = "Permission denied"
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=jsonable_encoder(response_data)
        )
    if not user_data.email.endswith("gofynd.com"):
        response_data = ResponseData.model_construct(success=False)
        response_data.message = "Currently allowed for fynd users"
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder(response_data)
        )

    # Process the subscription creation.
    payments_service = PaymentsService(connection_handler=connection_handler)
    order_details = await payments_service.create_subscription(order_details, user_data, psp_name)
    response_data = ResponseData.model_construct(success=True, data=order_details)
    return response_data


@handle_exceptions("Failed to fetch subscription details.", exception_classes=[PaymentError, PlanError])
async def get_subscription_by_id(
        subscription_id: str,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app)
):
    """
    Retrieve subscription details by subscription ID.
    """
    payments_service = PaymentsService(connection_handler=connection_handler)
    order_details = await payments_service.get_subscription_by_id(subscription_id)
    response_data = ResponseData.model_construct(success=True, data=order_details)
    return response_data


@handle_exceptions("Failed to unsubscribe from razorpay subscription.", exception_classes=[PaymentError, PlanError])
async def cancel_subscription(
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
        user_data: UserData = Depends(get_user_data_from_request)
):
    """
    Unsubscribe the current user from their Razorpay subscription.
    """
    payments_service = PaymentsService(connection_handler=connection_handler)
    is_free = await payments_service.unsubscribe(user_data.userId, user_data.orgId)
    response_data = ResponseData.model_construct(success=True, data=[])
    response_data.message = (
        "Your subscription has been cancelled"
        if is_free
        else "Your subscription will be cancelled at the end of the current cycle"
    )
    return response_data


@handle_exceptions("Failed to fetch subscriptions for current user.", exception_classes=[PaymentError, PlanError])
async def get_subscriptions(
        request: Request,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
        user_data: UserData = Depends(get_user_data_from_request)
):
    """
    Retrieve all subscriptions for the current user.
    """
    payments_service = PaymentsService(connection_handler=connection_handler)
    subscription_details = await payments_service.get_subscriptions_by_user_org(
        user_data.userId, user_data.orgId, user_data.firstName, user_data.lastName
    )
    response_data = ResponseData.construct(success=True, data=subscription_details)
    return response_data


@handle_exceptions("Failed to fetch payment downtimes.", exception_classes=[PaymentError, PlanError])
async def get_payment_downtimes():
    """
    Retrieve payment downtime information.
    """
    razorpay_client = RazorpayClient()
    payment_downtimes = await razorpay_client.get_payment_downtimes()
    response_data = ResponseData.model_construct(success=True, data=payment_downtimes)
    return response_data


@handle_exceptions("Failed to upgrade subscription.", exception_classes=[PaymentError, PlanError])
async def upgrade_subscription(
        upgrade_to_plan: CreateSubscription,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
        user_data: UserData = Depends(get_user_data_from_request)
):
    """
    Upgrade the user's subscription plan.
    """
    payment_service = PaymentsService(connection_handler=connection_handler)
    await payment_service.upgrade_subscription(upgrade_to_plan, user_data)
    response_data = ResponseData.model_construct(success=True, data=[])
    response_data.message = "Plan upgraded successfully."
    return response_data
