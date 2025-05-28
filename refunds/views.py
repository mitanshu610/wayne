from fastapi import Depends, Query, Path
from refunds.schemas import RefundSchema, RequestRefundSchema, UpdateRefundRequestSchema
from refunds.services import RefundsService
from utils.common import UserData, get_user_data_from_request
from utils.connection_handler import get_connection_handler_for_app, ConnectionHandler
from utils.serializers import ResponseData


async def get_refund_details(
    refund_id: str,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    """
    Get details of a specific refund by ID.
    """
    response_data = ResponseData.construct(success=True)
    try:
        refunds_service = RefundsService(connection_handler=connection_handler)
        refund_details = await refunds_service.get_refund_by_id(refund_id)
        response_data.data = refund_details
        return response_data
    except Exception as e:
        response_data.success = False
        response_data.message = f"Failed to fetch details for refund ID {refund_id}"
        response_data.errors = [str(e)]
        return response_data


async def initiate_refund(
    refund_details: RefundSchema,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    """
    Initiate a refund for a specific transaction.
    """
    response_data = ResponseData.construct(success=True)
    try:
        refunds_service = RefundsService(connection_handler=connection_handler)
        new_refund = await refunds_service.initiate_refund(refund_details)
        response_data.data = new_refund
        response_data.message = "Refund initiated successfully."
        return response_data
    except Exception as e:
        response_data.success = False
        response_data.message = "Failed to initiate refund"
        response_data.errors = [str(e)]
        return response_data


async def get_all_refunds_org(
    user_data: UserData = Depends(get_user_data_from_request),
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    """
    Get a list of all refunds.
    """
    response_data = ResponseData.construct(success=True)
    try:
        refunds_service = RefundsService(connection_handler=connection_handler)
        refunds = await refunds_service.get_all_refunds_by_entity(user_data.orgId)
        response_data.data = refunds
        return response_data
    except Exception as e:
        response_data.success = False
        response_data.message = "Failed to fetch refunds"
        response_data.errors = [str(e)]
        return response_data

async def create_refund_request(
    request_refund_details: RequestRefundSchema,
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
):
    """
    Request a refund
    """
    response_data = ResponseData.construct(success=True)
    try:
        refunds_service = RefundsService(connection_handler=connection_handler)
        refunds = await refunds_service.request_refund(request_refund_details)
        response_data.data = refunds
        return response_data
    except Exception as e:
        response_data.success = False
        response_data.message = "Failed to fetch refunds"
        response_data.errors = [str(e)]
        return response_data

async def get_all_refund_requests(
    connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
    page: int = Query(1, ge=1, description="Page number (must be 1 or greater)"),
    page_size: int = Query(10, ge=1, description="Number of records per page (must be 1 or greater)"),
):
    """
    Get all refund requests with pagination.
    """
    response_data = ResponseData.construct(success=True)
    try:
        refunds_service = RefundsService(connection_handler=connection_handler)
        refunds = await refunds_service.get_all_refund_requests(page, page_size)
        response_data.data = refunds
        return response_data
    except Exception as e:
        response_data.success = False
        response_data.message = "Failed to fetch refunds"
        response_data.errors = [str(e)]
        return response_data


async def update_refund_request(
    request_data: UpdateRefundRequestSchema,
    connection_handler=Depends(get_connection_handler_for_app),
):
    """
    Update a refund request by ID.
    """
    response_data = ResponseData.construct(success=True)
    try:
        refunds_service = RefundsService(connection_handler=connection_handler)
        updated_request = await refunds_service.update_refund_request(request_data)
        response_data.data = updated_request
        return response_data
    except Exception as e:
        response_data.success = False
        response_data.message = "Failed to update refund request"
        response_data.errors = [str(e)]
        return response_data