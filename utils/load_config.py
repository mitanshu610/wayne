import base64

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import loaded_config
from crons.downgrade_plan_cron import downgrade_users_to_basic
from rule_engine.services import RulesService
from utils.connection_handler import get_connection_handler_for_app, ConnectionHandler
from utils.connection_manager import ConnectionManager


async def run_on_startup():
    try:
        await init_connections()
        await init_scheduler()
        await init_data()
    except Exception as e:
        print(e)


async def run_on_exit():
    await loaded_config.connection_manager.close_connections()


async def init_connections():
    connection_manager = ConnectionManager(
        db_url=loaded_config.db_url,
        db_echo=loaded_config.db_echo
    )
    loaded_config.connection_manager = connection_manager
    loaded_config.razorpay_api_secret = base64.b64encode(
        f"{loaded_config.razorpay_api_key}:{loaded_config.razorpay_api_secret}".encode()).decode()


async def init_scheduler():
    loaded_config.aps_scheduler = AsyncIOScheduler()
    if loaded_config.server_type == 'downgrade_plan_scheduler':
        loaded_config.aps_scheduler.add_job(downgrade_users_to_basic, IntervalTrigger(seconds=15))
        loaded_config.aps_scheduler.start()


async def init_data():
    connection_handler = ConnectionHandler(
        connection_manager=loaded_config.connection_manager
    )
    rule_service = RulesService(connection_handler=connection_handler)
    await rule_service.initialize_all_rules_in_redis()
