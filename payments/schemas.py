import enum
from typing import Optional

from pydantic import BaseModel, Field


class CreateSubscription(BaseModel):
    plan_id: str
    psp_name: str
    coupon_id: Optional[str] = None
    is_active: bool = False

class PlanUpgradeSchema(BaseModel):
    plan_id: str

class PlanSlugs(enum.Enum):
    BASIC = "basic-plan"
    PRO_MONTHLY = "pro-plan-monthly-test"
    PRO_YEARLY = "premium-yearly"

class SubscriptionResponseSchema(BaseModel):
    amount: Optional[str] = None
    billing_cycle: Optional[str] = None
    plan_name: str
    plan_description: Optional[str] = None
    psp_subscription_details: dict