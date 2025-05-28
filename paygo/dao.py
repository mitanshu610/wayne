import uuid6
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from paygo.schemas import CreatePaygoOrderSchema
from paygo.models import PaygoOrders
from config.logging import logger
from utils.common import UserData


class PaygoDAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_paygo_order(self, order_details: CreatePaygoOrderSchema):
        order = PaygoOrders(
            id=uuid6.uuid6(),
            user_id=order_details.user_id,
            org_id=order_details.org_id,
            amount=order_details.amount,
            currency=order_details.currency,
            psp_name=order_details.psp_name
        )
        self.session.add(order)
        await self.session.commit()

    async def get_paygo_order_by_id(self, order_id: str):
        result = await self.session.execute(
            select(PaygoOrders).filter(PaygoOrders.id == order_id)
        )
        return result.scalars().first()
