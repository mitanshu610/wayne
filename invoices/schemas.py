from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class CreateInvoiceSchema(BaseModel):
    subscription_id: UUID = Field(..., description="Subscription ID linked to the invoice")
    invoice_date: datetime = Field(..., description="Date the invoice was generated")
    amount: str = Field(..., description="Total amount for the invoice")
    status: str = Field(..., description="Status of the invoice (e.g., pending, paid)")
    currency: str = Field(..., description="Currency of the invoice amount")
    meta_data: Optional[dict] = Field(None, description="Additional metadata for the invoice")

class InvoiceSchema(BaseModel):
    id: UUID = Field(..., description="Unique identifier of the invoice")
    psp_invoice_id: str = Field(..., description="Invoice ID from the payment service provider")
    user_id: int = Field(..., description="User ID (BigInteger)")
    org_id: int = Field(..., description="Organization ID (BigInteger)")
    subscription_id: UUID = Field(..., description="Foreign key to the subscription")
    invoice_date: int = Field(..., description="Date of the invoice in epoch")
    amount: str = Field(..., description="Amount to be charged")
    status: str = Field(default="draft", description="Current status of the invoice")
    currency: str = Field(..., description="Currency code (e.g., 'USD', 'INR')")
    next_due_date: Optional[int] = Field(None, description="Next due date if recurring")
    short_url: str = Field(..., description="Short URL to access the invoice")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        from_attributes = True