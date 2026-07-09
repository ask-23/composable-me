"""Async wrapper for running HydraWorkflow in background."""

import asyncio
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Optional

from web.backend.models import JobState
from web.backend.services.hydra_db import hydra_db
from web.backend.services.job_queue import Job, job_queue
from web.backend.observability.sse_errors import build_error_payload_from_exception
from web.backend.observability.sentry import capture_error, set_job_context

# Import from parent project
from runtime.crewai.hydra_workflow import HydraWorkflow, WorkflowState
from runtime.crewai.llm_client import get_llm_client

logger = logging.getLogger(__name__)

# Thread pool for running blocking workflow operations
_executor = ThreadPoolExecutor(max_workers=4)


def _artifacts_base_dir() -> Path:
    project_root = Path(__file__).parent.parent.parent
    return Path(os.environ.get("HYDRA_ARTIFACTS_DIR", str(project_root / "out")))


def _ensure_hydra_records(job: Job) -> None:
    company = job.company or "Unknown Company"
    role_title = job.role_title or "Unknown Role"

    if not job.hydra_job_id:
        hydra_job = hydra_db.create_job(
            company=company,
            role_title=role_title,
            source=job.source,
            url=job.url,
            status="new",
        )
        job.hydra_job_id = str(hydra_job["id"])
        hydra_db.create_job_description(job_id=job.hydra_job_id, jd_text=job.job_description)

    if not job.hydra_run_id:
        run = hydra_db.create_run(
            job_id=job.hydra_job_id,
            model_router=job.agent_models or None,
            config={
                "max_audit_retries": job.max_audit_retries,
                "model": job.model,
            },
            outcome=None,
        )
        job.hydra_run_id = str(run["id"])

    job_queue.update_job(
        job.id,
        company=company,
        role_title=role_title,
        source=job.source,
        url=job.url,
        hydra_job_id=job.hydra_job_id,
        hydra_run_id=job.hydra_run_id,
    )


def _persist_hydra_results(job: Job) -> None:
    if not job.hydra_job_id or not job.hydra_run_id:
        return

    outcome = "success" if job.success else "failed"
    hydra_db.update_run(
        run_id=job.hydra_run_id,
        model_router=job.agent_models or None,
        config={
            "max_audit_retries": job.max_audit_retries,
            "model": job.model,
        },
        outcome=outcome,
    )

    # Persist interview Q&A if available and not already stored.
    interrogation = job.intermediate_results.get("interrogation", {}) if job.intermediate_results else {}
    questions = interrogation.get("questions", []) if isinstance(interrogation, dict) else []
    answers = job.interview_answers or interrogation.get("interview_notes", [])
    if (questions or answers) and not hydra_db.list_interviews(job.hydra_run_id):
        structured_notes = interrogation if isinstance(interrogation, dict) and interrogation else {
            "questions": questions,
            "answers": answers,
        }
        hydra_db.create_interview(
            run_id=job.hydra_run_id,
            questions=questions,
            answers=answers,
            structured_notes=structured_notes,
        )

    base_dir = _artifacts_base_dir()
    company = job.company or "Unknown Company"
    role_title = job.role_title or "Unknown Role"

    if job.final_documents:
        resume = job.final_documents.get("resume")
        if resume:
            hydra_db.create_artifact_with_disk_write(
                base_dir=base_dir,
                company=company,
                role_title=role_title,
                run_id=job.hydra_run_id,
                kind="resume",
                content=resume,
            )
        cover_letter = job.final_documents.get("cover_letter")
        if cover_letter:
            hydra_db.create_artifact_with_disk_write(
                base_dir=base_dir,
                company=company,
                role_title=role_title,
                run_id=job.hydra_run_id,
                kind="cover_letter",
                content=cover_letter,
            )

    if job.audit_report:
        audit_content = json.dumps(job.audit_report, indent=2, sort_keys=True)
        hydra_db.create_artifact_with_disk_write(
            base_dir=base_dir,
            company=company,
            role_title=role_title,
            run_id=job.hydra_run_id,
            kind="audit_report",
            content=audit_content,
        )


