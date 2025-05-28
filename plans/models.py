from sqlalchemy import (
    Column, String, Boolean, UUID, Integer, Float, Date, ForeignKey, Index, DateTime
)
from sqlalchemy.dialects.postgresql import JSONB
from utils.sqlalchemy import Base, TimestampMixin
from sqlalchemy.orm import relationship


class Plan(TimestampMixin, Base):
    """
    A table to store plan details for each plan.
    """
    __tablename__ = 'plans'

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    amount = Column(String(50), nullable=False)
    currency = Column(String, nullable=False)
    billing_cycle = Column(String(50), nullable=False)
    slug = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    meta_data = Column(JSONB, nullable=True)
    psp_plan_id = Column(String, nullable=True)
    psp_price_id = Column(String, nullable=True)
    is_custom = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, default=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class PlanCoupon(TimestampMixin, Base):
    """
    A table to store coupons for each plan.

    This table handles coupon details such as code, discount type,
    discount value, usage limits, validity dates, and so on.
    """
    __tablename__ = 'plan_coupons'

    id = Column(UUID(as_uuid=True), primary_key=True)
    plan_id = Column(UUID(as_uuid=True), nullable=True)
    code = Column(String, nullable=False, unique=True)
    discount_type = Column(String(50), nullable=False)
    discount_value = Column(Float, nullable=False)
    usage_limit = Column(Integer, nullable=True)
    usage_count = Column(Integer, default=0)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    meta_data = Column(JSONB, nullable=True)

    __table_args__ = (
        Index('ix_plan_coupons_plan_id', plan_id),
        Index('ix_plan_coupons_is_active', is_active)
    )
