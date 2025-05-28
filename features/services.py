import uuid6
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from features.models import Feature, PlanFeature, BackendService
from plans.models import Plan
from features.schemas import FeatureSchema, FeatureUpdateSchema
from features.exceptions import (
    FeatureNotFoundError,
    PlanNotFoundError,
    DuplicateFeatureAssignmentError,
    ServiceError, FeatureError
)
from prometheus.metrics import DB_QUERY_LATENCY
from utils.decorators import latency
from config.logging import logger


class FeaturesService:
    def __init__(self, connection_handler):
        self.session: AsyncSession = connection_handler.session

    @latency(metric=DB_QUERY_LATENCY)
    async def get_all_features(self):
        try:
            result = await self.session.execute(select(Feature))
            features = result.scalars().all()
            return features
        except Exception as e:
            logger.error(f"Error retrieving features: {e}")
            raise ServiceError(detail=str(e))

    @latency(metric=DB_QUERY_LATENCY)
    async def create_feature(self, feature_details: FeatureSchema):
        try:
            feature_data = feature_details.dict()
            feature_data['be_service'] = feature_details.be_service.name

            new_feature = Feature(id=uuid6.uuid6(), **feature_data)
            self.session.add(new_feature)
            await self.session.commit()
            await self.session.refresh(new_feature)
            logger.info(f"Feature created successfully: {new_feature.id}")
            return new_feature
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Unexpected error while creating feature: {e}")
            raise ServiceError(detail=str(e))

    @latency(metric=DB_QUERY_LATENCY)
    async def update_feature(self, feature_id: str, feature_details: FeatureUpdateSchema):
        try:
            result = await self.session.execute(select(Feature).filter(Feature.id == feature_id))
            feature = result.scalars().first()
            if not feature:
                raise FeatureNotFoundError(feature_id)

            for key, value in feature_details.dict(exclude_unset=True).items():
                setattr(feature, key, value)

            await self.session.commit()
            logger.info(f"Feature updated successfully: {feature.id}")
            return feature
        except FeatureNotFoundError:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating feature with ID {feature_id}: {e}")
            raise ServiceError(detail=str(e))

    @latency(metric=DB_QUERY_LATENCY)
    async def delete_feature(self, feature_id: str):
        try:
            result = await self.session.execute(select(Feature).filter(Feature.id == feature_id))
            feature = result.scalars().first()
            if not feature:
                raise FeatureNotFoundError(feature_id)

            await self.session.delete(feature)
            await self.session.commit()
            logger.info(f"Feature deleted successfully: {feature.id}")
        except FeatureNotFoundError:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting feature with ID {feature_id}: {e}")
            raise ServiceError(detail=str(e))

    @latency(metric=DB_QUERY_LATENCY)
    async def get_features_for_plan(self, plan_id: str):
        try:
            result = await self.session.execute(
                select(Feature).join(PlanFeature).filter(PlanFeature.plan_id == plan_id)
            )
            features = result.scalars().all()
            return features
        except Exception as e:
            logger.error(f"Error retrieving features for plan ID {plan_id}: {e}")
            raise ServiceError(detail=str(e))

    @latency(metric=DB_QUERY_LATENCY)
    async def add_feature_to_plan(self, plan_id: str, feature_id: str):
        try:
            # Check if the plan exists
            plan_result = await self.session.execute(select(Plan).filter(Plan.id == plan_id))
            plan = plan_result.scalars().first()
            if not plan:
                raise PlanNotFoundError(plan_id)

            # Check if the feature exists
            feature_result = await self.session.execute(select(Feature).filter(Feature.id == feature_id))
            feature = feature_result.scalars().first()
            if not feature:
                raise FeatureNotFoundError(feature_id)

            # Check if the mapping already exists
            existing_mapping = await self.session.execute(
                select(PlanFeature).filter(
                    PlanFeature.plan_id == plan_id, PlanFeature.feature_id == feature_id
                )
            )
            if existing_mapping.scalars().first():
                raise DuplicateFeatureAssignmentError(feature_id, plan_id)

            plan_feature = PlanFeature(id=uuid6.uuid6(), plan_id=plan_id, feature_id=feature_id)
            self.session.add(plan_feature)
            await self.session.commit()
            logger.info(f"Feature {feature_id} added to plan {plan_id}")
        except (PlanNotFoundError, FeatureNotFoundError, DuplicateFeatureAssignmentError):
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error adding feature {feature_id} to plan {plan_id}: {e}")
            raise ServiceError(detail=str(e))

    @latency(metric=DB_QUERY_LATENCY)
    async def remove_feature_from_plan(self, plan_id: str, feature_id: str):
        try:
            result = await self.session.execute(
                select(PlanFeature).filter(
                    PlanFeature.plan_id == plan_id, PlanFeature.feature_id == feature_id
                )
            )
            plan_feature = result.scalars().first()
            if not plan_feature:
                raise FeatureError(
                    message="Feature not associated with this plan",
                    detail=f"No PlanFeature record found for plan_id={plan_id} & feature_id={feature_id}",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            await self.session.delete(plan_feature)
            await self.session.commit()
            logger.info(f"Feature {feature_id} removed from plan {plan_id}")
        except FeatureError:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error removing feature {feature_id} from plan {plan_id}: {e}")
            raise ServiceError(detail=str(e))

    @latency(metric=DB_QUERY_LATENCY)
    async def get_features_by_service(self, service: BackendService):
        """Retrieve features filtered by backend service."""
        try:
            result = await self.session.execute(
                select(Feature).filter(Feature.be_service == service.value)
            )
            features = result.scalars().all()
            logger.info(f"Retrieved {len(features)} features for service: {service.value}")
            return features
        except Exception as e:
            logger.error(f"Unexpected error while retrieving features for service {service.value}: {e}")
            raise ServiceError(detail=str(e))
