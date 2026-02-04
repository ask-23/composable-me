"""Job management endpoints with SSE streaming."""

import json
from datetime import datetime
from typing import AsyncGenerator

from litestar import Controller, get, post
from litestar.response import Response, Stream
from litestar.status_codes import HTTP_200_OK, HTTP_202_ACCEPTED, HTTP_404_NOT_FOUND
from litestar.exceptions import HTTPException

from web.backend.models import (
    CreateJobRequest,
    CreateJobResponse,
    JobResponse,
    FinalDocuments,
    AuditReport,
    JobState,
    AuditStatus,
    ApproveGapAnalysisRequest,
    SubmitInterviewAnswersRequest,
)
from web.backend.services.job_queue import job_queue
from web.backend.services.workflow_runner import start_workflow_background


_STATE_ORDER: dict[JobState, int] = {
    JobState.INITIALIZED: 0,
    JobState.GAP_ANALYSIS: 1,
    JobState.GAP_ANALYSIS_REVIEW: 2,
    JobState.INTERROGATION: 3,
    JobState.INTERROGATION_REVIEW: 4,
    JobState.DIFFERENTIATION: 5,
    JobState.TAILORING: 6,
    JobState.ATS_OPTIMIZATION: 7,
    JobState.AUDITING: 8,
    JobState.EXECUTIVE_SYNTHESIS: 9,
    JobState.COMPLETED: 10,
    JobState.FAILED: 11,
}


def _is_after_state(current: JobState, target: JobState) -> bool:
    return _STATE_ORDER.get(current, -1) > _STATE_ORDER.get(target, -1)


class JobsController(Controller):
    """Controller for job management endpoints."""

    path = "/api/jobs"

    @post("/", status_code=HTTP_202_ACCEPTED)
    async def create_job(self, data: CreateJobRequest) -> CreateJobResponse:
        """
        Create a new job and start processing in background.

        Returns job_id immediately while workflow runs asynchronously.
        """
        job = job_queue.create_job(
            job_description=data.job_description,
            resume=data.resume,
            source_documents=data.source_documents,
            company=data.company,
            role_title=data.role_title,
            source=data.source,
            url=data.url,
            model=data.model,
            max_audit_retries=data.max_audit_retries,
        )

        # Start workflow in background
        start_workflow_background(job)

        return CreateJobResponse(
            job_id=job.id,
            status="queued",
            created_at=job.created_at,
        )

    @post("/{job_id:str}/approve_gap_analysis", status_code=HTTP_200_OK)
    async def approve_gap_analysis(self, job_id: str, data: ApproveGapAnalysisRequest) -> dict:
        """Approve gap analysis and resume workflow."""
        job = job_queue.get_job(job_id)
        if not job:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Job not found")
        
        if job.state != JobState.GAP_ANALYSIS_REVIEW:
            # Idempotency: if user clicks twice or UI is stale, treat "already advanced" as a no-op.
            if _is_after_state(job.state, JobState.GAP_ANALYSIS_REVIEW):
                return {
                    "job_id": job_id,
                    "status": "noop",
                    "message": "Job already advanced past GAP_ANALYSIS_REVIEW",
                }
            raise HTTPException(status_code=400, detail=f"Job is not in GAP_ANALYSIS_REVIEW state (current: {job.state})")

        # Update job and get the updated object (crucial for workflow to see the approval)
        job = job_queue.update_job(job_id, gap_analysis_approved=data.approved)

        # Resume workflow with updated job
        start_workflow_background(job)
        
        return {"job_id": job_id, "status": "approved", "message": "Gap analysis approved, workflow resumed"}

    @post("/{job_id:str}/submit_interview_answers", status_code=HTTP_200_OK)
    async def submit_interview_answers(self, job_id: str, data: SubmitInterviewAnswersRequest) -> dict:
        """Submit interview answers and resume workflow."""
        job = job_queue.get_job(job_id)
        if not job:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Job not found")

        if job.state != JobState.INTERROGATION_REVIEW:
            if _is_after_state(job.state, JobState.INTERROGATION_REVIEW):
                return {
                    "job_id": job_id,
                    "status": "noop",
                    "message": "Job already advanced past INTERROGATION_REVIEW",
                }
            raise HTTPException(status_code=400, detail=f"Job is not in INTERROGATION_REVIEW state (current: {job.state})")

        # Update job and get the updated object (crucial for workflow to see the answers)
        job = job_queue.update_job(job_id, interview_answers=data.answers)

        # Resume workflow with updated job
        start_workflow_background(job)

        return {"job_id": job_id, "status": "submitted", "message": "Interview answers submitted, workflow resumed"}

    @get("/{job_id:str}", status_code=HTTP_200_OK)
    def get_job(self, job_id: str) -> JobResponse:
        """Get job status and results."""
        job = job_queue.get_job(job_id)

        if not job:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Job not found")

        # Build response
        final_docs = None
        if job.final_documents:
            final_docs = FinalDocuments(
                resume=job.final_documents.get("resume", ""),
                cover_letter=job.final_documents.get("cover_letter", ""),
            )

        audit_report = None
        if job.audit_report:
            audit_report = AuditReport(
                resume_audit=job.audit_report.get("resume_audit"),
                cover_letter_audit=job.audit_report.get("cover_letter_audit"),
                final_status=AuditStatus(job.audit_report.get("final_status")) if job.audit_report.get("final_status") else None,
                retry_count=job.audit_report.get("retry_count", 0),
                rejection_reason=job.audit_report.get("rejection_reason"),
                crash_error=job.audit_report.get("crash_error"),
            )

        return JobResponse(
            job_id=job.id,
            state=job.state,
            success=job.success,
            progress_percent=job.get_progress_percent(),
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            final_documents=final_docs,
            audit_report=audit_report,
            executive_brief=job.executive_brief,
            intermediate_results=job.intermediate_results,
            execution_log=job.execution_log,
            error_message=job.error_message,
            audit_failed=job.audit_failed,
            audit_error=job.audit_error,
            agent_models=job.agent_models,
        )

    @get("/{job_id:str}/stream")
    async def stream_job(self, job_id: str) -> Stream:
        """
        Stream job progress via Server-Sent Events.

        Events:
        - started: Job started processing
        - progress: State change with progress percent
        - log: New log entry
        - stage_complete: Agent stage completed with result
        - complete: Job finished (success or failure)
        - error: Error occurred
        """
        job = job_queue.get_job(job_id)

        if not job:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Job not found")

        async def event_generator() -> AsyncGenerator[bytes, None]:
            """Generate SSE events."""
            # Send initial state
            yield _format_sse_event("connected", {
                "job_id": job.id,
                "state": job.state.value,
                "progress": job.get_progress_percent(),
                "intermediate_results": job.intermediate_results,
                "agent_models": job.agent_models,
            })

            # If already complete, send final state and close
            if job.state in (JobState.COMPLETED, JobState.FAILED):
                yield _format_sse_event("complete", job.get_complete_event_payload())
                return

            # Stream events until job completes
            while True:
                event = await job.get_event(timeout=30.0)

                if event is None:
                    # Send keepalive comment
                    yield b": keepalive\n\n"
                    continue

                yield _format_sse_event(event["event"], event["data"])

                # Stop streaming on completion
                if event["event"] in ("complete", "error"):
                    break

        return Stream(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )


def _format_sse_event(event_type: str, data: dict) -> bytes:
    """Format data as SSE event."""
    json_data = json.dumps(data, default=str)
    return f"event: {event_type}\ndata: {json_data}\n\n".encode("utf-8")
