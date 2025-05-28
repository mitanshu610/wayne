import enum
import os
from typing import Optional, ClassVar

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from clerk_integration.utils import ClerkAuthHelper
from pydantic_settings import BaseSettings

from config.config_parser import docker_args
from utils.connection_manager import ConnectionManager
from utils.sqlalchemy import async_db_url

args = docker_args


class LogLevel(enum.Enum):  # noqa: WPS600
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class Settings(BaseSettings):
    CONSUMER_TYPE: str = args.consumer_type
    env: str = args.env
    port: int = args.port
    host: str = args.host
    debug: bool = args.debug
    workers_count: int = 1
    mode: str = args.mode
    postgres_fynix_wayne_read_write: str = args.postgres_fynix_wayne_read_write
    db_url: str = async_db_url(args.postgres_fynix_wayne_read_write)
    db_echo: bool = args.debug
    server_type: str = args.server_type
    realm: str = args.realm
    log_level: str = LogLevel.INFO.value
    connection_manager: Optional[ConnectionManager] = None

    BASE_DIR: ClassVar[str] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sentry_sample_rate: float = 1.0
    sentry_environment: str = args.sentry_environment
    redis_payments_url: str = os.getenv("REDIS_FEX_HIRUZEN_READ_WRITE", args.redis_payments_url)
    trial_expiration_time: int = args.pro_trial_expiration_time_seconds
    razorpay_api_base_url: str = args.razorpay_api_base_url
    razorpay_api_key: str = args.razorpay_api_key
    razorpay_api_secret: str = args.razorpay_api_secret

    paddle_api_base_url: str = args.paddle_api_base_url
    paddle_api_secret: str = args.paddle_api_secret
    paddle_client_token: str = args.paddle_client_token

    sentry_dsn: Optional[str] = args.sentry_dsn

    POD_NAMESPACE: str = args.K8S_POD_NAMESPACE
    NODE_NAME: str = args.K8S_NODE_NAME
    POD_NAME: str = args.K8S_POD_NAME
    aps_scheduler: Optional[AsyncIOScheduler] = None

    clerk_secret_key: str = args.clerk_secret_key
    clerk_auth_helper: ClerkAuthHelper = ClerkAuthHelper("Wayne", clerk_secret_key=clerk_secret_key)
    fallback_plan_id: str = args.fallback_plan_id
    subscription_cancellation_at: str = args.subscription_cancellation_at


loaded_config = Settings()
