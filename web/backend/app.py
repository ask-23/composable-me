"""Litestar application for Hydra web API."""

import logging
import os
from pathlib import Path

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

from web.backend.routes.health import HealthController
from web.backend.routes.jobs import JobsController

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
