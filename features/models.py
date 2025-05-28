from sqlalchemy import (
    Column, String, ForeignKey, UUID, Enum, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from utils.sqlalchemy import Base, TimestampMixin
from plans.models import Plan
import enum


class BackendService(enum.Enum):
    CEREBRUM = "cerebrum"
    REVIEW_PILOT = "review-pilot"


class Feature(TimestampMixin, Base):
    __tablename__ = 'features'

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False)
    description = Column(String, nullable=False)
    be_service = Column(Enum(BackendService, name="backendservice"), nullable=False)
    meta_data = Column(JSONB, nullable=True)

    __table_args__ = (
        Index('ix_features_name', name),  # Single-column index on 'name' for filtering/search
        Index('ix_features_slug', slug),  # Single-column index on 'slug' for unique lookups
        Index('ix_features_be_service', be_service),  # Single-column index on 'be_service'
    )

class PlanFeature(TimestampMixin, Base):
    __tablename__ = 'plan_features'

    id = Column(UUID(as_uuid=True), primary_key=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('plans.id'), nullable=False)
    feature_id = Column(UUID(as_uuid=True), ForeignKey('features.id'), nullable=False)

    __table_args__ = (
        Index('ix_plan_features_plan_id', plan_id),
        Index('ix_plan_features_feature_id', feature_id),
        Index('ix_plan_features_composite', plan_id, feature_id)
    )