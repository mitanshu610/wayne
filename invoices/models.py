from sqlalchemy import (
    Column, String, ForeignKey, UUID, Integer, Index, BigInteger
)
from sqlalchemy.dialects.postgresql import JSONB
from utils.sqlalchemy import Base, TimestampMixin


class Invoice(TimestampMixin, Base):
    __tablename__ = 'invoices'
    id = Column(UUID(as_uuid=True), primary_key=True)
    psp_invoice_id = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=False)
    org_id = Column(String, nullable=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=False, index=True)
    invoice_date = Column(Integer, nullable=False, index=True)
    amount = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True, default="draft")
    currency = Column(String, nullable=False)
    next_due_date = Column(Integer, nullable=True)
    short_url = Column(String, nullable=False)
    transaction_id = Column(String, nullable=True)
    psp_name = Column(String, nullable=True)
    meta_data = Column(JSONB, nullable=True, default=dict)

    __table_args__ = (
        Index('ix_invoices_user_org', 'user_id', 'org_id'),
    )

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}