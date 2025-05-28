from clerk_integration.utils import UserData
from fastapi import Depends, Query

from invoices.exceptions import InvoiceError
from invoices.services import InvoicesService
from payments.models import ProviderName
from utils.common import get_user_data_from_request
from utils.common import handle_exceptions
from utils.connection_handler import get_connection_handler_for_app, ConnectionHandler
from utils.serializers import ResponseData


@handle_exceptions("Failed to retrieve invoices", exception_classes=[InvoiceError])
async def get_invoices(
        page: int = Query(1, ge=1, description="Page number (must be 1 or greater)"),
        page_size: int = Query(10, ge=1, description="Number of records per page (must be 1 or greater)"),
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
        user_data: UserData = Depends(get_user_data_from_request)
):
    """
    Retrieve all invoices for the user.
    """
    response_data = ResponseData.model_construct(success=True)
    invoices_service = InvoicesService(connection_handler=connection_handler)
    invoice_details = await invoices_service.get_invoices(user_data.userId, user_data.orgId, page, page_size)
    response_data.data = invoice_details
    return response_data


@handle_exceptions("Failed to retrieve invoice", exception_classes=[InvoiceError])
async def get_invoice(
        invoice_id: str,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
        user_data: UserData = Depends(get_user_data_from_request)
):
    """
    Retrieve invoice details for the user.
    """
    response_data = ResponseData.model_construct(success=True)
    invoices_service = InvoicesService(connection_handler=connection_handler)
    invoice_details = await invoices_service.get_invoice(invoice_id, user_data.userId, user_data.orgId)
    response_data.data = invoice_details
    return response_data


@handle_exceptions("Failed to get invoice pdf", exception_classes=[InvoiceError])
async def get_invoice_pdf(
        psp_name: ProviderName,
        psp_invoice_id: str,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app),
        user_data: UserData = Depends(get_user_data_from_request)
):
    """
    Retrieve invoice pdf from payment service provider.
    """
    response_data = ResponseData.model_construct(success=True)
    invoices_service = InvoicesService(connection_handler=connection_handler)
    invoice_details = await invoices_service.get_invoice_pdf(psp_invoice_id, psp_name)
    response_data.data = invoice_details
    return response_data
