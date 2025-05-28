from fastapi.params import Depends
from fastapi import HTTPException, Request

from paygo.schemas import CreatePaygoOrderSchema
from paygo.services import PaygoService
from utils.common import get_user_data_from_request, UserData
from utils.connection_handler import get_connection_handler_for_app, ConnectionHandler
from utils.serializers import ResponseData


async def create_paygo_order(
        order_details: CreatePaygoOrderSchema,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
        user_data: UserData = Depends(get_user_data_from_request)
):
    response_data = ResponseData.construct(success=True)
    try:
        paygo_service = PaygoService(connection_handler=connection_handler)
        await paygo_service.create_paygo_order(order_details, user_data)
        response_data.data = []
        return response_data
    except Exception as e:
        response_data.success = False
        response_data.errors = [str(e)]
        return response_data