def _map_workflow_state(state: WorkflowState) -> JobState:
    """Map HydraWorkflow state to API JobState."""
    mapping = {
        WorkflowState.INITIALIZED: JobState.INITIALIZED,
        WorkflowState.GAP_ANALYSIS: JobState.GAP_ANALYSIS,
        WorkflowState.GAP_ANALYSIS_REVIEW: JobState.GAP_ANALYSIS_REVIEW,
        WorkflowState.INTERROGATION: JobState.INTERROGATION,
        WorkflowState.INTERROGATION_REVIEW: JobState.INTERROGATION_REVIEW,
        WorkflowState.DIFFERENTIATION: JobState.DIFFERENTIATION,
        WorkflowState.TAILORING: JobState.TAILORING,
        WorkflowState.ATS_OPTIMIZATION: JobState.ATS_OPTIMIZATION,
        WorkflowState.AUDITING: JobState.AUDITING,
        WorkflowState.EXECUTIVE_SYNTHESIS: JobState.EXECUTIVE_SYNTHESIS,
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
        job.started_at = datetime.now()
        job_queue.update_job(job.id, started_at=job.started_at, state=job.state)

        # Initialize LLM client
        llm = get_llm_client(model=job.model)

        # Create workflow
        workflow = HydraWorkflow(llm, max_audit_retries=job.max_audit_retries)

        # Build context
        context = {
            "job_description": job.job_description,
            "resume": job.resume,
            "source_documents": job.source_documents,
            "previous_results": job.intermediate_results,
            "gap_analysis_approved": job.gap_analysis_approved,
            "interview_answers": job.interview_answers,
        }

        # Execute workflow
        result = workflow.execute(context)

        # Update job with results
        job.state = _map_workflow_state(result.state)
        job.success = result.success
        job.final_documents = result.final_documents
        job.audit_report = result.audit_report
        job.executive_brief = getattr(result, "executive_brief", None)
        # Merge intermediate results to preserve any that were collected
        if result.intermediate_results:
            job.intermediate_results = {**job.intermediate_results, **result.intermediate_results}
        job.execution_log = result.execution_log or []
        job.error_message = result.error_message
        job.audit_failed = getattr(result, "audit_failed", False)
        job.audit_error = getattr(result, "audit_error", None)
        job.agent_models = result.agent_models or {}

        if job.state not in (JobState.GAP_ANALYSIS_REVIEW, JobState.INTERROGATION_REVIEW):
            job.completed_at = datetime.now()

        _ensure_hydra_records(job)
        _persist_hydra_results(job)
        job_queue.update_job(job.id)

        logger.info(f"Job {job.id} completed: success={job.success}, state={job.state}")

    except Exception as e:
        logger.error(f"Job {job.id} failed with exception: {e}")
        job.state = JobState.FAILED
        job.success = False
        job.completed_at = datetime.now()
        job.error_message = str(e)
        _ensure_hydra_records(job)
        _persist_hydra_results(job)
        job_queue.update_job(job.id)


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

    This runs the sync workflow in a thread pool while polling for state changes.
    """
    job.started_at = datetime.now()
    job.state = JobState.INITIALIZED
    job_queue.update_job(job.id, started_at=job.started_at, state=job.state)

    # Emit started event
    await job.emit_event("started", {
        "job_id": job.id,
        "state": job.state.value,
        "agent_models": job.agent_models,
    })

    loop = asyncio.get_event_loop()

    try:
        # Initialize LLM client
        llm = get_llm_client(model=job.model)
        
        # Create workflow
        workflow = HydraWorkflow(llm, max_audit_retries=job.max_audit_retries)
        
        # Store agent_models immediately so it's available
        job.agent_models = workflow.agent_models
        _ensure_hydra_records(job)

        # Build context (include previous results for resuming)
        context = {
            "job_description": job.job_description,
            "resume": job.resume,
            "source_documents": job.source_documents,
            "previous_results": job.intermediate_results,
            "gap_analysis_approved": job.gap_analysis_approved,
            "interview_answers": job.interview_answers,
        }

        # Create a future for the workflow execution
        def run_workflow():
            return workflow.execute(context)

        future = loop.run_in_executor(_executor, run_workflow)

        # Poll for state changes while workflow runs
        last_state = None
        last_log_length = 0
        emitted_stages: set[str] = set()  # Track stages already emitted via SSE

        while not future.done():
            await asyncio.sleep(0.5)  # Poll twice per second for responsiveness
            
            # Get current state from workflow
            current_state = _map_workflow_state(workflow.get_current_state())
            
            # Emit state change event
            if current_state != last_state:
                last_state = current_state
                job.state = current_state
                await job.emit_event("progress", {
                    "state": current_state.value,
                    "progress": job.get_progress_percent(),
                    "agent_models": job.agent_models,
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
            for stage, stage_result in intermediate.items():
                if stage not in emitted_stages:
                    emitted_stages.add(stage)
                    job.intermediate_results[stage] = stage_result
                    await job.emit_event("stage_complete", {
                        "stage": stage,
                        "result": stage_result,
                    })

        # Get the result from the future
        result = future.result()

        # Update job with results
        job.state = _map_workflow_state(result.state)
        job.success = result.success
        job.final_documents = result.final_documents
        job.audit_report = result.audit_report
        job.executive_brief = getattr(result, "executive_brief", None)
        # Merge intermediate results - don't overwrite what was collected during polling
        if result.intermediate_results:
            job.intermediate_results = {**job.intermediate_results, **result.intermediate_results}

        # Emit stage_complete for any stages not emitted during polling loop.
        # This handles stages that completed after the final poll but before
        # future.done() returned True (race condition fix).
        for stage, stage_result in job.intermediate_results.items():
            if stage not in emitted_stages:
                await job.emit_event("stage_complete", {
                    "stage": stage,
                    "result": stage_result,
                })

        job.execution_log = result.execution_log or []
        job.error_message = result.error_message
        job.audit_failed = getattr(result, "audit_failed", False)
        job.audit_error = getattr(result, "audit_error", None)
        job.agent_models = result.agent_models or {}

        logger.info(f"Job {job.id} completed: success={job.success}, state={job.state}")

        # Always emit a final progress update so clients see the final state,
        # even if the workflow finished between polling intervals.
        await job.emit_event("progress", {
            "state": job.state.value,
            "progress": job.get_progress_percent(),
            "agent_models": job.agent_models,
        })

        # Pause states are not terminal: keep SSE stream alive and do not mark completed.
        if job.state in (JobState.GAP_ANALYSIS_REVIEW, JobState.INTERROGATION_REVIEW):
            job_queue.update_job(job.id)
            return

        # Terminal-ish: mark completion and emit completion event.
        job.completed_at = datetime.now()
        _persist_hydra_results(job)
        job_queue.update_job(job.id)
        await job.emit_event("complete", job.get_complete_event_payload())

    except Exception as e:
        logger.error(f"Async workflow failed for job {job.id}: {e}")
        job.state = JobState.FAILED
        job.error_message = str(e)
        job.completed_at = datetime.now()

        _ensure_hydra_records(job)
        _persist_hydra_results(job)
        job_queue.update_job(job.id)

        # Capture to Sentry with job context
        sentry_event_id = capture_error(
            e,
            stage=job.state.value if job.state else "unknown",
        ) or ""

        # Emit structured SSE error payload with PII redaction
        error_payload = build_error_payload_from_exception(
            job_id=job.id,
            error=e,
            stage=job.state.value if job.state else "",
            sentry_event_id=sentry_event_id,
        )
        await job.emit_event("error", error_payload)


def start_workflow_background(job: Job) -> None:
    """
    Start workflow execution in background.

    This schedules the async workflow to run without blocking.
    """
    asyncio.create_task(run_workflow_async(job))
