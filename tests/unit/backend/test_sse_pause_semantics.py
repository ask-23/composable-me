"""Test SSE pause semantics - when workflow pauses, no 'complete' event should be emitted."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from runtime.crewai.hydra_workflow import WorkflowState, WorkflowResult


async def _drain_job_events(job) -> list[dict]:
    events: list[dict] = []
    while not job._event_queue.empty():
        events.append(await job._event_queue.get())
    return events


@pytest.mark.asyncio
async def test_run_workflow_async_does_not_emit_complete_on_pause():
    """
    Deterministic regression test for the original bug:

    When HydraWorkflow returns a paused review state (e.g. GAP_ANALYSIS_REVIEW),
    backend MUST NOT emit an SSE 'complete' event.

    This test calls run_workflow_async(job) directly and inspects the job's
    in-memory SSE event queue so it doesn't depend on TestClient scheduling.
    """

    from web.backend.services.job_queue import job_queue
    from web.backend.services.workflow_runner import run_workflow_async

    mock_workflow_result = WorkflowResult(
        state=WorkflowState.GAP_ANALYSIS_REVIEW,
        success=False,
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

    with patch("web.backend.services.workflow_runner.HydraWorkflow") as mock_workflow_class:
        mock_workflow_instance = MagicMock()
        mock_workflow_instance.execute.return_value = mock_workflow_result
        mock_workflow_instance.get_current_state.return_value = WorkflowState.GAP_ANALYSIS_REVIEW
        mock_workflow_instance.get_execution_log.return_value = mock_workflow_result.execution_log
        mock_workflow_instance.get_intermediate_results.return_value = mock_workflow_result.intermediate_results
        mock_workflow_instance.agent_models = mock_workflow_result.agent_models
        mock_workflow_class.return_value = mock_workflow_instance

        with patch("web.backend.services.workflow_runner.get_llm_client") as mock_llm:
            mock_llm.return_value = MagicMock(model="test-model")

            job = job_queue.create_job(
                job_description="Test JD",
                resume="Test resume",
                source_documents="",
                model="test-model",
                max_audit_retries=0,
            )

            await run_workflow_async(job)

            events = await _drain_job_events(job)
            event_types = [e["event"] for e in events]

            assert "started" in event_types
            assert job.completed_at is None
            assert "complete" not in event_types, (
                "Backend must not emit 'complete' when workflow pauses at GAP_ANALYSIS_REVIEW; "
                f"got events={event_types}"
            )

@pytest.mark.asyncio
async def test_run_workflow_async_does_not_emit_complete_on_interrogation_review_pause():
    """
    Deterministic pause semantics test for INTERROGATION_REVIEW state.
    """

    from web.backend.services.job_queue import job_queue
    from web.backend.services.workflow_runner import run_workflow_async

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

    with patch("web.backend.services.workflow_runner.HydraWorkflow") as mock_workflow_class:
        mock_workflow_instance = MagicMock()
        mock_workflow_instance.execute.return_value = mock_workflow_result
        mock_workflow_instance.get_current_state.return_value = WorkflowState.INTERROGATION_REVIEW
        mock_workflow_instance.get_execution_log.return_value = mock_workflow_result.execution_log
        mock_workflow_instance.get_intermediate_results.return_value = mock_workflow_result.intermediate_results
        mock_workflow_instance.agent_models = mock_workflow_result.agent_models
        mock_workflow_class.return_value = mock_workflow_instance

        with patch("web.backend.services.workflow_runner.get_llm_client") as mock_llm:
            mock_llm.return_value = MagicMock(model="test-model")

            job = job_queue.create_job(
                job_description="Test JD",
                resume="Test resume",
                source_documents="",
                model="test-model",
                max_audit_retries=0,
            )

            await run_workflow_async(job)

            events = await _drain_job_events(job)
            event_types = [e["event"] for e in events]

            assert "started" in event_types
            assert job.completed_at is None
            assert "complete" not in event_types, (
                "Backend must not emit 'complete' when workflow pauses at INTERROGATION_REVIEW; "
                f"got events={event_types}"
            )


@pytest.mark.asyncio
async def test_run_workflow_async_emits_complete_on_completion():
    """Control test: when workflow returns COMPLETED, backend emits 'complete' and sets completed_at."""

    from web.backend.services.job_queue import job_queue
    from web.backend.services.workflow_runner import run_workflow_async

    mock_workflow_result = WorkflowResult(
        state=WorkflowState.COMPLETED,
        success=True,
        final_documents={"resume": "Final resume", "cover_letter": "Final cover letter"},
        audit_report={"final_status": "APPROVED"},
        executive_brief={"summary": "Test brief"},
        error_message=None,
        execution_log=["Started", "Completed all stages"],
        intermediate_results={"tailoring": {"status": "complete"}},
        audit_failed=False,
        audit_error=None,
        agent_models={"tailoring": "gpt-4o"},
    )

    with patch("web.backend.services.workflow_runner.HydraWorkflow") as mock_workflow_class:
        mock_workflow_instance = MagicMock()
        mock_workflow_instance.execute.return_value = mock_workflow_result
        mock_workflow_instance.get_current_state.return_value = WorkflowState.COMPLETED
        mock_workflow_instance.get_execution_log.return_value = mock_workflow_result.execution_log
        mock_workflow_instance.get_intermediate_results.return_value = mock_workflow_result.intermediate_results
        mock_workflow_instance.agent_models = mock_workflow_result.agent_models
        mock_workflow_class.return_value = mock_workflow_instance

        with patch("web.backend.services.workflow_runner.get_llm_client") as mock_llm:
            mock_llm.return_value = MagicMock(model="test-model")

            job = job_queue.create_job(
                job_description="Test JD",
                resume="Test resume",
                source_documents="",
                model="test-model",
                max_audit_retries=0,
            )

            await run_workflow_async(job)

            events = await _drain_job_events(job)
            event_types = [e["event"] for e in events]

            assert "started" in event_types
            assert "complete" in event_types
            assert job.completed_at is not None


@pytest.mark.asyncio
async def test_run_workflow_async_emits_stage_complete_for_intermediate_results_on_pause():
    """
    Regression test for race condition fix:

    When workflow pauses (e.g. at GAP_ANALYSIS_REVIEW), the backend MUST emit
    'stage_complete' events for all intermediate results, even if the polling
    loop didn't catch them before the workflow finished.

    This tests the fix for the bug where:
    1. Gap analysis completes and stores result
    2. WorkflowPaused is raised immediately
    3. Polling loop exits before catching the intermediate result
    4. Frontend never receives stage_complete event
    5. User sees "No output to review" with FIT SCORE = 0
    """

    from web.backend.services.job_queue import job_queue
    from web.backend.services.workflow_runner import run_workflow_async

    gap_analysis_result = {
        "fit_score": 75,
        "matches": ["Python", "AWS", "Leadership"],
        "gaps": ["Kubernetes"],
        "adjacent_skills": ["Docker"],
    }

    mock_workflow_result = WorkflowResult(
        state=WorkflowState.GAP_ANALYSIS_REVIEW,
        success=False,
        final_documents=None,
        audit_report=None,
        executive_brief=None,
        error_message=None,
        execution_log=["Started workflow", "Completed gap analysis", "Pausing for review"],
        intermediate_results={"gap_analysis": gap_analysis_result},
        audit_failed=False,
        audit_error=None,
        agent_models={"gap_analyzer": "together_ai/meta-llama/Llama-4-Maverick"},
    )

    with patch("web.backend.services.workflow_runner.HydraWorkflow") as mock_workflow_class:
        mock_workflow_instance = MagicMock()
        mock_workflow_instance.execute.return_value = mock_workflow_result
        mock_workflow_instance.get_current_state.return_value = WorkflowState.GAP_ANALYSIS_REVIEW
        mock_workflow_instance.get_execution_log.return_value = mock_workflow_result.execution_log
        # Simulate race condition: polling loop sees empty intermediate results
        # but workflow.execute() returns them in the final result
        mock_workflow_instance.get_intermediate_results.return_value = {}
        mock_workflow_instance.agent_models = mock_workflow_result.agent_models
        mock_workflow_class.return_value = mock_workflow_instance

        with patch("web.backend.services.workflow_runner.get_llm_client") as mock_llm:
            mock_llm.return_value = MagicMock(model="test-model")

            job = job_queue.create_job(
                job_description="Test JD",
                resume="Test resume",
                source_documents="",
                model="test-model",
                max_audit_retries=0,
            )

            await run_workflow_async(job)

            events = await _drain_job_events(job)
            event_types = [e["event"] for e in events]

            # Find stage_complete events
            stage_complete_events = [e for e in events if e["event"] == "stage_complete"]

            assert "stage_complete" in event_types, (
                "Backend must emit 'stage_complete' for intermediate results even when "
                "polling loop misses them due to race condition"
            )

            # Verify the gap_analysis stage_complete was emitted with correct data
            gap_analysis_events = [
                e for e in stage_complete_events
                if e["data"].get("stage") == "gap_analysis"
            ]
            assert len(gap_analysis_events) == 1, (
                f"Expected exactly one stage_complete for gap_analysis, got {len(gap_analysis_events)}"
            )

            emitted_result = gap_analysis_events[0]["data"]["result"]
            assert emitted_result["fit_score"] == 75, (
                f"stage_complete event should contain full gap analysis result, got {emitted_result}"
            )
