import logging

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from config.settings import loaded_config


def configure_sentry():
    with open(f"{loaded_config.BASE_DIR}/gitsha", "r") as file:
        gitsha = file.readline()

    sentry_sdk.init(
        dsn='https://b2e64b82a45f353c3d080f46adf3ae2a@o71740.ingest.us.sentry.io/4508697042944000',
        traces_sample_rate=loaded_config.sentry_sample_rate,
        environment=loaded_config.sentry_environment,
        release=gitsha,
        integrations=[
            LoggingIntegration(
                level=logging.getLevelName(loaded_config.log_level.upper()),
                event_level=logging.ERROR,
            ),
            SqlalchemyIntegration(),
        ],
    )
