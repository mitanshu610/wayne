from typing import List, Dict

from clerk_integration.utils import UserData

from config.logging import logger
from config.settings import loaded_config
from rule_engine.dao import RulesDAO
from rule_engine.schemas import RuleDetailsSchema
from utils.connection_handler import ConnectionHandler
from utils.redis_client import RedisClient


class StatisticsService:

    def __init__(self, connection_handler: ConnectionHandler):
        self.redis_client = RedisClient()
        self.rules_dao = RulesDAO(connection_handler.session)

    async def get_service_usage_stats(self, user_data: UserData) -> List[Dict]:
        """
        Get service usage statistics with concise rule details as a flat list with usage percentage.

        Returns:
            List of rule statistics objects with flat structure and calculated usage percentage.
        """
        stats_list = []
        try:
            plan_id = user_data.publicMetadata.get("subscription", {}).get(
                "active_plan_id", "") or loaded_config.fallback_plan_id
            plan_rules = await self.rules_dao.get_rules_by_plan_id(plan_id)

            for rule in plan_rules:
                redis_rule_key = f"org:{user_data.orgId}:rule:{rule.id}" if user_data.orgId \
                    else f"user:{user_data.userId}:rule:{rule.id}"
                current_rule_usage = await self.redis_client.get_key(redis_rule_key) or 0
                try:
                    # Convert to Pydantic model and then to dict
                    rule_details = RuleDetailsSchema.model_validate(rule).model_dump()

                    # Extract request_limit from condition_data
                    request_limit = None
                    reset_period = None
                    if rule_details.get("condition_data") and isinstance(rule_details["condition_data"], dict):
                        request_limit = rule_details["condition_data"].get("request_limit")
                        reset_period = rule_details["condition_data"].get("reset_period")

                    # Calculate percentage if possible
                    usage_percentage = 0
                    if request_limit and current_rule_usage and current_rule_usage.isdigit():
                        current_value = int(current_rule_usage)
                        usage_percentage = round((current_value / request_limit) * 100, 2)

                    # Create flat structure
                    stat_obj = {
                        "id": rule.id,
                        "name": rule_details.get("name"),
                        "description": rule_details.get("description"),
                        "enabled": rule_details.get("enabled"),
                        "current_value": int(current_rule_usage),
                        "request_limit": request_limit,
                        "usage_percentage": usage_percentage,
                        "reset_period": reset_period
                    }

                    stats_list.append(stat_obj)

                except Exception as rule_err:
                    stats_list.append({
                        "id": rule.id,
                        "current_value": current_rule_usage,
                        "error": str(rule_err)
                    })

            return stats_list

        except Exception as e:
            logger.error(f"Error getting service usage stats: {str(e)}")
            raise Exception(f"Failed to retrieve service usage statistics: {str(e)}")
