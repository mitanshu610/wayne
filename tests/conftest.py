import pytest
from unittest.mock import AsyncMock, MagicMock

from rule_engine.services import RulesService
from utils.connection_handler import ConnectionHandler
from payments.services import PaymentsService
from integrations.razorpay_client import RazorpayClient
from utils.redis_client import RedisClient


@pytest.fixture
def mock_connection_handler():
    mock_handler = MagicMock(spec=ConnectionHandler)
    mock_handler.session = AsyncMock()
    return mock_handler

@pytest.fixture
def mock_razorpay_client():
    mock_client = MagicMock(spec=RazorpayClient)
    return mock_client

@pytest.fixture
def mock_redis_client():
    mock_client = MagicMock(spec=RedisClient)
    return mock_client

@pytest.fixture
def payments_service(mock_connection_handler, mock_razorpay_client, mock_redis_client):
    service = PaymentsService(connection_handler=mock_connection_handler)
    service.razorpay_client = mock_razorpay_client
    service.redis_client = mock_redis_client
    return service


@pytest.fixture
def rules_service(mock_connection_handler, mock_redis_client):
    service = RulesService(connection_handler=mock_connection_handler)
    service.redis_client = mock_redis_client
    return service