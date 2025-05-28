import enum

from sqlalchemy import (
    Column, String, Boolean, ForeignKey, UUID, Enum, Integer, Index, BigInteger, JSON
)
from utils.sqlalchemy import Base, TimestampMixin


class PSPName(enum.Enum):
    STRIPE = "Stripe"
    RAZORPAY = "Razorpay"
    PADDLE = "Paddle"


class ProviderName(enum.Enum):
    STRIPE = "stripe"
    RAZORPAY = "razorpay"
    PADDLE = "paddle"


class BillingCycle(enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "yearly"


class PaymentStatus(enum.Enum):
    CAPTURED = "captured"
    FAILED = "failed"
    PENDING = "pending"


class Subscriptions(TimestampMixin, Base):
    __tablename__ = 'subscriptions'
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(String, nullable=False)
    org_id = Column(String, nullable=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('plans.id'), nullable=False, index=True)
    start_date = Column(Integer, nullable=False, index=True)
    end_date = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=False, index=True)
    is_trial = Column(Boolean, default=False, index=True)
    cancel_at_cycle_end = Column(Boolean, nullable=False, default=False)
    billing_cycle = Column(Enum(BillingCycle), nullable=False)
    amount = Column(String(50), nullable=False)
    currency = Column(String(50), nullable=False)
    psp_name = Column(Enum(PSPName), nullable=False)
    psp_subscription_id = Column(String(255), nullable=True, index=True)
    status = Column(String, nullable=False, index=True)

    __table_args__ = (
        Index('ix_subscriptions_user_org', 'user_id', 'org_id'),
    )

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Payments(TimestampMixin, Base):
    __tablename__ = 'payments'
    id = Column(UUID(as_uuid=True), primary_key=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=False, index=True)
    user_id = Column(String, nullable=False)
    org_id = Column(String, nullable=True)
    payment_date = Column(Integer, nullable=False, index=True)  # Epoch time
    amount = Column(String(50), nullable=False)
    currency = Column(String(50), nullable=False)
    psp_payment_id = Column(String(50), nullable=False, index=True)
    psp_name = Column(Enum(PSPName), nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False)

    __table_args__ = (
        Index('ix_payments_subscription_id', 'subscription_id'),
        Index('ix_payments_user_org', 'user_id', 'org_id')
    )


class RequestResponseLog(TimestampMixin, Base):
    __tablename__ = 'request_response_logs'
    id = Column(UUID(as_uuid=True), primary_key=True)
    request_data = Column(String, nullable=False)
    response_data = Column(String, nullable=False)
    reason = Column(String, nullable=True)


class Customer(TimestampMixin, Base):
    __tablename__ = 'customers'
    id = Column(UUID(as_uuid=True), primary_key=True)
    customer_id = Column(String, nullable=True, index=True)
    psp_name = Column(Enum(PSPName), nullable=False)
    user_id = Column(String, nullable=False)
    org_id = Column(String, nullable=True)

    __table_args__ = (
        Index('ix_customers_user_org', 'user_id', 'org_id'),
    )


class ScheduledDowngrade(TimestampMixin, Base):
    __tablename__ = 'scheduled_downgrades'

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(String, nullable=False)
    org_id = Column(String, nullable=True)
    scheduled_at = Column(Integer, nullable=False)
    status = Column(String, default="pending", index=True)

    __table_args__ = (
        Index('ix_scheduleddowngrade_user_org', 'user_id', 'org_id'),
    )