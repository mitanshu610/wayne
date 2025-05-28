import uuid6
from sqlalchemy.ext.asyncio import AsyncSession

from config.logging import logger
from payments.models import PSPName, Payments, PaymentStatus


class WebhookDAO:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_payment_details(self, user_id, org_id, subscription_id, created_at, amount, currency, payment_id,
                                     payment_status, psp_name: PSPName = PSPName.RAZORPAY):
        try:
            payment = Payments(
                id=uuid6.uuid6(),
                subscription_id=subscription_id,
                user_id=user_id,
                org_id=org_id,
                payment_date=created_at,
                amount=str(amount),
                currency=currency,
                psp_payment_id=payment_id,
                psp_name=psp_name,
                status=PaymentStatus(payment_status),
            )

            self.session.add(payment)
            await self.session.commit()
        except Exception as e:
            logger.error("Error while recording subscription to DB: %s", str(e))
            raise e
