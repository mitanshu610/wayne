import httpx
from config.settings import loaded_config
from config.logging import logger


async def initiate_razorpay_refund(payment_id: str, refund_amount: str) -> str:
    """
    Initiate a refund in Razorpay and return the Razorpay refund ID.
    """
    url = f"https://api.razorpay.com/v1/payments/{payment_id}/refund"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {loaded_config.razorpay_api_secret}"
    }
    body = {
        "amount": int(refund_amount)
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=body)
            response_data = response.json()

            if response.status_code in (200, 201):
                logger.info(f"Razorpay refund created successfully: {response_data}")
                return response_data["id"]
            else:
                logger.error(f"Error initiating Razorpay refund: {response_data}")
                raise ValueError("Failed to initiate Razorpay refund")
        except httpx.RequestError as exc:
            logger.error(f"Error connecting to Razorpay: {exc}")
            raise exc