from fastapi import HTTPException, Request, BackgroundTasks
from fastapi.params import Depends

from config.logging import logger, get_call_stack
from utils.connection_handler import get_connection_handler_for_app, ConnectionHandler
from webhooks.services import WebhookService, PaddleWebhookService


async def capture_razorpay_webhook(
        request: Request,
        background_tasks: BackgroundTasks,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app)
):
    try:
        payload = await request.json()
        logger.info(f"Received Razorpay webhook: {payload}")
        event = payload.get("event")

        webhook_service = WebhookService(connection_handler=connection_handler)

        event_mapper = {
            "subscription.activated": webhook_service.handle_subscription_activated,
            "payment.captured": webhook_service.handle_payment_event,
            "payment.failed": webhook_service.handle_payment_event,
            "subscription.cancelled": webhook_service.handle_subscription_cancelled,
            "invoice.paid": webhook_service.handle_invoice_paid,
            "invoice.expired": webhook_service.handle_invoice_expired
        }

        handler = event_mapper.get(event)
        if handler:
            background_tasks.add_task(handler, payload)
        else:
            logger.warning("Unhandled event type: %s", str(event))
            return {"status": "ignored", "message": f"Unhandled event type: {event}"}

        logger.info("Processed Razorpay event: %s", str(event))
        return {"status": "success", "message": "Webhook processed successfully"}

    except Exception as e:
        logger.error("Error processing Razorpay webhook: %s", str(e), call_stack=get_call_stack())
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def capture_paddle_webhook(
        request: Request,
        background_tasks: BackgroundTasks,
        connection_handler: ConnectionHandler = Depends(get_connection_handler_for_app)
):
    event = await request.json()
    # print("event >> ", event)
    event_type = event.get("event_type")

    webhook_service = PaddleWebhookService(connection_handler=connection_handler)
    event_mapper = {
        "transaction.completed": webhook_service.handle_transaction_completed_failed,
        "transaction.payment_failed": webhook_service.handle_transaction_completed_failed,
        "subscription.canceled": webhook_service.handle_subscription_cancelled
    }

    handler = event_mapper.get(event_type)
    if handler:
        background_tasks.add_task(handler, event)
    else:
        logger.warning("Unhandled event type: %s", str(event))
        return {"status": "ignored", "message": f"Unhandled event type: {event}"}

    pass
