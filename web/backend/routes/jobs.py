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
)
from web.backend.services.job_queue import job_queue
from web.backend.services.workflow_runner import start_workflow_background


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

    @get("/{job_id:str}", status_code=HTTP_200_OK)
    async def get_job(self, job_id: str) -> JobResponse:
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
            intermediate_results=job.intermediate_results,
            execution_log=job.execution_log,
            error_message=job.error_message,
            audit_failed=job.audit_failed,
            audit_error=job.audit_error,
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
            })

            # If already complete, send final state and close
            if job.state in (JobState.COMPLETED, JobState.FAILED):
                yield _format_sse_event("complete", {
                    "job_id": job.id,
                    "success": job.success,
                    "state": job.state.value,
                    "final_documents": job.final_documents,
                    "audit_report": job.audit_report,
                    "audit_failed": job.audit_failed,
                })
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
