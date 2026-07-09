"""Litestar application for Hydra web API."""

import logging
import os
from pathlib import Path
from typing import Callable

# Load environment variables from .env file BEFORE any other imports
# This ensures API keys are available when workflow_runner imports llm_client
from dotenv import load_dotenv

# Find .env/a.env files in project root (parent of web/backend)
project_root = Path(__file__).parent.parent.parent
env_files = [project_root / "a.env", project_root / ".env"]
loaded_env_files = []
for env_file in env_files:
    if env_file.exists():
        load_dotenv(env_file)
        loaded_env_files.append(str(env_file))
if loaded_env_files:
    logging.info(f"Loaded environment from {', '.join(loaded_env_files)}")
else:
    logging.warning(f"No .env or a.env file found at {project_root}")

from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.logging import LoggingConfig
from litestar.middleware.base import DefineMiddleware, MiddlewareProtocol
from litestar.types import ASGIApp, Receive, Scope, Send

from web.backend.routes.health import HealthController
from web.backend.routes.jobs import JobsController
from web.backend.telemetry import init_telemetry, shutdown_telemetry, get_tracer, create_span
from web.backend.observability.sentry import setup_sentry
from web.backend.db import apply_migrations

# Configure logging
logging_config = LoggingConfig(
    root={"level": "INFO", "handlers": ["console"]},
    formatters={
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    log_exceptions="always",
)


class TelemetryMiddleware(MiddlewareProtocol):
    """ASGI middleware for OpenTelemetry tracing of HTTP requests."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        tracer = get_tracer()
        if tracer is None:
            await self.app(scope, receive, send)
            return

        # Extract request information
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")

        # Create span for the request
        with tracer.start_as_current_span(
            f"{method} {path}",
            attributes={
                "http.method": method,
                "http.url": path,
                "http.scheme": scope.get("scheme", "http"),
                "http.host": dict(scope.get("headers", [])).get(b"host", b"").decode(),
            }
        ) as span:
            # Track response status
            status_code = 500  # Default to error

            async def send_wrapper(message):
                nonlocal status_code
                if message["type"] == "http.response.start":
                    status_code = message.get("status", 500)
                    span.set_attribute("http.status_code", status_code)
                await send(message)

            try:
                await self.app(scope, receive, send_wrapper)
            except Exception as e:
                span.record_exception(e)
                span.set_attribute("http.status_code", 500)
                raise


async def on_startup() -> None:
    """Initialize telemetry, Sentry, and database on application startup."""
    init_telemetry()
    setup_sentry()
    # Apply database migrations
    try:
        apply_migrations()
    except Exception as exc:
        logging.error("Database migrations failed: %s", exc)


async def on_shutdown() -> None:
    """Shutdown telemetry on application shutdown."""
    shutdown_telemetry()

# Configure CORS for local development
cors_config = CORSConfig(
    allow_origins=["http://localhost:4321", "http://localhost:3000", "http://127.0.0.1:4321"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Create Litestar app
app = Litestar(
    route_handlers=[HealthController, JobsController],
    cors_config=cors_config,
    logging_config=logging_config,
    middleware=[TelemetryMiddleware],
    on_startup=[on_startup],
    on_shutdown=[on_shutdown],
    debug=True,
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "web.backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
