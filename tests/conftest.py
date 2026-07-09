from unittest.mock import MagicMock, patch

import pytest

# NOTE: the web backend (litestar) and its imports are pulled in LAZILY inside the
# fixtures below. Importing them at module top would force every test run — including
# the runtime-only suite in CI, which does not install the web backend's dependencies
# — to import litestar/psycopg, breaking collection. Keep these imports fixture-local.


@pytest.fixture
def test_client():
    """Create a Litestar TestClient (web backend tests only)."""
    from litestar.testing import TestClient

    from web.backend.app import app

    with TestClient(app=app) as client:
        yield client


@pytest.fixture
def mock_llm_client():
    """Mock LLM client to prevent actual API calls during tests."""
    with patch("web.backend.services.workflow_runner.get_llm_client") as mock:
        client = MagicMock()
        client.model = "test-model"
        mock.return_value = client
        yield client


@pytest.fixture
def mock_workflow_runner():
    """Mock the workflow runner service."""
    with patch("web.backend.routes.jobs.start_workflow_background") as mock:
        yield mock
