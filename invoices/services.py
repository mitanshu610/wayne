from integrations.paddle_client import PaddleClient
from integrations.razorpay_client import RazorpayClient
from invoices.dao import InvoicesDAO
from invoices.schemas import CreateInvoiceSchema
from payments.dao import PaymentsDAO
from payments.models import ProviderName
from plans.dao import PlansDAO
from utils.connection_handler import ConnectionHandler
from utils.sqlalchemy import get_current_time


class InvoicesService:
    def __init__(self, connection_handler: ConnectionHandler):
        self.connection_handler = connection_handler
        self.invoices_dao = InvoicesDAO(session=self.connection_handler.session)
        self.payments_dao = PaymentsDAO(session=self.connection_handler.session)
        self.plans_dao = PlansDAO(session=self.connection_handler.session)
        self.razorpay_client = RazorpayClient()
        self.paddle_client = PaddleClient()

    async def create_draft_invoice(self, draft_details: CreateInvoiceSchema, user_id: int, org_id: int):
        """
        Create a draft invoice in the database.

        :param draft_details: CreateInvoiceSchema containing invoice details.
        :param user_id: user id in db.
        :param org_id: org id in db.
        :return: The created draft invoice object.
        :raises InvoiceError: If invoice creation fails.
        """
        customer = await self.payments_dao.get_customer_by_user_and_org_id(user_id, org_id)
        subscription_details = await self.payments_dao.get_subscription_by_id(str(draft_details.subscription_id))
        plan_details = await self.plans_dao.get_plan_by_id(subscription_details.plan_id)
        await self.razorpay_client.draft_invoice(customer.customer_id,
                                                 plan_details.name,
                                                 float(plan_details.amount),
                                                 plan_details.currency, plan_details.description)
        invoice_data = {
            "subscription_id": draft_details.subscription_id,
            "invoice_date": get_current_time(),
            "amount": plan_details.amount,
            "currency": plan_details.currency,
            "status": "draft"
        }

        draft_invoice = await self.invoices_dao.create_invoice(**invoice_data)
        return draft_invoice

    async def get_invoices(self, user_id: str, org_id: str, page, page_size):
        """
        Get all invoices for a user

        :param user_id: user id in db.
        :param org_id: org id in db.
        :param page: page number.
        :param page_size: number of records in a page.
        :return: Invoices of the user.
        :raises InvoiceError: If invoice creation fails.
        """
        return await self.invoices_dao.get_user_invoices_paginated(user_id, org_id, page, page_size)

    async def get_invoice(self, invoice_id: str, user_id: str, org_id: str):
        """
        Get all invoice details for a user

        :param user_id: user id in db.
        :param org_id: org id in db.
        :param invoice_id: invoice id in db.
        :return: Invoice details of the user.
        :raises InvoiceError: If invoice details fails.
        """
        return await self.invoices_dao.get_user_invoice(invoice_id, user_id, org_id)

    async def get_invoice_pdf(self, psp_invoice_id: str, psp_name: ProviderName):
        if psp_name == ProviderName.PADDLE:
            invoice = await self.paddle_client.get_transaction_invoice(transaction_id=psp_invoice_id)
            invoice_pdf_url = invoice.get("data").get("url") if invoice and invoice.get("data") else ""
            return {"invoice_pdf_url": invoice_pdf_url}
        elif psp_name == ProviderName.RAZORPAY:
            pass
