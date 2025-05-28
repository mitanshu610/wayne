import uuid6
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, update

from refunds.models import Refund, RequestRefund
from payments.models import Subscriptions
from refunds.schemas import RefundSchema, RequestRefundSchema, UpdateRefundRequestSchema
from config.logging import logger
from utils.decorators import latency
from prometheus.metrics import DB_QUERY_LATENCY


class RefundsDAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    @latency(metric=DB_QUERY_LATENCY)
    async def get_refund_by_id(self, refund_id: str):
        """Retrieve a specific refund by ID."""
        try:
            result = await self.session.execute(select(Refund).filter(Refund.id == refund_id))
            refund = result.scalars().first()
            if not refund:
                raise ValueError("Refund not found")
            return refund
        except Exception as e:
            logger.error(f"Error retrieving refund with ID {refund_id}: {e}")
            raise

    @latency(metric=DB_QUERY_LATENCY)
    async def get_refunds_by_entity(self, org_id):
        """
        Retrieve refunds associated with a specific user or organization by joining orders and refunds.
        Either `user_id` or `org_id` can be provided, or both can be None.
        """
        try:
            query = select(Refund).join(Subscriptions, Refund.order_id == Subscriptions.id)
            query = query.filter(Subscriptions.org_id == org_id)
            result = await self.session.execute(query)
            refunds = result.scalars().all()
            if not refunds:
                logger.info(f"No refunds found")
            return refunds
        except Exception as e:
            logger.error(f"Unexpected error while retrieving refunds: {e}")
            raise

    @latency(metric=DB_QUERY_LATENCY)
    async def create_refund(self, refund_details: RefundSchema, razorpay_refund_id: str):
        """Create a new refund."""
        try:
            new_refund_id = uuid6.uuid6()
            new_refund = Refund(
                id=new_refund_id,
                razorpay_refund_id=razorpay_refund_id,
                **refund_details.dict()
            )
            self.session.add(new_refund)
            await self.session.commit()
            await self.session.refresh(new_refund)
            return new_refund
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Unexpected error while creating refund: {e}")
            raise

    @latency(metric=DB_QUERY_LATENCY)
    async def create_refund_request(self, refund_request_details: RequestRefundSchema):
        """Create a new refund request."""
        try:
            new_request_id = uuid6.uuid6()  # Generate a new UUID for the refund request
            new_request = RequestRefund(
                id=new_request_id,
                order_id=refund_request_details.order_id,
                request_date=refund_request_details.request_date,
                reason=refund_request_details.reason,
                meta_data=refund_request_details.meta_data,
                status="pending"
            )
            self.session.add(new_request)
            await self.session.commit()
            await self.session.refresh(new_request)
            return new_request
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Unexpected error while creating refund request: {e}")
            raise e

    @latency(metric=DB_QUERY_LATENCY)
    async def get_all_refund_requests(self, page: int, page_size: int):
        """
        Get all refund requests with pagination using session.execute.
        """
        try:
            offset = (page - 1) * page_size

            query = select(RequestRefund).offset(offset).limit(page_size)
            result = await self.session.execute(query)
            refund_requests = result.scalars().all()

            count_query = select(func.count(RequestRefund.id))
            count_result = await self.session.execute(count_query)
            total_count = count_result.scalar()

            return {
                "refund_requests": refund_requests,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": (total_count + page_size - 1) // page_size,
                },
            }
        except Exception as e:
            logger.error(f"Unexpected error while retrieving refund requests: {e}")
            raise e

    @latency(metric=DB_QUERY_LATENCY)
    async def update_refund_request(self, request_data: UpdateRefundRequestSchema):
        """
        Update a refund request by ID.
        """
        try:
            query = (
                update(RequestRefund)
                .where(RequestRefund.id == request_data.request_refund_id)
                .values(**request_data.dict(exclude_unset=True))
                .execution_options(synchronize_session="fetch")
            )
            await self.session.execute(query)
            await self.session.commit()

            result = await self.session.execute(select(RequestRefund).filter(RequestRefund.id == request_data.request_refund_id))
            updated_request = result.scalars().first()

            if not updated_request:
                raise ValueError(f"Refund request with ID {request_data.request_refund_id} not found")

            return updated_request
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating refund request with ID {request_data.request_refund_id}: {e}")
            raise