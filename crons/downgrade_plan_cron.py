from config.settings import loaded_config
from payments.dao import PaymentsDAO
from payments.schemas import PlanSlugs
from plans.dao import PlansDAO
from rule_engine.services import RulesService
from utils.connection_handler import ConnectionHandler
from config.logging import get_call_stack, logger



async def downgrade_users_to_basic():
    """Fetch all users whose trial period has expired and downgrade them to the Basic Plan."""
    connection_handler = ConnectionHandler(connection_manager=loaded_config.connection_manager)
    payments_dao = PaymentsDAO(session=connection_handler.session)
    plans_dao = PlansDAO(session=connection_handler.session)
    rules_dao = RulesService(connection_handler)

    try:
        expired_trials = await payments_dao.get_expired_trials()
        print(expired_trials)
        if not expired_trials:
            logger.info("No expired trials found.")
            return

        basic_plan = await plans_dao.get_plan_by_slug(PlanSlugs.BASIC.value)
        if not basic_plan:
            logger.error("Basic plan not found, cannot proceed with downgrade.")
            return

        for trial in expired_trials:
            try:
                logger.info("Downgrading user %s in org %s to Basic Plan.", trial.user_id, trial.org_id)
                trial.plan_id = basic_plan.id
                trial.status = "active"
                await payments_dao.update_subscription(trial)
                await payments_dao.mark_scheduled_downgrade_completed(trial.user_id, trial.org_id)
                logger.info("Successfully downgraded user %s to Basic Plan.", str(trial.user_id))
                await rules_dao.delete_plan_related_keys(user_id=trial.user_id, org_id=trial.org_id)
            except Exception as e:
                logger.error("Error while downgrading user %s: %s", trial.user_id, str(e))

    except Exception as e:
        await connection_handler.session.rollback()
        logger.error("An error occurred while downgrading users: %s", str(e))
        raise e
    finally:
        await connection_handler.session.close()