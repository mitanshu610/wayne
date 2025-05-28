import time
from typing import Optional

import uuid6
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from config.logging import logger
from invoices.exceptions import (
    InvoiceNotFoundError, InvoiceError, DuplicateInvoiceError, InvalidInvoiceDetailsError
)
from invoices.models import Invoice
from prometheus.metrics import DB_QUERY_LATENCY
from utils.decorators import latency


class InvoicesDAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    @latency(metric=DB_QUERY_LATENCY)
    async def create_invoice(self, subscription_id, invoice_id, amount, currency, status, next_due, user_id, org_id,
                             short_url, transaction_id, psp_name: str):
        """
        Create a new invoice record in the database.

        :param subscription_id: The associated subscription ID.
        :param invoice_id: The unique ID for the invoice.
        :param amount: The amount for the invoice.
        :param currency: The currency of the invoice.
        :param status: The status of the invoice (e.g., paid, partially_paid).
        :param next_due: Next due date for invoice.
        :return: The created Invoice object.
        :raises DuplicateInvoiceError: If an invoice with the same ID already exists.
        :raises InvalidInvoiceDetailsError: If the invoice cannot be created.
        """
        new_invoice_id = uuid6.uuid6()
        try:
            new_invoice = Invoice(
                id=new_invoice_id,
                psp_invoice_id=invoice_id,
                subscription_id=subscription_id,
                invoice_date=int(time.time()),
                amount=str(amount),
                currency=currency,
                status=status,
                next_due_date=next_due,
                user_id=user_id,
                org_id=org_id,
                short_url=short_url,
                transaction_id=transaction_id,
                psp_name=psp_name
            )
            self.session.add(new_invoice)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(new_invoice)
            logger.info("Invoice created successfully for subscription ID: %s", str(subscription_id))
            return new_invoice
        except IntegrityError as e:
            logger.error("Integrity error while adding invoice: %s", str(e))
            raise DuplicateInvoiceError(invoice_id)
        except Exception as e:
            logger.error("Error creating invoice for subscription ID %s: %s", str(subscription_id), str(e))
            raise InvalidInvoiceDetailsError(detail="Failed to create invoice with the provided details.")

    @latency(metric=DB_QUERY_LATENCY)
    async def get_invoice_by_psp_id(self, invoice_id: str):
        """
        Fetch an invoice from the database using its ID.
        """
        try:
            result = await self.session.execute(
                select(Invoice).filter(Invoice.psp_invoice_id == invoice_id)
            )
            invoice = result.scalars().first()
            if not invoice:
                raise InvoiceNotFoundError(invoice_id)
            return invoice
        except InvoiceNotFoundError as e:
            logger.error("Invoice not found: %s", str(e))
            raise
        except Exception as e:
            logger.error("Error fetching invoice by ID %s: %s", str(invoice_id), str(e))
            raise InvoiceError(detail=f"Database error while fetching invoice by ID {invoice_id}")

    @latency(metric=DB_QUERY_LATENCY)
    async def get_latest_invoice_by_subscription_id(self, subscription_id: str):
        """
        Fetch the latest invoice for a specific subscription.

        :param subscription_id: The subscription ID.
        :return: The latest Invoice object or None if not found.
        """
        try:
            result = await self.session.execute(
                select(Invoice)
                .filter(Invoice.subscription_id == subscription_id)
                .order_by(Invoice.invoice_date.desc())
                .limit(1)
            )
            return result.scalars().first()
        except Exception as e:
            logger.error("Error fetching latest invoice for subscription ID %s: %s", str(subscription_id), str(e))
            raise e

    @latency(metric=DB_QUERY_LATENCY)
    async def update_invoice_status(self, invoice_id: str, status: str, next_due_date: Optional[int]):
        """
        Update the status of an invoice.

        :param invoice_id: The ID of the invoice to update.
        :param status: The new status for the invoice.
        :param next_due_date: The next due date for the invoice.
        :return: The updated Invoice object.
        """
        try:
            invoice = await self.get_invoice_by_psp_id(invoice_id)
            invoice.status = status
            invoice.next_due_date = next_due_date
            self.session.add(invoice)
            await self.session.commit()
            logger.info("Invoice status updated successfully for ID: %s", str(invoice_id))
            return invoice
        except Exception as e:
            logger.error("Error updating invoice status for ID %s: %s", str(invoice_id), str(e))
            raise e

    @latency(metric=DB_QUERY_LATENCY)
    async def get_user_invoices_paginated(self, user_id: str, org_id: str, page: int = 1, page_size: int = 10) -> dict:
        """
        Fetch invoices for a user with pagination.

        :param user_id: The user ID to fetch invoices for.
        :param org_id: The org ID to fetch invoices for.
        :param page: The page number (1-based index).
        :param page_size: The number of invoices per page.
        :return: A dictionary containing the invoices and pagination details.
        """
        try:
            offset = (page - 1) * page_size
            total_invoices_query = await self.session.execute(
                select(func.count()).select_from(Invoice).filter(Invoice.user_id == user_id, Invoice.org_id == org_id)
            )
            total_invoices = total_invoices_query.scalar()

            result = await self.session.execute(
                select(Invoice)
                .filter(Invoice.user_id == user_id, Invoice.org_id == org_id)
                .offset(offset)
                .limit(page_size)
                .order_by(Invoice.invoice_date.desc())
            )

            invoices = result.scalars().all()
            total_pages = (total_invoices + page_size - 1) // page_size  # Ceiling division

            logger.info("Fetched %d invoices for user ID: %s", len(invoices), str(user_id))
            invoices_list = []
            for invoice in invoices:
                invoices_list.append({
                    "invoice_id": invoice.id,
                    "subscription_id": invoice.subscription_id,
                    "invoice_date": invoice.invoice_date,
                    "amount": invoice.amount,
                    "psp_invoice_id": invoice.psp_invoice_id,
                    "status": invoice.status,
                    "currency": invoice.currency,
                    "next_due_date": invoice.next_due_date,
                    "short_url": invoice.short_url,
                    "transaction_id": invoice.transaction_id,
                    "psp_name": invoice.psp_name
                })

            return {
                "invoices": invoices_list,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_invoices": total_invoices,
                    "total_pages": total_pages,
                },
            }
        except Exception as e:
            logger.error("Error fetching invoices for user ID %s with pagination: %s", str(user_id), str(e))
            raise InvoiceError(detail="Error fetching invoices with pagination.")

    @latency(metric=DB_QUERY_LATENCY)
    async def get_user_invoice(self, invoice_id: str, user_id: str, org_id: str):
        try:
            query = (select(Invoice).where(Invoice.id == invoice_id)
                     .filter(Invoice.user_id == user_id, Invoice.org_id == org_id))
            result = await self.session.execute(query)
            return result.scalar()
        except Exception as e:
            logger.error(f"Error fetching invoice {invoice_id} for user ID {user_id}: {e}")
            raise InvoiceError(detail=f"Error fetching invoice {invoice_id}.")
