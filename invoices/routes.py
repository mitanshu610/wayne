from fastapi import APIRouter
from app.routing import CustomRequestRoute
from invoices.views import get_invoices, get_invoice, get_invoice_pdf

router = APIRouter(route_class=CustomRequestRoute, prefix="/invoices")

router.add_api_route(
    "/",
    endpoint=get_invoices,
    tags=["Invoices"],
    description="Get User Org Paginated Invoices",
    methods=["GET"]
)

router.add_api_route(
    "/{invoice_id}",
    endpoint=get_invoice,
    tags=["Invoices"],
    description="get pdf url of invoice",
    methods=["GET"]
)

router.add_api_route(
    "/psp/{psp_name}/{psp_invoice_id}/pdf",
    endpoint=get_invoice_pdf,
    tags=["Invoices"],
    description="get pdf url of invoice",
    methods=["GET"]
)

