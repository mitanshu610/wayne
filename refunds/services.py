from payments.dao import PaymentsDAO
from refunds.schemas import RefundSchema, RequestRefundSchema, UpdateRefundRequestSchema
from refunds.dao import RefundsDAO
from config.logging import logger
from refunds.utils import initiate_razorpay_refund


class RefundsService:
    def __init__(self, connection_handler):
        self.connection_handler = connection_handler
        self.refunds_dao = RefundsDAO(session=connection_handler.session)
        self.payments_dao = PaymentsDAO(session=connection_handler.session)

    async def get_all_refunds_by_entity(self, org_id):
        """
        Retrieve all refunds using DAO.
        """
        return await self.refunds_dao.get_refunds_by_entity(org_id)

    async def get_refund_by_id(self, refund_id: str):
        """
        Retrieve a specific refund by ID using DAO.
        """
        return await self.refunds_dao.get_refund_by_id(refund_id)

    async def initiate_refund(self, refund_details: RefundSchema):
        """
        Initiate a new refund.
        """
        order_details = await self.payments_dao.get_order_by_id(refund_details.order_id)
        razorpay_refund_id = await initiate_razorpay_refund(order_details.psp_payment_id, order_details.amount)
        return await self.refunds_dao.create_refund(refund_details, razorpay_refund_id)

    async def request_refund(self, refund_request_details: RequestRefundSchema):
        """
        Request a new refund.

        This method creates an entry in the `RequestRefund` table and marks the status as "pending."
        """
        order_details = await self.payments_dao.get_order_by_id(refund_request_details.order_id)
        if not order_details:
            logger.error(f"Order with ID {refund_request_details.order_id} not found.")
            raise ValueError(f"Order with ID {refund_request_details.order_id} not found.")
        refund_request_id = await self.refunds_dao.create_refund_request(refund_request_details)
        logger.info(f"Refund request created successfully with ID: {refund_request_id}")

    async def get_all_refund_requests(self, page: int, page_size: int):
        """
        Get all refund requests with pagination.
        """
        return await self.refunds_dao.get_all_refund_requests(page, page_size)

    async def update_refund_request(self, request_data: UpdateRefundRequestSchema):
        """
        Update a refund request by ID.
        """
        return await self.refunds_dao.update_refund_request(request_data)