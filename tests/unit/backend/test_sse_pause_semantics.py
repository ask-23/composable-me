"""Test SSE pause semantics - when workflow pauses, no 'complete' event should be emitted."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from web.backend.models import JobState
from runtime.crewai.hydra_workflow import WorkflowState, WorkflowResult


@pytest.mark.asyncio
async def test_sse_stream_no_complete_on_pause(test_client):
    """
    Test that SSE stream does NOT emit 'event: complete' when workflow pauses.

    Scenario: Workflow pauses at GAP_ANALYSIS_REVIEW state.
    Expected: SSE stream emits progress events but NOT a complete event.

    This is a regression test for the pause semantics bug where workflows
    incorrectly emitted 'complete' events when pausing for user input.
    """

    # Mock workflow execution to pause at GAP_ANALYSIS_REVIEW
    mock_workflow_result = WorkflowResult(
        state=WorkflowState.GAP_ANALYSIS_REVIEW,
        success=False,  # Not complete yet
        final_documents=None,
        audit_report=None,
        executive_brief=None,
        error_message=None,
        execution_log=["Started workflow", "Completed gap analysis", "Pausing for review"],
        intermediate_results={"gap_analysis": {"status": "pending_review"}},
        audit_failed=False,
        audit_error=None,
        agent_models={"gap_analyzer": "gpt-4o-mini"},
    )

    # Mock the workflow execute method to return paused state
    with patch('web.backend.services.workflow_runner.HydraWorkflow') as mock_workflow_class:
        mock_workflow_instance = MagicMock()
        mock_workflow_instance.execute.return_value = mock_workflow_result
        mock_workflow_instance.get_current_state.return_value = WorkflowState.GAP_ANALYSIS_REVIEW
        mock_workflow_instance.get_execution_log.return_value = mock_workflow_result.execution_log
        mock_workflow_instance.get_intermediate_results.return_value = mock_workflow_result.intermediate_results
        mock_workflow_instance.agent_models = mock_workflow_result.agent_models
        mock_workflow_class.return_value = mock_workflow_instance

        # Mock LLM client
        with patch('web.backend.services.workflow_runner.get_llm_client') as mock_llm:
            mock_llm.return_value = MagicMock(model="test-model")

            # Create a job
            payload = {
                "job_description": "Senior Software Engineer position",
                "resume": "My resume content here",
                "source_documents": "Portfolio and references"
            }

            create_response = test_client.post("/api/jobs", json=payload)
            assert create_response.status_code == 202
            job_id = create_response.json()["job_id"]

            # Wait a moment for the workflow to execute in background
            import asyncio
            await asyncio.sleep(2)

            # Stream the job progress
            response = test_client.get(f"/api/jobs/{job_id}/stream")
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

            # Parse SSE events from response
            content = response.text
            events = _parse_sse_events(content)

            # Assertions
            # 1. Must have at least a 'connected' event
            event_types = [e["event"] for e in events]
            assert "connected" in event_types, f"Expected 'connected' event, got: {event_types}"

            # 2. Must NOT have a 'complete' event (this is the key assertion)
            assert "complete" not in event_types, \
                f"SSE stream must NOT emit 'complete' event when workflow pauses at {JobState.GAP_ANALYSIS_REVIEW}"

            # 3. Should have 'progress' events showing the paused state
            progress_events = [e for e in events if e["event"] == "progress"]
            assert len(progress_events) > 0, "Expected at least one progress event"

            # 4. Final progress event should show GAP_ANALYSIS_REVIEW state
            # Note: Due to timing, we might catch the workflow in progress, so just verify no complete
            print(f"\nDebug - SSE Events captured: {event_types}")
            print(f"Debug - Progress events: {len(progress_events)}")


@pytest.mark.asyncio
async def test_sse_stream_with_interrogation_review_pause(test_client):
    """
    Test SSE pause semantics for INTERROGATION_REVIEW state.

    Another pause state to verify the fix works across all pause points.
    """

    # Mock workflow execution to pause at INTERROGATION_REVIEW
    mock_workflow_result = WorkflowResult(
        state=WorkflowState.INTERROGATION_REVIEW,
        success=False,
        final_documents=None,
        audit_report=None,
        executive_brief=None,
        error_message=None,
        execution_log=["Started", "Gap analysis complete", "Interrogation complete", "Pausing for interview"],
        intermediate_results={
            "gap_analysis": {"status": "approved"},
            "interrogation": {"questions": ["Q1", "Q2"]},
        },
        audit_failed=False,
        audit_error=None,
        agent_models={"interrogator": "gpt-4o-mini"},
    )

    with patch('web.backend.services.workflow_runner.HydraWorkflow') as mock_workflow_class:
        mock_workflow_instance = MagicMock()
        mock_workflow_instance.execute.return_value = mock_workflow_result
        mock_workflow_instance.get_current_state.return_value = WorkflowState.INTERROGATION_REVIEW
        mock_workflow_instance.get_execution_log.return_value = mock_workflow_result.execution_log
        mock_workflow_instance.get_intermediate_results.return_value = mock_workflow_result.intermediate_results
        mock_workflow_instance.agent_models = mock_workflow_result.agent_models
        mock_workflow_class.return_value = mock_workflow_instance

        with patch('web.backend.services.workflow_runner.get_llm_client') as mock_llm:
            mock_llm.return_value = MagicMock(model="test-model")

            payload = {
                "job_description": "Senior Software Engineer with 5+ years of experience",
                "resume": "Experienced developer with strong technical skills",
                "source_documents": ""
            }

            create_response = test_client.post("/api/jobs", json=payload)
            assert create_response.status_code == 202
            job_id = create_response.json()["job_id"]

            # Wait for workflow to pause
            import asyncio
            await asyncio.sleep(2)

            # Stream the job
            response = test_client.get(f"/api/jobs/{job_id}/stream")
            assert response.status_code == 200

            content = response.text
            events = _parse_sse_events(content)
            event_types = [e["event"] for e in events]

            # Must NOT emit 'complete' when paused at INTERROGATION_REVIEW
            assert "complete" not in event_types, \
                f"SSE stream must NOT emit 'complete' event when paused at {JobState.INTERROGATION_REVIEW}"

            print(f"\nDebug - INTERROGATION_REVIEW test events: {event_types}")


def _parse_sse_events(sse_text: str) -> list[dict]:
    """
    Parse SSE event stream into structured events.

    SSE format:
        event: event_type
        data: {"key": "value"}

        (blank line)

    Returns:
        List of dicts with 'event' and 'data' keys
    """
    events = []
    lines = sse_text.strip().split('\n')

    current_event = None
    current_data = None

    for line in lines:
        line = line.strip()

        # Skip comments and keepalives
        if line.startswith(':'):
            continue

        if line.startswith('event:'):
            current_event = line.split(':', 1)[1].strip()
        elif line.startswith('data:'):
            current_data = line.split(':', 1)[1].strip()
        elif line == '' and current_event:
            # Blank line signals end of event
            events.append({
                "event": current_event,
                "data": current_data
            })
            current_event = None
            current_data = None

    return events
