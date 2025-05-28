import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_add_rule_to_plan(rules_service, mock_redis_client):
    # Mock the methods
    rules_service.rules_dao.add_rule_to_plan = AsyncMock()
    rules_service.rules_dao.get_rule_by_id = AsyncMock(return_value=MagicMock(service_slug=MagicMock(value="service_slug")))
    rules_service.rules_dao.get_plan_rules_with_conditions = AsyncMock(return_value={"rules": []})
    background_task = MagicMock()

    await rules_service.add_rule_to_plan("plan_123", "rule_123", background_task)

    rules_service.rules_dao.add_rule_to_plan.assert_called_once_with("plan_123", "rule_123")
    background_task.add_task.assert_called_once()

    for call in background_task.add_task.call_args_list:
        func, *args = call[0]
        await func(*args)

    mock_redis_client.add_key.assert_called_once_with(
        "plan_rules:service_slug:plan_123", '{"rules": []}'
    )


@pytest.mark.asyncio
async def test_remove_rule_from_plan(rules_service, mock_redis_client):
    # Mock the methods
    rules_service.rules_dao.remove_rule_from_plan = AsyncMock()
    rules_service.rules_dao.get_rule_by_id = AsyncMock(return_value=MagicMock(service_slug=MagicMock(value="service_slug")))
    rules_service.rules_dao.get_plan_rules_with_conditions = AsyncMock(return_value={"rules": []})
    background_task = MagicMock()

    await rules_service.remove_rule_from_plan("plan_123", "rule_123", background_task)

    rules_service.rules_dao.remove_rule_from_plan.assert_called_once_with("plan_123", "rule_123")
    background_task.add_task.assert_called_once()

    for call in background_task.add_task.call_args_list:
        func, *args = call[0]
        await func(*args)

    mock_redis_client.add_key.assert_called_once_with(
        "plan_rules:service_slug:plan_123", '{"rules": []}'
    )

@pytest.mark.asyncio
async def test_update_plan_rules_in_redis(rules_service, mock_redis_client):
    rules_service.rules_dao.get_rule_by_id = AsyncMock(return_value=MagicMock(service_slug=MagicMock(value="service_slug")))
    rules_service.rules_dao.get_plan_rules_with_conditions = AsyncMock(return_value={"rules": []})

    await rules_service.update_plan_rules_in_redis("plan_123", "rule_123")

    mock_redis_client.add_key.assert_called_once_with(
        "plan_rules:service_slug:plan_123", '{"rules": []}'
    )