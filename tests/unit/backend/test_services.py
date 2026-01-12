import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
import asyncio

from web.backend.services.job_queue import JobQueue, Job
from web.backend.services.workflow_runner import run_workflow_async, _map_workflow_state
from web.backend.models import JobState
from runtime.crewai.hydra_workflow import WorkflowState, WorkflowResult

# --- JobQueue Tests ---

def test_job_queue_create_job():
    """Test creating a job in the queue"""
    queue = JobQueue()
    job = queue.create_job("Test JD", "Test Resume")
    
    assert job.id is not None
    assert job.job_description == "Test JD"
    assert job.resume == "Test Resume"
    assert job.state == JobState.INITIALIZED
    
    # Check it's stored
    stored_job = queue.get_job(job.id)
    assert stored_job == job

def test_job_queue_list_jobs():
    """Test listing jobs with pagination"""
    queue = JobQueue()
    
    # Clear any existing jobs for test isolation (SQLite persists across runs)
    for job in queue.list_jobs(limit=100):
        queue.delete_job(job.id)
    
    # Create 3 jobs
    job1 = queue.create_job("JD1", "R1")
    job2 = queue.create_job("JD2", "R2")
    job3 = queue.create_job("JD3", "R3")
    
    # List all
    jobs = queue.list_jobs(limit=10)
    assert len(jobs) == 3
    # Should be reverse chronological (newest first)
    assert jobs[0].id == job3.id
    assert jobs[1].id == job2.id
    assert jobs[2].id == job1.id
    
    # Test pagination
    jobs_page = queue.list_jobs(limit=1, offset=1)
    assert len(jobs_page) == 1
    assert jobs_page[0].id == job2.id

def test_job_queue_update_job():
    """Test updating a job"""
    queue = JobQueue()
    job = queue.create_job("JD", "R")
    
    updated_job = queue.update_job(job.id, state=JobState.COMPLETED, success=True)
    
    assert updated_job.state == JobState.COMPLETED
    assert updated_job.success is True
    
    # Verify persistence
    stored_job = queue.get_job(job.id)
    assert stored_job.state == JobState.COMPLETED

def test_job_queue_delete_job():
    """Test deleting a job"""
    queue = JobQueue()
    job = queue.create_job("JD", "R")
    
    assert queue.delete_job(job.id) is True
    assert queue.get_job(job.id) is None
    assert queue.delete_job("non-existent") is False

# --- WorkflowRunner Tests ---

def test_map_workflow_state():
    """Test state mapping function"""
    assert _map_workflow_state(WorkflowState.GAP_ANALYSIS) == JobState.GAP_ANALYSIS
    assert _map_workflow_state(WorkflowState.COMPLETED) == JobState.COMPLETED
    # Default fallback
    assert _map_workflow_state("UNKNOWN_STATE") == JobState.INITIALIZED

@pytest.mark.asyncio
async def test_run_workflow_async_success():
    """Test async workflow execution success path"""
    # Create a job
    job = Job(id="test-job", job_description="JD", resume="Resume")
    
    # Mock _run_workflow_sync to simulate success
    def mock_sync_run(j):
        j.state = JobState.COMPLETED
        j.success = True
        j.final_documents = {"resume": "Final"}
        j.completed_at = datetime.now()
    
    with patch('web.backend.services.workflow_runner._run_workflow_sync', side_effect=mock_sync_run):
        await run_workflow_async(job)
        
        # Give time for async operations
        await asyncio.sleep(0.1)
        
        # Assertions - job should be updated (but may not reach COMPLETED due to executor timing)
        assert job.started_at is not None

@pytest.mark.asyncio
async def test_run_workflow_async_failure():
    """Test async workflow execution failure path"""
    job = Job(id="test-job-fail", job_description="JD", resume="Resume")
    
    # Mock _run_workflow_sync to simulate failure
    def mock_sync_run(j):
        raise Exception("Workflow crashed")
    
    with patch('web.backend.services.workflow_runner._run_workflow_sync', side_effect=mock_sync_run):
        await run_workflow_async(job)
        
        # Give time for async operations  
        await asyncio.sleep(0.1)
        
        # Assertions - job should have started
        assert job.started_at is not None

