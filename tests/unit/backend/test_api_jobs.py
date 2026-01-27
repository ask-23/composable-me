import pytest
from unittest.mock import patch, MagicMock
from web.backend.models import JobState
from web.backend.services.job_queue import job_queue

def test_create_job_success(test_client, mock_workflow_runner):
    """Test successful job creation"""
    payload = {
        "job_description": "Test Job Description",
        "resume": "Test Resume Content",
        "source_documents": "Test Source Docs"
    }
    
    response = test_client.post("/api/jobs", json=payload)
    
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"
    
    # Verify workflow runner was called
    mock_workflow_runner.assert_called_once()
    
def test_create_job_missing_fields(test_client):
    """Test job creation with missing required fields"""
    payload = {
        "job_description": "Test Job Description"
        # Missing resume and source_documents
    }
    
    response = test_client.post("/api/jobs", json=payload)
    
    assert response.status_code == 400

def test_get_job_not_found(test_client):
    """Test getting a non-existent job"""
    response = test_client.get("/api/jobs/non-existent-id")
    assert response.status_code == 404

def test_get_job_success(test_client, mock_workflow_runner):
    """Test getting an existing job"""
    # Create a job first
    payload = {
        "job_description": "Test Job Description",
        "resume": "Test Resume",
        "source_documents": "Test Sources"
    }
    create_response = test_client.post("/api/jobs", json=payload)
    job_id = create_response.json()["job_id"]
    
    # Get the job
    response = test_client.get(f"/api/jobs/{job_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert data["state"] == "initialized"

def test_approve_gap_analysis_allows_resume_from_review_state(test_client, mock_workflow_runner):
    payload = {
        "job_description": "Test Job Description (long enough)",
        "resume": "Test Resume Content (long enough)",
        "source_documents": "",
    }
    create_response = test_client.post("/api/jobs", json=payload)
    job_id = create_response.json()["job_id"]
    assert mock_workflow_runner.call_count == 1

    # Move job to the pause state
    job_queue.update_job(job_id, state=JobState.GAP_ANALYSIS_REVIEW)

    response = test_client.post(
        f"/api/jobs/{job_id}/approve_gap_analysis",
        json={"approved": True},
    )
    assert response.status_code == 200
    assert mock_workflow_runner.call_count == 2

def test_approve_gap_analysis_is_idempotent_after_review_state(test_client, mock_workflow_runner):
    payload = {
        "job_description": "Test Job Description (long enough)",
        "resume": "Test Resume Content (long enough)",
        "source_documents": "",
    }
    create_response = test_client.post("/api/jobs", json=payload)
    job_id = create_response.json()["job_id"]
    assert mock_workflow_runner.call_count == 1

    # Simulate job already advanced beyond the review state
    job_queue.update_job(job_id, state=JobState.INTERROGATION)

    response = test_client.post(
        f"/api/jobs/{job_id}/approve_gap_analysis",
        json={"approved": True},
    )
    assert response.status_code == 200
    assert mock_workflow_runner.call_count == 1

def test_submit_interview_answers_allows_resume_from_review_state(test_client, mock_workflow_runner):
    payload = {
        "job_description": "Test Job Description (long enough)",
        "resume": "Test Resume Content (long enough)",
        "source_documents": "",
    }
    create_response = test_client.post("/api/jobs", json=payload)
    job_id = create_response.json()["job_id"]
    assert mock_workflow_runner.call_count == 1

    job_queue.update_job(job_id, state=JobState.INTERROGATION_REVIEW)

    response = test_client.post(
        f"/api/jobs/{job_id}/submit_interview_answers",
        json={"answers": [{"question": "Q1", "answer": "A1"}]},
    )
    assert response.status_code == 200
    assert mock_workflow_runner.call_count == 2

def test_submit_interview_answers_is_idempotent_after_review_state(test_client, mock_workflow_runner):
    payload = {
        "job_description": "Test Job Description (long enough)",
        "resume": "Test Resume Content (long enough)",
        "source_documents": "",
    }
    create_response = test_client.post("/api/jobs", json=payload)
    job_id = create_response.json()["job_id"]
    assert mock_workflow_runner.call_count == 1

    job_queue.update_job(job_id, state=JobState.DIFFERENTIATION)

    response = test_client.post(
        f"/api/jobs/{job_id}/submit_interview_answers",
        json={"answers": [{"question": "Q1", "answer": "A1"}]},
    )
    assert response.status_code == 200
    assert mock_workflow_runner.call_count == 1

@pytest.mark.asyncio
async def test_job_stream_exists(test_client):
    """Test that the stream endpoint is reachable"""
    # Note: Testing SSE with TestClient is complex, basic check for 404 on non-existent
    response = test_client.get("/api/jobs/fake-id/stream")
    # Should be 404 because job doesn't exist (or 200 if we mock it right, but start simple)
    # The controller checks for job existence first
    assert response.status_code == 404
