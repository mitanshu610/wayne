import time

import uuid6
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import class_mapper, aliased

from config.logging import logger
from config.settings import loaded_config
from payments.exceptions import SubscriptionNotFoundError
from payments.models import BillingCycle, PSPName, Subscriptions, Customer, ScheduledDowngrade
from payments.schemas import CreateSubscription, PlanSlugs
from plans.dao import PlansDAO
from prometheus.metrics import DB_QUERY_LATENCY
from utils.common import UserData
from utils.decorators import latency


class PaymentsDAO:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.plan_dao = PlansDAO(self.session)

    @latency(metric=DB_QUERY_LATENCY)
    async def save_subscription(self, subscription_details: CreateSubscription, plan, start_date,
                                razorpay_subscription_details, user_data: UserData, is_trial=False):
        """
        Record a new subscription in the Subscriptions table.

        :param subscription_details: Data from the CreateOrderSchema.
        :param plan: Plan details from the database.
        :param start_date: Start date of the subscription.
        :param razorpay_subscription_details: Razorpay subscription details.
        :param user_data: User-related data containing user_id and org_id.
        """
        try:
            billing_cycle = BillingCycle(plan.billing_cycle.lower())
            psp_name = PSPName(subscription_details.psp_name.capitalize())

            if razorpay_subscription_details["status"] == "trial":
                amount = "0"
            else:
                amount = plan.amount

            subscription = Subscriptions(
                id=uuid6.uuid6(),
                user_id=user_data.userId,
                org_id=user_data.orgId,
                plan_id=subscription_details.plan_id,
                start_date=start_date,
                is_active=subscription_details.is_active,
                end_date=None,
                billing_cycle=billing_cycle,
                amount=amount,
                currency=plan.currency,
                psp_name=psp_name,
                psp_subscription_id=razorpay_subscription_details["id"],
                status=razorpay_subscription_details["status"],
                is_trial=is_trial
            )

            self.session.add(subscription)
            await self.session.commit()
            subscription_dict = {col.key: getattr(subscription, col.key) for col in class_mapper(Subscriptions).columns}
            keys_to_remove = ["user_id", "org_id", "amount", "currency"]
            filtered_subscription = {key: value for key, value in subscription_dict.items() if
                                     key not in keys_to_remove}
            # filtered_subscription["rzp_key"] = loaded_config.razorpay_api_key
            return filtered_subscription
        except Exception as e:
            logger.error("Error while adding subscription to database %s", str(e))
            raise e

    @latency(metric=DB_QUERY_LATENCY)
    async def save_paddle_subscription(self, subscription_details: CreateSubscription, plan, start_date,
                                       razorpay_subscription_details, user_data: UserData, is_trial=False):
        """
        Record a new subscription in the Subscriptions table.

        :param subscription_details: Data from the CreateOrderSchema.
        :param plan: Plan details from the database.
        :param start_date: Start date of the subscription.
        :param razorpay_subscription_details: Razorpay subscription details.
        :param user_data: User-related data containing user_id and org_id.
        """
        try:
            billing_cycle = BillingCycle(plan.billing_cycle.lower())
            psp_name = PSPName(subscription_details.psp_name.capitalize())

            if razorpay_subscription_details["status"] == "trial":
                amount = "0"
            else:
                amount = plan.amount

            subscription = Subscriptions(
                id=uuid6.uuid6(),
                user_id=user_data.userId,
                org_id=user_data.orgId,
                plan_id=subscription_details.plan_id,
                start_date=start_date,
                is_active=subscription_details.is_active,
                end_date=None,
                billing_cycle=billing_cycle,
                amount=amount,
                currency=plan.currency,
                psp_name=psp_name,
                psp_subscription_id=razorpay_subscription_details["id"],
                status=razorpay_subscription_details["status"],
                is_trial=is_trial
            )

            self.session.add(subscription)
            await self.session.commit()
            subscription_dict = {col.key: getattr(subscription, col.key) for col in class_mapper(Subscriptions).columns}
            keys_to_remove = ["user_id", "org_id", "amount", "currency"]
            filtered_subscription = {key: value for key, value in subscription_dict.items() if
                                     key not in keys_to_remove}
            filtered_subscription["rzp_key"] = loaded_config.razorpay_api_key
            return filtered_subscription
        except Exception as e:
            logger.error("Error while adding subscription to database %s", str(e))
            raise e

    @latency(metric=DB_QUERY_LATENCY)
    async def get_subscription_by_id(self, subscription_id: str):
        """
        Fetch a subscription from the database using its ID.

        :param subscription_id: The subscription ID to query.
        :return: The subscription if found, or None.
        """
        try:
            result = await self.session.execute(
                select(Subscriptions).filter(Subscriptions.id == subscription_id)
            )
            return result.scalars().first()
        except Exception as e:
            logger.error("Database error while fetching subscription by ID: %s", str(e))
            raise e

    @latency(metric=DB_QUERY_LATENCY)
    async def get_subscription_by_razorpay_id(self, razorpay_sub_id: str):
        """
        Fetch a subscription from the database using its ID.

        :param razorpay_sub_id: The subscription ID to query.
        :return: The subscription if found, or None.
        """
        try:
            result = await self.session.execute(
                select(Subscriptions).filter(Subscriptions.psp_subscription_id == razorpay_sub_id)
            )
            return result.scalars().first()
        except Exception as e:
            logger.error("Database error while fetching subscription by ID: %s", str(e))
            raise e

    @latency(metric=DB_QUERY_LATENCY)
    async def get_subscription_by_psp_subscription_id(self, psp_subscription_id: str):
        """
        Fetch a subscription from the database using its ID.

        :param psp_subscription_id: The subscription ID to query.
        :return: The subscription if found, or None.
        """
        try:
            result = await self.session.execute(
                select(Subscriptions).filter(Subscriptions.psp_subscription_id == psp_subscription_id)
            )
            return result.scalars().first()
        except Exception as e:
            logger.error("Database error while fetching subscription by ID: %s", str(e))
            raise e

    @latency(metric=DB_QUERY_LATENCY)
    async def get_subscriptions_by_user_and_org_id(self, user_id: int, org_id: int):
        """
        Fetch all subscriptions associated with a specific user and organization.

        :param user_id: The user ID to query.
        :param org_id: The organization ID to query.
        :return: List of subscriptions for the given user and organization.
        """
        try:
            result = await self.session.execute(
                select(Subscriptions).filter(Subscriptions.user_id == user_id, Subscriptions.org_id == org_id,
                                             Subscriptions.is_active == True)
            )
            return result.scalars().first()
        except Exception as e:
            logger.error("Database error while fetching user and org id: %s", str(e))
            raise e

    @latency(metric=DB_QUERY_LATENCY)
    async def delete_subscription_by_id(self, subscription_id: str):
        """
        Delete a subscription from the database using its ID.

        :param subscription_id: The subscription ID to delete.
        """
        result = await self.session.execute(
            select(Subscriptions).filter(Subscriptions.id == subscription_id)
        )
        subscription = result.scalars().first()
        if not subscription:
            raise SubscriptionNotFoundError()

        await self.session.delete(subscription)
        await self.session.commit()

    @latency(metric=DB_QUERY_LATENCY)
    async def update_subscription(self, subscription: Subscriptions):
        """
        Update an existing subscription in the database.

        :param subscription: The updated subscription object.
        """
        try:
            self.session.add(subscription)
            await self.session.commit()
        except Exception as e:
            logger.error("Database error while updating subscription: %s", str(e))
            raise e

    @latency(metric=DB_QUERY_LATENCY)
    async def get_customer_by_user_and_org_id(self, user_id: int, org_id: int):
        """
        Fetch a customer from the database using the user ID and organization ID.

        :param user_id: The user ID to query.
        :param org_id: The organization ID to query.
        :return: Customer object if found.
        """
        try:
            result = await self.session.execute(
                select(Customer).filter(Customer.user_id == user_id, Customer.org_id == org_id)
            )
            customer = result.scalars().first()
            return customer
        except Exception as e:
            logger.error("Database error while fetching customer by user and org: %s", str(e))
            raise e

    @latency(metric=DB_QUERY_LATENCY)
    async def create_customer(self, user_data: UserData, razorpay_customer, psp_name):
        try:
            customer = Customer(
                id=uuid6.uuid6(),
                customer_id=razorpay_customer["id"],
                psp_name=PSPName(psp_name.capitalize()),
                user_id=user_data.userId,
                org_id=user_data.orgId
            )
            self.session.add(customer)
            await self.session.commit()
            return customer
        except Exception as e:
            logger.error("Database error while fetching customer by user and org: %s", str(e))
            raise e

    async def get_current_user_basic_subscription(self, user_id, org_id):
        try:
            basic_plan = await self.plan_dao.get_plan_by_slug(PlanSlugs.BASIC.value)
            result = await self.session.execute(select(Subscriptions).filter(
                Subscriptions.org_id == org_id,
                Subscriptions.user_id == user_id,
                Subscriptions.is_active == True,
                Subscriptions.plan_id == str(basic_plan.id)
            ))
            return result.scalars().first()
        except Exception as e:
            logger.error("Database error while fetching customer by user and org: %s", str(e))
            raise e

    @latency(metric=DB_QUERY_LATENCY)
    async def has_user_taken_trial(self, user_id: int, org_id: int):
        """
        Checks if the user has already availed the 14-day trial.

        :param user_id: The user ID.
        :param org_id: The organization ID.
        :return: True if the user has already taken a trial, False otherwise.
        """
        try:
            result = await self.session.execute(
                select(Subscriptions)
                .filter(
                    Subscriptions.user_id == user_id,
                    Subscriptions.org_id == org_id,
                    Subscriptions.is_trial == True
                )
                .limit(1)
            )
            return result.scalars().first()
        except Exception as e:
            logger.error("Database error while checking trial status: %s", str(e))
            raise e

    @latency(metric=DB_QUERY_LATENCY)
    async def schedule_downgrade_to_basic(self, user_id: int, org_id: int, trial_end_date: int):
        """Schedules a downgrade to the Basic Plan after the trial period ends."""
        try:
            downgrade_entry = ScheduledDowngrade(
                id=uuid6.uuid6(),
                user_id=user_id,
                org_id=org_id,
                scheduled_at=trial_end_date,
                status="pending"
            )
            self.session.add(downgrade_entry)
            await self.session.commit()
        except Exception as e:
            logger.error("Database error while scheduling the entry for downgrade: %s", str(e))
            raise e

    @latency(metric=DB_QUERY_LATENCY)
    async def mark_scheduled_downgrade_completed(self, user_id: int, org_id: int):
        """
        Marks the scheduled downgrade as completed after execution.
        :param user_id: The user ID.
        :param org_id: The organization ID.
        """
        try:
            query = select(ScheduledDowngrade).where(
                ScheduledDowngrade.user_id == user_id,
                ScheduledDowngrade.org_id == org_id,
                ScheduledDowngrade.status == "pending"
            )

            result = await self.session.execute(query)
            scheduled_downgrade = result.scalar_one_or_none()

            if scheduled_downgrade:
                scheduled_downgrade.status = "completed"
                await self.session.commit()
                logger.info(f"Marked downgrade for user {user_id} in org {org_id} as completed.")
            else:
                logger.warning(f"No pending downgrade found for user {user_id} in org {org_id}.")
        except Exception as e:
            logger.error(f"Failed to Mark downgrade for user {user_id} in org {org_id} as completed: %s", str(e))
            raise e

    @latency(metric=DB_QUERY_LATENCY)
    async def get_expired_trials(self):
        """
        Fetch all trial subscriptions that have expired and are pending downgrade.
        """
        try:
            now = int(time.time())

            sub_alias = aliased(Subscriptions)
            downgrade_alias = aliased(ScheduledDowngrade)

            query = (
                select(sub_alias)
                .select_from(sub_alias)
                .join(
                    downgrade_alias,
                    (sub_alias.user_id == downgrade_alias.user_id) &
                    (sub_alias.org_id == downgrade_alias.org_id)
                )
                .where(
                    sub_alias.is_trial == True,
                    sub_alias.is_active == True,
                    downgrade_alias.scheduled_at <= now,
                    downgrade_alias.status == "pending"
                )
            )

            result = await self.session.execute(query)
            expired_trials = result.scalars().all()

            return expired_trials

        except Exception as e:
            logger.error(f"Failed to fetch expiring trial-based subscriptions: {str(e)}")
            raise e
