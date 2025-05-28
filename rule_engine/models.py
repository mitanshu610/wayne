import enum

from sqlalchemy import (
    Column,
    String,
    Boolean,
    ForeignKey,
    Enum, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from utils.sqlalchemy import TimestampMixin, Base
from features.models import BackendService
from sqlalchemy.orm import relationship


class ScopeEnum(enum.Enum):
    ORGANISATION = "organisation"
    USER = "user"
#
# class OperatorEnum(enum.Enum):
#     EQUAL = "="
#     GREATER_THAN = ">"
#     LESS_THAN = "<"
#     GREATER_THAN_OR_EQUAL = ">="
#     LESS_THAN_OR_EQUAL = "<="

class Rule(TimestampMixin, Base):
    __tablename__ = 'rules'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    scope = Column(Enum(ScopeEnum), nullable=False, index=True)
    enabled = Column(Boolean, nullable=False, default=True)
    meta_data = Column(JSONB, nullable=True, default=dict)
    rule_slug = Column(String, nullable=False)
    rule_class_name = Column(String, nullable=False)
    service_slug = Column(Enum(BackendService), nullable=False)
    condition_data = Column(JSONB, nullable=True)

    plan_rules = relationship("PlanRule", back_populates="rule")

    def __repr__(self):
        return f"<Rule(id={self.id}, name={self.name}, scope={self.scope})>"


# class RuleCondition(TimestampMixin, Base):
#     __tablename__ = 'rule_conditions'
#
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
#     rule_id = Column(UUID(as_uuid=True), ForeignKey('rules.id'), nullable=False, index=True)
#     condition_key = Column(String, nullable=False)  # Example: "users_count"
#     operator = Column(Enum(OperatorEnum), nullable=False)  # Example: ">=", "<", "="
#     value = Column(String, nullable=False)  # Value to compare against
#     meta_data = Column(JSONB, nullable=True, default=dict)
#     time_period = Column(String, nullable=True)  # Example: "Monthly", "Yearly", "hourly"
#
#     def __repr__(self):
#         return f"<RuleCondition(id={self.id}, rule_id={self.rule_id}, condition_key={self.condition_key})>"


class PlanRule(TimestampMixin, Base):
    __tablename__ = 'plan_rules'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('plans.id'), nullable=False, index=True)
    rule_id = Column(UUID(as_uuid=True), ForeignKey('rules.id'), nullable=False, index=True)
    meta_data = Column(JSONB, nullable=True, default=dict)

    rule = relationship("Rule", back_populates="plan_rules")

    __table_args__ = (
        UniqueConstraint('plan_id', 'rule_id', name='uq_plan_rule'),
    )

    def __repr__(self):
        return f"<PlanRule(id={self.id}, plan_id={self.plan_id}, rule_id={self.rule_id})>"
