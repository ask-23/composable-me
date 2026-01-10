"""Health check endpoint."""

from litestar import Controller, get
from litestar.status_codes import HTTP_200_OK


class HealthController(Controller):
    """Health check controller."""

    path = "/health"

    @get("/", status_code=HTTP_200_OK)
    async def health_check(self) -> dict:
        """Return health status."""
        return {
            "status": "healthy",
            "service": "hydra-api",
            "version": "1.0.0",
        }
