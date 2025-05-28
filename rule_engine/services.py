import json
from typing import Optional

from fastapi import BackgroundTasks

from rule_engine.dao import RulesDAO
from rule_engine.schemas import RuleSchema
from utils.connection_handler import ConnectionHandler
from utils.redis_client import RedisClient


class RulesService:
    def __init__(self, connection_handler: ConnectionHandler):
        self.connection_handler = connection_handler
        self.rules_dao = RulesDAO(session=connection_handler.session)
        self.redis_client = RedisClient()

    async def get_rules_by_plan(self, plan_id: str):
        """
        Fetches all rules associated with a specific plan ID.

        :param plan_id: The ID of the plan.
        :return: A list of Rule objects associated with the given plan.
        """
        rules = await self.rules_dao.get_rules_by_plan_id(plan_id)
        return rules

    async def add_rule_to_plan(self, plan_id, rule_id, background_task: BackgroundTasks):
        """
        Adds a rule to a plan and schedules a background task to update the Redis cache.

        :param plan_id: The ID of the plan.
        :param rule_id: The ID of the rule to be added to the plan.
        :param background_task: FastAPI's BackgroundTasks instance to handle asynchronous tasks.
        :return: None
        """
        await self.rules_dao.add_rule_to_plan(plan_id, rule_id)
        background_task.add_task(self.update_plan_rules_in_redis, plan_id, rule_id)

    async def create_rule(self, rule_details: RuleSchema):
        """
        Creates a new rule along with its associated conditions.

        :param rule_details: An instance of RuleSchema containing rule and condition details.
        :return: The newly created Rule object with its associated conditions.
        """
        rule_data = rule_details.dict()
        rule_data["scope"] = rule_data["scope"].upper()
        new_rule = await self.rules_dao.create_rule(rule_data)
        return new_rule

    async def remove_rule_from_plan(self, plan_id, rule_id, background_task: BackgroundTasks):
        """
        Removes a rule from a plan and schedules a background task to update the Redis cache.

        :param plan_id: The ID of the plan.
        :param rule_id: The ID of the rule to be removed from the plan.
        :param background_task: FastAPI's BackgroundTasks instance to handle asynchronous tasks.
        :return: None
        """
        await self.rules_dao.remove_rule_from_plan(plan_id, rule_id)
        background_task.add_task(self.update_plan_rules_in_redis, plan_id, rule_id)

    async def update_plan_rules_in_redis(self, plan_id, rule_id):
        """
        Updates the Redis cache for the rules associated with a given plan.

        :param plan_id: The ID of the plan.
        :param rule_id: The ID of the rule.
        :return: None
        """
        rule_details = await self.rules_dao.get_rule_by_id(rule_id)
        rules_data_with_conditions = await self.rules_dao.get_plan_rules_with_conditions(plan_id,
                                                                                         rule_details.service_slug)
        redis_rule_key = f"plan_rules:{rule_details.service_slug.value}:{plan_id}"
        await self.redis_client.add_key(redis_rule_key, json.dumps(rules_data_with_conditions))

    async def get_rules_with_conditions(self, plan_id, service_slug):
        """
        Updates the Redis cache for the rules associated with a given plan.

        :param plan_id: The ID of the plan.
        :param service_slug: slug of service.
        """

        redis_plan_rules_key = f"plan_rules:{service_slug}:{plan_id}"
        if await self.redis_client.exists_key(redis_plan_rules_key):
            rule_value = await self.redis_client.get_key(redis_plan_rules_key)
            return json.loads(rule_value)
        rules_data_with_conditions = await self.rules_dao.get_plan_rules_with_conditions(plan_id, service_slug.upper())
        await self.redis_client.add_key(redis_plan_rules_key, json.dumps(rules_data_with_conditions))
        return rules_data_with_conditions

    async def initialize_all_rules_in_redis(self):
        plan_rules = await self.rules_dao.get_all_rules()
        plan_rules_with_conditions = {}
        for plan_rule in plan_rules:
            if str(plan_rule.plan_id) not in plan_rules_with_conditions:
                plan_rules_with_conditions[str(plan_rule.plan_id)] = {}

            if plan_rule.rule.service_slug.value not in plan_rules_with_conditions[str(plan_rule.plan_id)]:
                plan_rules_with_conditions[str(plan_rule.plan_id)][plan_rule.rule.service_slug.value] = []

            plan_rules_with_conditions[str(plan_rule.plan_id)][plan_rule.rule.service_slug.value].append(
                {
                    "id": str(plan_rule.rule.id),
                    "name": plan_rule.rule.name,
                    "description": plan_rule.rule.description,
                    "scope": plan_rule.rule.scope.value,
                    "enabled": plan_rule.rule.enabled,
                    "meta_data": plan_rule.rule.meta_data,
                    "rule_slug": plan_rule.rule.rule_slug,
                    "rule_class_name": plan_rule.rule.rule_class_name,
                    "service_slug": plan_rule.rule.service_slug.value,
                    "conditions": plan_rule.rule.condition_data or {},
                }
            )

        for plan_id in plan_rules_with_conditions:
            for service_slug in plan_rules_with_conditions[plan_id]:
                redis_plan_rules_key = f"plan_rules:{service_slug}:{plan_id}"
                await self.redis_client.add_key(redis_plan_rules_key,
                                                json.dumps(plan_rules_with_conditions[plan_id][service_slug]))

    async def delete_plan_related_keys(self, user_id: str, org_id: Optional[str] = None):
        pattern = f"org:{org_id}:rule:*" if org_id else f"user:{user_id}:rule:*"
        rules_keys = await self.redis_client.get_keys(pattern)
        for key in rules_keys:
            await self.redis_client.delete_key(key)
