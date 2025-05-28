import enum

from pydantic import BaseModel, Field, constr, validator
from typing import Optional, Dict, Any
from datetime import date, datetime

from slugify import slugify


class PlanSchema(BaseModel):
    """
    Schema for creating a new Plan
    """
    name: constr(min_length=1) = Field(
        ...,
        description="Name of the plan"
    )
    amount: constr(max_length=50) = Field(
        ...,
        description="Amount for the plan"
    )
    currency: constr(min_length=1) = Field(
        ...,
        description="Currency of the plan"
    )
    billing_cycle: constr(max_length=50) = Field(
        ...,
        description="Billing cycle for the plan"
    )
    description: Optional[str] = Field(
        None,
        description="Optional description of the plan"
    )
    meta_data: Optional[Dict] = Field(
        None,
        description="Additional metadata for the plan"
    )
    is_custom: bool = Field(
        default=False,
        description="Flag to indicate if the plan is custom"
    )
    slug: str = Field(
        None,
        description="Auto-generated slug for the plan"
    )

    def __init__(self, **data):
        super().__init__(**data)
        self.slug = slugify(self.name)


class PlanUpdateSchema(BaseModel):
    """
    Schema for updating an existing Plan
    """
    name: Optional[constr(min_length=1)] = Field(
        None,
        description="Name of the plan"
    )
    amount: Optional[constr(max_length=50)] = Field(
        None,
        description="Amount for the plan"
    )
    currency: Optional[constr(min_length=1)] = Field(
        None,
        description="Currency of the plan"
    )
    billing_cycle: Optional[constr(max_length=50)] = Field(
        None,
        description="Billing cycle for the plan"
    )
    description: Optional[str] = Field(
        None,
        description="Optional description of the plan"
    )
    meta_data: Optional[Dict] = Field(
        None,
        description="Additional metadata for the plan"
    )
    is_custom: Optional[bool] = Field(
        None,
        description="Flag to indicate if the plan is custom"
    )


class PlanCouponSchema(BaseModel):
    """
    Schema for creating or updating a PlanCoupon.
    """
    code: constr(min_length=1, max_length=50) = Field(
        ...,
        description="Unique coupon code"
    )
    discount_type: constr(min_length=1, max_length=50) = Field(
        ...,
        description="Discount type (e.g., 'percentage' or 'fixed')"
    )
    discount_value: float = Field(
        ...,
        description="Value of the discount"
    )
    usage_limit: Optional[int] = Field(
        None,
        description="Global usage limit for the coupon"
    )
    end_date: datetime = Field(
        ...,
        description="Date until which the coupon is valid"
    )


class DiscountType(enum.Enum):
    PERCENTAGE = "percentage"
    FLAT = "flat"