import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config.logging import logger
from app.router import api_router
from utils.custom_middleware import SecurityHeadersMiddleware
from utils.load_config import run_on_startup, run_on_exit
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from utils.constants import PROMETHEUS_LOG_TIME
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from opentelemetry.instrumentation import asgi


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_on_startup()
    yield
    await run_on_exit()


async def repeated_task_for_prometheus():
    while True:
        # await generate_prometheus_data()
        await asyncio.sleep(PROMETHEUS_LOG_TIME)


def get_app() -> FastAPI:
    class PatchedASGIGetter(asgi.ASGIGetter):
        def keys(self, carrier):
            print("keys")
            headers = carrier.get("headers") or []
            return [_key.decode("utf8") for (_key, _value) in headers]

    asgi.asgi_getter = PatchedASGIGetter()
    """
    Get FastAPI application.

    This is the main constructor of an application.

    :return: application.
    """

    payments_app = FastAPI(
        debug=True,
        title="payments",
        docs_url="/api_docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        root_path="/"
    )

    payments_app.add_middleware(
        CORSMiddleware,
        # allow_origins=["*"],  # Only allow this origins
        allow_origins=[],  # Only allow this origins
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )

    payments_app.include_router(api_router)
    payments_app.add_middleware(SessionMiddleware, secret_key="** Session Middleware **")
    # payments_app.add_middleware(SecurityHeadersMiddleware)    

    FastAPIInstrumentor.instrument_app(payments_app)
    return payments_app
