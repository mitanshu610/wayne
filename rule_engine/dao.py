import uuid6
from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from config.logging import logger
from rule_engine.exceptions import RuleError
from rule_engine.models import Rule, PlanRule


class RulesDAO:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_rules_by_plan_id(self, plan_id: str):
        """
        Fetch all rules associated with a specific plan ID.
        """
        try:
            query = (
                select(Rule)
                .join(PlanRule, PlanRule.rule_id == Rule.id)
                .where(PlanRule.plan_id == plan_id)
            )
            result = await self.session.execute(query)
            rules = result.scalars().all()
            logger.info("Retrieved %d rules for plan ID: %s", len(rules), str(plan_id))
            return rules
        except Exception as e:
            logger.error("Error occurred while getting rules by plan ID %s: %s", str(plan_id), str(e))
            raise RuleError(
                message="Failed to fetch rules for the specified plan ID.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

    async def get_rule_by_id(self, rule_id: str):
        """
        Fetch a rule by its ID.
        """
        try:
            query = select(Rule).where(Rule.id == rule_id, Rule.enabled == True)
            result = await self.session.execute(query)
            rule = result.scalar_one_or_none()
            if not rule:
                raise RuleError(message="Rule not found.", status_code=status.HTTP_404_NOT_FOUND)
            logger.info("Retrieved rule with ID: %s", str(rule_id))
            return rule
        except Exception as e:
            logger.error("Error occurred while getting rule by ID %s: %s", str(rule_id), str(e))
            raise RuleError(
                message="Failed to fetch the rule by ID.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

    async def create_rule(self, rule_data: dict):
        """
        Create a new rule with its conditions embedded in the condition_data field.
        """
        try:
            new_rule = Rule(
                id=uuid6.uuid6(),
                name=rule_data["name"],
                description=rule_data.get("description"),
                scope=rule_data["scope"],
                enabled=rule_data.get("enabled", True),
                meta_data=rule_data.get("meta_data", {}),
                rule_slug=rule_data["rule_slug"],
                rule_class_name=rule_data["rule_class_name"],
                service_slug=rule_data["service_slug"].replace("-", "_").upper(),
                condition_data=rule_data.get("conditions", {}),
            )
            self.session.add(new_rule)
            await self.session.commit()
            logger.info("Rule created successfully with ID: %s", str(new_rule.id))
            return new_rule
        except IntegrityError as e:
            await self.session.rollback()
            logger.error("Integrity error occurred while creating rule: %s", str(e))
            raise RuleError(
                message="Database integrity error while creating rule.",
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            await self.session.rollback()
            logger.error("Error occurred while creating rule: %s", str(e))
            raise RuleError(
                message="Failed to create a new rule.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

    async def add_rule_to_plan(self, plan_id: str, rule_id: str):
        """
        Add a rule to a plan by creating a PlanRule entry.
        """
        try:
            rule_query = select(Rule).where(Rule.id == rule_id)
            rule_result = await self.session.execute(rule_query)
            rule = rule_result.scalar_one_or_none()

            if not rule:
                raise RuleError(
                    message="Rule not found.",
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invalid Rule ID.",
                )

            new_plan_rule = PlanRule(plan_id=plan_id, rule_id=rule_id)
            self.session.add(new_plan_rule)
            await self.session.commit()
            logger.info("Rule %s added to plan %s", str(rule_id), str(plan_id))
            return new_plan_rule
        except IntegrityError as e:
            await self.session.rollback()
            logger.error("Integrity error while adding rule to plan: %s", str(e))
            raise RuleError(
                message="Similar mapping already exists.",
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to add rule to plan %s: %s", str(plan_id), str(e))
            raise RuleError(
                message="Failed to add rule to plan.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

    async def get_plan_rules_with_conditions(self, plan_id: str, service_slug: str):
        """
        Fetch all rules and their embedded conditions for a given plan.
        """
        try:
            result = (
                await self.session.execute(
                    select(Rule)
                    .join(PlanRule, PlanRule.rule_id == Rule.id)
                    .where(PlanRule.plan_id == plan_id, Rule.service_slug == service_slug)
                )
            )

            rules_with_conditions = []

            for rule in result.scalars().all():
                rules_with_conditions.append(
                    {
                        "id": str(rule.id),
                        "name": rule.name,
                        "description": rule.description,
                        "scope": rule.scope.value,
                        "enabled": rule.enabled,
                        "meta_data": rule.meta_data,
                        "rule_slug": rule.rule_slug,
                        "rule_class_name": rule.rule_class_name,
                        "service_slug": rule.service_slug.value,
                        "conditions": rule.condition_data or {},
                    }
                )

            logger.info("Retrieved %d rules with conditions for plan ID: %s", len(rules_with_conditions), str(plan_id))
            return rules_with_conditions
        except Exception as e:
            logger.error("Error occurred while fetching plan rules with conditions for plan ID %s: %s",
                         str(plan_id), str(e))
            raise RuleError(
                message="Failed to fetch rules and conditions for the plan.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

    async def remove_rule_from_plan(self, plan_id: str, rule_id: str):
        """
        Remove a rule from a plan by deleting the PlanRule entry.
        """
        try:
            stmt = select(PlanRule).where(PlanRule.plan_id == plan_id, PlanRule.rule_id == rule_id)
            result = await self.session.execute(stmt)
            plan_rule = result.scalars().first()

            if not plan_rule:
                raise RuleError(
                    message="Plan rule mapping not found.",
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invalid Rule ID or Plan ID.",
                )

            await self.session.delete(plan_rule)
            await self.session.commit()
            logger.info("Successfully removed rule ID %s from plan ID %s", str(rule_id), str(plan_id))
        except RuleError:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error("Error occurred while removing rule ID %s from plan ID %s: %s",
                         str(rule_id), str(plan_id), str(e))
            raise RuleError(
                message="Failed to remove rule from plan.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

    async def get_all_rules(self):
        try:
            query = select(PlanRule).options(joinedload(PlanRule.rule))
            result = await self.session.execute(query)
            return result.unique().scalars().all()
        except Exception as e:
            await self.session.rollback()
            logger.error("Error occurred while getting all rules")
            raise RuleError(
                message="Failed to get all rules.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )