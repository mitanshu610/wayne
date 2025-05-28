from sqlalchemy import (
    Column, String, Date, ForeignKey, UUID, Integer, Enum, DateTime, Index, BigInteger
)
from sqlalchemy.dialects.postgresql import JSONB

from payments.models import PSPName, PaymentStatus
from utils.sqlalchemy import Base, TimestampMixin


class PaygoUsage(TimestampMixin, Base):
    __tablename__ = 'paygo_usage'

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    user_id = Column(String, nullable=False)
    org_id = Column(String, nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('paygo_plans.id'), nullable=False)
    usage_metric = Column(String(255), nullable=False)
    usage_units = Column(Integer, nullable=False)
    usage_date = Column(Date, nullable=False)
    billing_cycle_date = Column(Date, nullable=True)


class PaygoOrders(TimestampMixin, Base):
    __tablename__ = 'paygo_orders'
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(String, nullable=False)
    org_id = Column(String, nullable=False)
    amount = Column(String(50), nullable=False)
    currency = Column(String(50), nullable=False)
    psp_order_id = Column(String(50), nullable=False, index=True)
    psp_name = Column(Enum(PSPName), nullable=False)


class PaygoPlan(TimestampMixin, Base):
    __tablename__ = 'paygo_plans'

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    quota_limit = Column(Integer, nullable=True)
    quota_reset = Column(String(50), nullable=True)


class PaygoInvoice(TimestampMixin, Base):
    __tablename__ = 'paygo_invoices'

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    user_id = Column(String, nullable=False)
    org_id = Column(String, nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey('paygo_orders.id'), nullable=False)
    invoice_date = Column(Date, nullable=False)
    amount = Column(String, nullable=False)
    status = Column(String(50), nullable=False)
    currency = Column(String(10), nullable=False)


class PaygoPayments(TimestampMixin, Base):
    __tablename__ = 'paygo_payments'

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    user_id = Column(String, nullable=False)
    org_id = Column(String, nullable=False)
    psp_payment_id = Column(String(50), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey('paygo_orders.id'), nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False, index=True)
    psp_name = Column(Enum(PSPName), nullable=False)
    payment_date = Column(DateTime(timezone=True), nullable=False, index=True)
    amount = Column(String(50), nullable=False)
    currency = Column(String(50), nullable=False)

    __table_args__ = (
        Index('ix_paygo_payments_user_org', 'user_id', 'org_id'),
    )


class PaygoMetricDefinition(TimestampMixin, Base):
    __tablename__ = 'paygo_metric_definitions'

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(String, nullable=True)
    rate_per_unit = Column(String, nullable=False)


class PlanMetric(TimestampMixin, Base):
    __tablename__ = 'paygo_plan_metric'

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('paygo_plans.id'), nullable=False, index=True)
    metric_id = Column(UUID(as_uuid=True), ForeignKey('paygo_metric_definitions.id'), nullable=False, index=True)
