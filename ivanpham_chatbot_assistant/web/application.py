import logging

import sentry_sdk
from fastapi import FastAPI
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from ivanpham_chatbot_assistant.log import configure_logging
from ivanpham_chatbot_assistant.settings import settings
from ivanpham_chatbot_assistant.web.api.router import api_router
from ivanpham_chatbot_assistant.web.lifespan import lifespan_setup

from ivanpham_chatbot_assistant.web.middleware.request_id_middleware import RequestIDMiddleware
from ivanpham_chatbot_assistant.web.middleware.logging_middleware import APILoggingMiddleware
from ivanpham_chatbot_assistant.web.middleware.rate_limit_middleware import setup_rate_limiter
from ivanpham_chatbot_assistant.web.exceptions.global_exception_handler import setup_global_exception_handlers
from ivanpham_chatbot_assistant.web.metrics.prometheus_metrics import PrometheusMiddleware, metrics_router

def get_app() -> FastAPI:
    """
    Get FastAPI application.

    This is the main constructor of an application.

    :return: application.
    """
    configure_logging()
    if settings.sentry_dsn:
        # Enables sentry integration.
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            traces_sample_rate=settings.sentry_sample_rate,
            environment=settings.environment,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                LoggingIntegration(
                    level=logging.getLevelName(
                        settings.log_level.value,
                    ),
                    event_level=logging.ERROR,
                ),
                SqlalchemyIntegration(),
            ],
        )
    app = FastAPI(
        title="ivanpham_chatbot_assistant",
        lifespan=lifespan_setup,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Setup global exception handlers
    setup_global_exception_handlers(app)
    
    # Setup Rate Limiting
    setup_rate_limiter(app)

    # Register Middlewares (Order is important, last added is executed first locally)
    app.add_middleware(APILoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(PrometheusMiddleware)

    # Mount metrics endpoint
    app.include_router(router=metrics_router)

    # Main router for the API.
    app.include_router(router=api_router, prefix="/api/v1")

    return app
