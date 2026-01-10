from unittest.mock import MagicMock, patch
from web.backend.services.job_queue import Job
from web.backend.models import JobState
from runtime.crewai.hydra_workflow import WorkflowState, WorkflowResult
from web.backend.services.workflow_runner import _run_workflow_sync

def test_run_workflow_sync_success():
    """Test the synchronous workflow execution logic"""
    # Create job
    job = Job(id="sync-test", job_description="JD", resume="Res")
    
    # Mock mocks
    mock_llm = MagicMock()
    mock_workflow_instance = MagicMock()
    mock_result = WorkflowResult(
        state=WorkflowState.COMPLETED,
        success=True,
        final_documents={"doc": "content"},
        audit_report={"status": "ok"},
        intermediate_results={"stage": "data"},
        execution_log=["log1"]
    )
    mock_workflow_instance.execute.return_value = mock_result
    
    with patch('web.backend.services.workflow_runner.get_llm_client', return_value=mock_llm), \
         patch('web.backend.services.workflow_runner.HydraWorkflow', return_value=mock_workflow_instance):
         
        _run_workflow_sync(job)
        
        # Verify job update
        assert job.success is True
        assert job.state == JobState.COMPLETED
        assert job.final_documents == {"doc": "content"}
        assert job.execution_log == ["log1"]

def test_run_workflow_sync_failure():
    """Test sync workflow failure handling"""
    job = Job(id="sync-fail", job_description="JD", resume="Res")
    
    with patch('web.backend.services.workflow_runner.get_llm_client') as mock_get_llm:
        mock_get_llm.side_effect = Exception("Setup failed")
        
        _run_workflow_sync(job)
        
        assert job.success is False
        assert job.state == JobState.FAILED
        assert "Setup failed" in job.error_message
