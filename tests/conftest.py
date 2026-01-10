import pytest
from unittest.mock import MagicMock, patch
from litestar.testing import TestClient
from web.backend.app import app

@pytest.fixture
def test_client():
    """Create a Litestar TestClient"""
    with TestClient(app=app) as client:
        yield client

@pytest.fixture
def mock_llm_client():
    """Mock LLM client to prevent actual API calls during tests"""
    with patch('web.backend.services.workflow_runner.get_llm_client') as mock:
        # Mock the LLM object returned
        client = MagicMock()
        client.model = "test-model"
        mock.return_value = client
        yield client

@pytest.fixture
def mock_workflow_runner():
    """Mock the workflow runner service"""
    with patch('web.backend.routes.jobs.start_workflow_background') as mock:
        yield mock
