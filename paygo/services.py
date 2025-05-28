from config.logging import logger
from utils.common import UserData
from paygo.dao import PaygoDAO
from paygo.schemas import CreatePaygoOrderSchema
from utils.connection_handler import ConnectionHandler
from integrations.razorpay_client import RazorpayClient


class PaygoService:
    def __init__(self, connection_handler: ConnectionHandler = None):
        self.connection_handler = connection_handler
        self.paygo_dao = PaygoDAO(session=connection_handler.session)
        self.razorpay_client = RazorpayClient()

    async def create_paygo_order(self, order_details: CreatePaygoOrderSchema, user_data: UserData):
        logger.info(f"user_data: {user_data}")
        await self.paygo_dao.save_paygo_order(order_details)

    async def get_paygo_order_by_id(self, order_id: str):
        return await self.paygo_dao.get_paygo_order_by_id(order_id)