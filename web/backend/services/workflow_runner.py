"""Async wrapper for running HydraWorkflow in background."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional
import logging

from web.backend.services.job_queue import Job, job_queue
from web.backend.models import JobState

# Import from parent project
from runtime.crewai.hydra_workflow import HydraWorkflow, WorkflowState
from runtime.crewai.llm_client import get_llm_client

logger = logging.getLogger(__name__)

# Thread pool for running blocking workflow operations
_executor = ThreadPoolExecutor(max_workers=4)


def _map_workflow_state(state: WorkflowState) -> JobState:
    """Map HydraWorkflow state to API JobState."""
    mapping = {
        WorkflowState.INITIALIZED: JobState.INITIALIZED,
        WorkflowState.GAP_ANALYSIS: JobState.GAP_ANALYSIS,
        WorkflowState.INTERROGATION: JobState.INTERROGATION,
        WorkflowState.DIFFERENTIATION: JobState.DIFFERENTIATION,
        WorkflowState.TAILORING: JobState.TAILORING,
        WorkflowState.ATS_OPTIMIZATION: JobState.ATS_OPTIMIZATION,
        WorkflowState.AUDITING: JobState.AUDITING,
        WorkflowState.COMPLETED: JobState.COMPLETED,
        WorkflowState.FAILED: JobState.FAILED,
    }
    return mapping.get(state, JobState.INITIALIZED)


def _run_workflow_sync(job: Job) -> None:
    """
    Run HydraWorkflow synchronously (called in thread pool).

    This is the blocking function that actually executes the workflow.
    """
    try:
        # Initialize LLM client
        llm = get_llm_client(model=job.model)

        # Create workflow
        workflow = HydraWorkflow(llm, max_audit_retries=job.max_audit_retries)

        # Build context
        context = {
            "job_description": job.job_description,
            "resume": job.resume,
            "source_documents": job.source_documents,
        }

        # Execute workflow
        result = workflow.execute(context)

        # Update job with results
        job.state = _map_workflow_state(result.state)
        job.success = result.success
        job.completed_at = datetime.now()
        job.final_documents = result.final_documents
        job.audit_report = result.audit_report
        job.intermediate_results = result.intermediate_results or {}
        job.execution_log = result.execution_log or []
        job.error_message = result.error_message
        job.audit_failed = getattr(result, "audit_failed", False)
        job.audit_error = getattr(result, "audit_error", None)
        job.agent_models = result.agent_models or {}

        logger.info(f"Job {job.id} completed: success={job.success}, state={job.state}")

    except Exception as e:
        logger.error(f"Job {job.id} failed with exception: {e}")
        job.state = JobState.FAILED
        job.success = False
        job.completed_at = datetime.now()
        job.error_message = str(e)


async def _poll_workflow_state(job: Job, workflow: HydraWorkflow) -> None:
    """Poll workflow state and emit SSE events."""
    last_state = None
    last_log_length = 0

    while job.state not in (JobState.COMPLETED, JobState.FAILED):
        await asyncio.sleep(1)  # Poll every second

        # Get current state from workflow
        current_state = _map_workflow_state(workflow.get_current_state())

        # Emit state change event
        if current_state != last_state:
            last_state = current_state
            job.state = current_state
            await job.emit_event("progress", {
                "state": current_state.value,
                "progress": job.get_progress_percent(),
            })

        # Emit new log entries
        current_log = workflow.get_execution_log()
        if len(current_log) > last_log_length:
            new_entries = current_log[last_log_length:]
            last_log_length = len(current_log)
            job.execution_log = current_log
            for entry in new_entries:
                await job.emit_event("log", {"message": entry})

        # Emit intermediate results
        intermediate = workflow.get_intermediate_results()
        for stage, result in intermediate.items():
            if stage not in job.intermediate_results:
                job.intermediate_results[stage] = result
                await job.emit_event("stage_complete", {
                    "stage": stage,
                    "result": result,
                })


async def run_workflow_async(job: Job) -> None:
    """
    Run HydraWorkflow asynchronously with progress updates.

    This wraps the sync workflow execution and polls for state changes.
    """
    job.started_at = datetime.now()
    job.state = JobState.INITIALIZED

    # Emit started event
    await job.emit_event("started", {
        "job_id": job.id,
        "state": job.state.value,
        "agent_models": job.agent_models,
    })

    loop = asyncio.get_event_loop()

    try:
        # Run blocking workflow in thread pool
        await loop.run_in_executor(_executor, _run_workflow_sync, job)

        # Emit completion event
        await job.emit_event("complete", {
            "job_id": job.id,
            "success": job.success,
            "state": job.state.value,
            "final_documents": job.final_documents,
            "audit_report": job.audit_report,
            "audit_failed": job.audit_failed,
            "audit_error": job.audit_error,
            "error_message": job.error_message,
            "agent_models": job.agent_models,
        })

    except Exception as e:
        logger.error(f"Async workflow failed for job {job.id}: {e}")
        job.state = JobState.FAILED
        job.error_message = str(e)
        job.completed_at = datetime.now()

        await job.emit_event("error", {
            "job_id": job.id,
            "error": str(e),
        })


def start_workflow_background(job: Job) -> None:
    """
    Start workflow execution in background.

    This schedules the async workflow to run without blocking.
    """
    asyncio.create_task(run_workflow_async(job))
