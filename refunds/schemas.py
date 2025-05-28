from pydantic import BaseModel, Field, constr, UUID4
from typing import Optional, Dict, Any


class RefundSchema(BaseModel):
    """
    Schema for creating or initiating a refund.
    """
    order_id: UUID4 = Field(
        ...,
        description="UUID of the associated transaction"
    )
    refund_amount: constr(min_length=1) = Field(
        ...,
        description="Amount to be refunded"
    )
    refund_currency: constr(min_length=1, max_length=3) = Field(
        ...,
        description="Currency of the refund (e.g., 'INR', 'USD')"
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for initiating the refund"
    )
    meta_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata for the refund"
    )

class RequestRefundSchema:
    order_id: str
    request_date: str
    reason: str
    meta_data: dict = None

class UpdateRefundRequestSchema:
    request_refund_id: str
    status: str