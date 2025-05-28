import pytest
from unittest.mock import AsyncMock, MagicMock
from payments.services import PaymentsService
from payments.schemas import CreateSubscription
from payments.exceptions import SubscriptionConflictError, PaymentError, SubscriptionNotFoundError
from utils.common import UserData


@pytest.fixture
def mock_user_data():
    return UserData(_id=1, orgId=4, firstName="test", lastName="user", workspace=[])


@pytest.mark.asyncio
async def test_ensure_idempotency(payments_service, mock_redis_client, mock_user_data):
    mock_redis_client.exists_key = AsyncMock(return_value=False)

    await payments_service._ensure_idempotency(mock_user_data)

    mock_redis_client.add_key.assert_called_once_with(
        f"subscription_idempotency_org:{mock_user_data.userId}:{mock_user_data.orgId}",
        "processing",
        expiration=300
    )


@pytest.mark.asyncio
async def test_ensure_idempotency_conflict(payments_service, mock_redis_client, mock_user_data):
    mock_redis_client.exists_key = AsyncMock(return_value=True)

    with pytest.raises(SubscriptionConflictError):
        await payments_service._ensure_idempotency(mock_user_data)


# @pytest.mark.asyncio
# async def test_delete_subscription_idempotency(payments_service, mock_redis_client, mock_user_data):
#     mock_redis_client.exists_key = AsyncMock(return_value=True)
#     mock_redis_client.delete_key = AsyncMock()
#
#     await payments_service.delete_subscription_idempotency(mock_user_data)
#
#     mock_redis_client.delete_key.assert_called_once_with(
#         f"subscription_idempotency_org:{mock_user_data.userId}:{mock_user_data.orgId}"
#     )


@pytest.mark.asyncio
async def test_ensure_customer_exists(payments_service, mock_user_data):
    payments_service.payments_dao.get_customer_by_user_and_org_id = AsyncMock(return_value=None)
    payments_service.razorpay_client.create_customer = AsyncMock(return_value={"id": "cust_123"})
    payments_service.payments_dao.create_customer = AsyncMock(return_value={"customer_id": "cust_123"})

    customer = await payments_service._ensure_customer_exists(mock_user_data)

    assert customer["customer_id"] == "cust_123"
    payments_service.razorpay_client.create_customer.assert_called_once_with(mock_user_data)


@pytest.mark.asyncio
async def test_create_subscription(payments_service, mock_user_data, mock_redis_client):
    subscription_details = CreateSubscription(plan_id="plan_123", psp_name="razorpay")
    mock_redis_client.exists_key.return_value = False

    # Mock DAO methods
    payments_service.payments_dao.get_subscriptions_by_user_and_org_id = AsyncMock(return_value=None)
    payments_service.payments_dao.get_customer_by_user_and_org_id = AsyncMock(return_value=None)
    payments_service.razorpay_client.create_customer = AsyncMock(return_value={"id": "cust_123"})
    payments_service.payments_dao.create_customer = AsyncMock(return_value=MagicMock(customer_id="cust_123"))
    payments_service.plans_dao.get_plan_by_id = AsyncMock(return_value=MagicMock(is_custom=False, amount="100"))
    payments_service.coupon_service.validate_and_apply_coupon = AsyncMock(return_value=(0, None))
    payments_service.plans_service.create_discounted_plan_if_needed = AsyncMock(
        return_value=MagicMock(razorpay_plan_id="plan_razorpay_123"))
    payments_service.razorpay_client.create_subscription = AsyncMock(return_value={"id": "sub_123", "status": "active"})
    payments_service.payments_dao.save_subscription = AsyncMock(return_value={"id": "sub_123", "status": "active"})

    subscription = await payments_service.create_subscription(subscription_details, mock_user_data)

    assert subscription["status"] == "active"
    payments_service.razorpay_client.create_subscription.assert_called_once()



@pytest.mark.asyncio
async def test_create_subscription_conflict(payments_service, mock_user_data):
    subscription_details = CreateSubscription(plan_id="plan_123", psp_name="razorpay")

    payments_service.payments_dao.get_subscriptions_by_user_and_org_id = AsyncMock(return_value=True)

    with pytest.raises(PaymentError):
        await payments_service.create_subscription(subscription_details, mock_user_data)


@pytest.mark.asyncio
async def test_get_subscription_by_id(payments_service):
    payments_service.payments_dao.get_subscription_by_id = AsyncMock(return_value={"id": "sub_123"})

    subscription = await payments_service.get_subscription_by_id("sub_123")

    assert subscription["id"] == "sub_123"


@pytest.mark.asyncio
async def test_get_subscription_by_id_not_found(payments_service):
    payments_service.payments_dao.get_subscription_by_id = AsyncMock(return_value=None)

    with pytest.raises(SubscriptionNotFoundError):
        await payments_service.get_subscription_by_id("sub_123")


@pytest.mark.asyncio
async def test_get_subscriptions_by_user_org(payments_service, mock_user_data):
    mock_subscription = MagicMock(plan_id="plan_123")
    payments_service.payments_dao.get_subscriptions_by_user_and_org_id = AsyncMock(return_value=mock_subscription)

    # Explicitly set the 'name' and 'description' attributes
    mock_plan = MagicMock()
    mock_plan.name = "Plan A"
    mock_plan.description = "Description A"

    payments_service.plans_dao.get_plan_by_id = AsyncMock(return_value=mock_plan)

    subscription_details = await payments_service.get_subscriptions_by_user_org(
        mock_user_data.userId,
        mock_user_data.orgId
    )

    # Assert the correct name is returned
    assert subscription_details["plan_name"] == "Plan A"


@pytest.mark.asyncio
async def test_unsubscribe(payments_service, mock_user_data):
    mock_subscription = MagicMock(psp_subscription_id="sub_razorpay_123")
    payments_service.payments_dao.get_subscriptions_by_user_and_org_id = AsyncMock(return_value=mock_subscription)
    payments_service.razorpay_client.end_subscription = AsyncMock()
    payments_service.payments_dao.update_subscription = AsyncMock()

    await payments_service.unsubscribe(mock_user_data.userId, mock_user_data.orgId)

    payments_service.razorpay_client.end_subscription.assert_called_once_with("sub_razorpay_123")
    payments_service.payments_dao.update_subscription.assert_called_once()
