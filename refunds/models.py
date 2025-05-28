import enum
from sqlalchemy import (
    Column, String, UUID, Date, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from utils.sqlalchemy import Base, TimestampMixin
from sqlalchemy import Enum

class RefundStatusEnum(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Refund(TimestampMixin, Base):
    __tablename__ = 'refunds'
    id = Column(UUID(as_uuid=True), primary_key=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=False)
    refund_amount = Column(String, nullable=False)
    refund_date = Column(String, nullable=False)
    refund_currency = Column(String, nullable=False)
    refund_status = Column(String, nullable=False, default="initiated")
    refund_request_id = Column(UUID(as_uuid=True), ForeignKey('refund_requests.id'), nullable=False)
    razorpay_refund_id = Column(String, nullable=False)
    meta_data = Column(JSONB, nullable=True)

    __table_args__ = (
        Index('ix_refunds_subscription_id', subscription_id),
    )


class RefundStatus(TimestampMixin, Base):
    __tablename__ = 'refund_status'
    id = Column(UUID(as_uuid=True), primary_key=True)
    refund_id = Column(UUID(as_uuid=True), ForeignKey('refunds.id'), nullable=False)
    status = Column(String, nullable=False, default="initiated")


class RequestRefund(TimestampMixin, Base):
    __tablename__ = 'refund_requests'
    id = Column(UUID(as_uuid=True), primary_key=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=False)
    request_date = Column(Date, nullable=False)
    reason = Column(String, nullable=True)
    meta_data = Column(JSONB, nullable=True)
    status = Column(Enum(RefundStatusEnum), nullable=False, default=RefundStatusEnum.PENDING.value)

    __table_args__ = (
        Index('ix_request_refund_subscription_id', subscription_id),
    )