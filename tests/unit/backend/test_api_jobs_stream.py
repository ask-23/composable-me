
import pytest
from unittest.mock import MagicMock, patch
from web.backend.models import JobState
def test_stream_job_success(test_client):
    """Test streaming job events"""
    # Create mock job with async event generator
    mock_job = MagicMock() 
    mock_job.id = "stream-test-id"
    mock_job.state = JobState.INITIALIZED
    mock_job.get_progress_percent.return_value = 0
    mock_job.success = False
    mock_job.final_documents = {}
    mock_job.audit_report = {}
    mock_job.audit_failed = False
    
    # Setup mock event generator
    async def mock_get_event(timeout):
        return {"event": "progress", "data": {"state": "running"}}

    mock_job.get_event = mock_get_event # This needs to be awaitable or return awaitable? 
    # In controller: event = await job.get_event(timeout=30.0)
    # The mock function above is async, so calling it returns coroutine. Correct.

    # But we need to break the loop. The loop breaks on "complete" or "error".
    # So we need side_effect to return progress then complete.
    
    events = [
        {"event": "progress", "data": {"state": "running"}},
        {"event": "complete", "data": {"result": "done"}}
    ]
    
    async def side_effect(timeout):
        if events:
            return events.pop(0)
        return None # keepalive

    mock_job.get_event = MagicMock(side_effect=side_effect)

    with patch('web.backend.services.job_queue.JobQueue.get_job', return_value=mock_job):
        response = test_client.get("/api/jobs/stream-test-id/stream")
        assert response.status_code == 200
        content = response.text
        assert "event: progress" in content
        assert "event: complete" in content
