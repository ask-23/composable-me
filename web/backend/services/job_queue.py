"""Postgres-backed job queue for tracking workflow execution.

Jobs are persisted to Postgres and survive server restarts.
SSE event queues remain in-memory (ephemeral by design).
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Optional

from psycopg.types.json import Json

from web.backend.db import apply_migrations, get_conn
from web.backend.models import JobState


def _init_db() -> None:
    """Initialize the database schema if needed."""
    apply_migrations()


# Initialize DB on module load
_init_db()


@dataclass
class Job:
    """Represents a job in the queue."""

    id: str
    company: Optional[str] = None
    role_title: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    hydra_job_id: Optional[str] = None
    hydra_run_id: Optional[str] = None
    state: JobState = JobState.INITIALIZED
    success: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Input context
    job_description: str = ""
    resume: str = ""
    source_documents: str = ""
    model: Optional[str] = None
    max_audit_retries: int = 2

    # Results
    final_documents: Optional[dict[str, str]] = None
    audit_report: Optional[dict[str, Any]] = None
    executive_brief: Optional[dict[str, Any]] = None
    intermediate_results: dict[str, Any] = field(default_factory=dict)
    execution_log: list[str] = field(default_factory=list)
    error_message: Optional[str] = None
    audit_failed: bool = False
    audit_error: Optional[str] = None
    agent_models: dict[str, str] = field(default_factory=dict)

    # User inputs for resume
    gap_analysis_approved: bool = False
    interview_answers: list[dict[str, Any]] = field(default_factory=list)

    # For SSE updates (in-memory only, not persisted)
    _event_queue: asyncio.Queue = field(default_factory=asyncio.Queue, repr=False)

    def get_progress_percent(self) -> int:
        """Calculate progress percentage based on current state."""
        stage_progress = {
            JobState.INITIALIZED: 0,
            JobState.GAP_ANALYSIS: 15,
            JobState.GAP_ANALYSIS_REVIEW: 18,
            JobState.INTERROGATION: 30,
            JobState.INTERROGATION_REVIEW: 35,
            JobState.DIFFERENTIATION: 45,
            JobState.TAILORING: 60,
            JobState.ATS_OPTIMIZATION: 75,
            JobState.AUDITING: 90,
            JobState.EXECUTIVE_SYNTHESIS: 95,
            JobState.COMPLETED: 100,
            JobState.FAILED: 100,
        }
        return stage_progress.get(self.state, 0)

    async def emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit an SSE event to listeners."""
        await self._event_queue.put({"event": event_type, "data": data})

    async def get_event(self, timeout: float = 30.0) -> Optional[dict[str, Any]]:
        """Get next event from queue with timeout."""
        try:
            return await asyncio.wait_for(self._event_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    def get_complete_event_payload(self) -> dict[str, Any]:
        """Generate the complete event payload (DRY helper for SSE).

        Used by both workflow_runner.py (live completion) and
        jobs.py (already-complete reconnection) to ensure consistency.
        """
        return {
            "job_id": self.id,
            "success": self.success,
            "state": self.state.value,
            "final_documents": self.final_documents,
            "audit_report": self.audit_report,
            "executive_brief": self.executive_brief,
            "audit_failed": self.audit_failed,
            "audit_error": self.audit_error,
            "error_message": self.error_message,
            "agent_models": self.agent_models,
        }


def _deserialize_datetime(value: Optional[object]) -> Optional[datetime]:
    """Convert stored value back to datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return None


def _coerce_json(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return value


def _row_to_job(row: dict[str, Any]) -> Job:
    """Convert database row to Job."""
    return Job(
        id=row["id"],
        company=row.get("company"),
        role_title=row.get("role_title"),
        source=row.get("source"),
        url=row.get("url"),
        hydra_job_id=row.get("hydra_job_id"),
        hydra_run_id=row.get("hydra_run_id"),
        state=JobState(row["state"]),
        success=bool(row["success"]),
        created_at=_deserialize_datetime(row.get("created_at")) or datetime.now(),
        started_at=_deserialize_datetime(row.get("started_at")),
        completed_at=_deserialize_datetime(row.get("completed_at")),
        job_description=row.get("job_description") or "",
        resume=row.get("resume") or "",
        source_documents=row.get("source_documents") or "",
        model=row.get("model"),
        max_audit_retries=row.get("max_audit_retries") or 2,
        final_documents=_coerce_json(row.get("final_documents"), None),
        audit_report=_coerce_json(row.get("audit_report"), None),
        executive_brief=_coerce_json(row.get("executive_brief"), None),
        intermediate_results=_coerce_json(row.get("intermediate_results"), {}),
        execution_log=_coerce_json(row.get("execution_log"), []),
        error_message=row.get("error_message"),
        audit_failed=bool(row.get("audit_failed")),
        audit_error=row.get("audit_error"),
        agent_models=_coerce_json(row.get("agent_models"), {}),
        gap_analysis_approved=bool(row.get("gap_analysis_approved")),
        interview_answers=_coerce_json(row.get("interview_answers"), []),
    )


class JobQueue:
    """Thread-safe Postgres-backed job storage."""

    def __init__(self) -> None:
        self._lock = Lock()
        # In-memory cache for active jobs (for SSE event queues)
        self._active_jobs: dict[str, Job] = {}

    def create_job(
        self,
        job_description: str,
        resume: str,
        source_documents: str = "",
        company: Optional[str] = None,
        role_title: Optional[str] = None,
        source: Optional[str] = None,
        url: Optional[str] = None,
        model: Optional[str] = None,
        max_audit_retries: int = 2,
    ) -> Job:
        """Create and store a new job."""
        job_id = str(uuid.uuid4())
        safe_company = company or "Unknown Company"
        safe_role = role_title or "Unknown Role"
        job = Job(
            id=job_id,
            company=safe_company,
            role_title=safe_role,
            source=source,
            url=url,
            job_description=job_description,
            resume=resume,
            source_documents=source_documents,
            model=model,
            max_audit_retries=max_audit_retries,
        )

        with self._lock:
            with get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO job_queue (
                        id, company, role_title, source, url, hydra_job_id, hydra_run_id,
                        state, success, created_at, started_at, completed_at,
                        job_description, resume, source_documents, model, max_audit_retries,
                        final_documents, audit_report, executive_brief, intermediate_results,
                        execution_log, error_message, audit_failed, audit_error, agent_models,
                        gap_analysis_approved, interview_answers
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s
                    )
                    """,
                    (
                        job.id,
                        job.company,
                        job.role_title,
                        job.source,
                        job.url,
                        job.hydra_job_id,
                        job.hydra_run_id,
                        job.state.value,
                        job.success,
                        job.created_at,
                        job.started_at,
                        job.completed_at,
                        job.job_description,
                        job.resume,
                        job.source_documents,
                        job.model,
                        job.max_audit_retries,
                        Json(job.final_documents) if job.final_documents is not None else None,
                        Json(job.audit_report) if job.audit_report is not None else None,
                        Json(job.executive_brief) if job.executive_brief is not None else None,
                        Json(job.intermediate_results),
                        Json(job.execution_log),
                        job.error_message,
                        job.audit_failed,
                        job.audit_error,
                        Json(job.agent_models),
                        job.gap_analysis_approved,
                        Json(job.interview_answers),
                    ),
                )
                conn.commit()

            # Cache for SSE events
            self._active_jobs[job_id] = job

        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        # Check cache first (for active SSE connections)
        with self._lock:
            if job_id in self._active_jobs:
                return self._active_jobs[job_id]

        # Fetch from database
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM job_queue WHERE id = %s", (job_id,)).fetchone()
            if row:
                job = _row_to_job(row)
                with self._lock:
                    self._active_jobs[job_id] = job
                return job
            return None

    def update_job(self, job_id: str, **kwargs) -> Optional[Job]:
        """Update job fields."""
        with self._lock:
            job = self._active_jobs.get(job_id)
            if not job:
                # Load from DB if not in cache
                with get_conn() as conn:
                    row = conn.execute("SELECT * FROM job_queue WHERE id = %s", (job_id,)).fetchone()
                    if row:
                        job = _row_to_job(row)
                        self._active_jobs[job_id] = job

            if not job:
                return None

            # Update in-memory object
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)

            # Persist to database
            with get_conn() as conn:
                conn.execute(
                    """
                    UPDATE job_queue SET
                        company = %s,
                        role_title = %s,
                        source = %s,
                        url = %s,
                        hydra_job_id = %s,
                        hydra_run_id = %s,
                        state = %s,
                        success = %s,
                        started_at = %s,
                        completed_at = %s,
                        final_documents = %s,
                        audit_report = %s,
                        executive_brief = %s,
                        intermediate_results = %s,
                        execution_log = %s,
                        error_message = %s,
                        audit_failed = %s,
                        audit_error = %s,
                        agent_models = %s,
                        gap_analysis_approved = %s,
                        interview_answers = %s
                    WHERE id = %s
                    """,
                    (
                        job.company,
                        job.role_title,
                        job.source,
                        job.url,
                        job.hydra_job_id,
                        job.hydra_run_id,
                        job.state.value,
                        job.success,
                        job.started_at,
                        job.completed_at,
                        Json(job.final_documents) if job.final_documents is not None else None,
                        Json(job.audit_report) if job.audit_report is not None else None,
                        Json(job.executive_brief) if job.executive_brief is not None else None,
                        Json(job.intermediate_results),
                        Json(job.execution_log),
                        job.error_message,
                        job.audit_failed,
                        job.audit_error,
                        Json(job.agent_models),
                        job.gap_analysis_approved,
                        Json(job.interview_answers),
                        job_id,
                    ),
                )
                conn.commit()

            return job

    def list_jobs(self, limit: int = 10, offset: int = 0) -> list[Job]:
        """List jobs with pagination."""
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM job_queue ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (limit, offset),
            ).fetchall()
            return [_row_to_job(row) for row in rows]

    def delete_job(self, job_id: str) -> bool:
        """Delete a job by ID."""
        with self._lock:
            if job_id in self._active_jobs:
                del self._active_jobs[job_id]

        with get_conn() as conn:
            cursor = conn.execute("DELETE FROM job_queue WHERE id = %s", (job_id,))
            conn.commit()
            return cursor.rowcount > 0


# Global job queue instance
job_queue = JobQueue()
