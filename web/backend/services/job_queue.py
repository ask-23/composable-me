"""SQLite-backed job queue for tracking workflow execution.

Jobs are persisted to disk and survive server restarts.
SSE event queues remain in-memory (ephemeral by design).
"""

import json
import sqlite3
import uuid
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Optional

from web.backend.models import JobState


# Database path - relative to project root
DB_PATH = Path(__file__).parent.parent / "data" / "jobs.db"


def _ensure_db_dir():
    """Ensure the data directory exists."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _init_db():
    """Initialize the database schema if needed."""
    _ensure_db_dir()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            state TEXT NOT NULL DEFAULT 'INITIALIZED',
            success INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            started_at TEXT,
            completed_at TEXT,
            job_description TEXT DEFAULT '',
            resume TEXT DEFAULT '',
            source_documents TEXT DEFAULT '',
            model TEXT,
            max_audit_retries INTEGER DEFAULT 2,
            final_documents TEXT,
            audit_report TEXT,
            executive_brief TEXT,
            intermediate_results TEXT DEFAULT '{}',
            execution_log TEXT DEFAULT '[]',
            error_message TEXT,
            audit_failed INTEGER DEFAULT 0,
            audit_error TEXT,
            agent_models TEXT DEFAULT '{}',
            gap_analysis_approved INTEGER DEFAULT 0,
            interview_answers TEXT DEFAULT '[]'
        )
    """)
    conn.commit()
    conn.close()


# Initialize DB on module load
_init_db()


@dataclass
class Job:
    """Represents a job in the queue."""
    id: str
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


def _serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO string for storage."""
    return dt.isoformat() if dt else None


def _deserialize_datetime(s: Optional[str]) -> Optional[datetime]:
    """Convert ISO string back to datetime."""
    return datetime.fromisoformat(s) if s else None


def _job_to_row(job: Job) -> tuple:
    """Convert Job to database row."""
    return (
        job.id,
        job.state.value,
        1 if job.success else 0,
        _serialize_datetime(job.created_at),
        _serialize_datetime(job.started_at),
        _serialize_datetime(job.completed_at),
        job.job_description,
        job.resume,
        job.source_documents,
        job.model,
        job.max_audit_retries,
        json.dumps(job.final_documents) if job.final_documents else None,
        json.dumps(job.audit_report) if job.audit_report else None,
        json.dumps(job.executive_brief) if job.executive_brief else None,
        json.dumps(job.intermediate_results),
        json.dumps(job.execution_log),
        job.error_message,
        1 if job.audit_failed else 0,
        job.audit_error,
        json.dumps(job.agent_models),
        1 if job.gap_analysis_approved else 0,
        json.dumps(job.interview_answers),
    )


def _row_to_job(row: tuple) -> Job:
    """Convert database row to Job."""
    return Job(
        id=row[0],
        state=JobState(row[1]),
        success=bool(row[2]),
        created_at=_deserialize_datetime(row[3]) or datetime.now(),
        started_at=_deserialize_datetime(row[4]),
        completed_at=_deserialize_datetime(row[5]),
        job_description=row[6] or "",
        resume=row[7] or "",
        source_documents=row[8] or "",
        model=row[9],
        max_audit_retries=row[10] or 2,
        final_documents=json.loads(row[11]) if row[11] else None,
        audit_report=json.loads(row[12]) if row[12] else None,
        executive_brief=json.loads(row[13]) if row[13] else None,
        intermediate_results=json.loads(row[14]) if row[14] else {},
        execution_log=json.loads(row[15]) if row[15] else [],
        error_message=row[16],
        audit_failed=bool(row[17]),
        audit_error=row[18],
        agent_models=json.loads(row[19]) if row[19] else {},
        gap_analysis_approved=bool(row[20]) if len(row) > 20 else False,
        interview_answers=json.loads(row[21]) if len(row) > 21 and row[21] else [],
    )


class JobQueue:
    """Thread-safe SQLite-backed job storage."""

    def __init__(self):
        self._lock = Lock()
        # In-memory cache for active jobs (for SSE event queues)
        self._active_jobs: dict[str, Job] = {}

    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(str(DB_PATH))

    def create_job(
        self,
        job_description: str,
        resume: str,
        source_documents: str = "",
        model: Optional[str] = None,
        max_audit_retries: int = 2,
    ) -> Job:
        """Create and store a new job."""
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            job_description=job_description,
            resume=resume,
            source_documents=source_documents,
            model=model,
            max_audit_retries=max_audit_retries,
        )

        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    INSERT INTO jobs (
                        id, state, success, created_at, started_at, completed_at,
                        job_description, resume, source_documents, model, max_audit_retries,
                        final_documents, audit_report, executive_brief, intermediate_results,
                        execution_log, error_message, audit_failed, audit_error, agent_models,
                        gap_analysis_approved, interview_answers
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, _job_to_row(job))
                conn.commit()
            finally:
                conn.close()
            
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
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                job = _row_to_job(row)
                with self._lock:
                    self._active_jobs[job_id] = job
                return job
            return None
        finally:
            conn.close()

    def update_job(self, job_id: str, **kwargs) -> Optional[Job]:
        """Update job fields."""
        with self._lock:
            job = self._active_jobs.get(job_id)
            if not job:
                # Load from DB if not in cache
                conn = self._get_conn()
                try:
                    cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
                    row = cursor.fetchone()
                    if row:
                        job = _row_to_job(row)
                        self._active_jobs[job_id] = job
                finally:
                    conn.close()
            
            if not job:
                return None
            
            # Update in-memory object
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            
            # Persist to database
            conn = self._get_conn()
            try:
                conn.execute("""
                    UPDATE jobs SET
                        state = ?, success = ?, started_at = ?, completed_at = ?,
                        final_documents = ?, audit_report = ?, executive_brief = ?,
                        intermediate_results = ?, execution_log = ?, error_message = ?,
                        audit_failed = ?, audit_error = ?, agent_models = ?,
                        gap_analysis_approved = ?, interview_answers = ?
                    WHERE id = ?
                """, (
                    job.state.value,
                    1 if job.success else 0,
                    _serialize_datetime(job.started_at),
                    _serialize_datetime(job.completed_at),
                    json.dumps(job.final_documents) if job.final_documents else None,
                    json.dumps(job.audit_report) if job.audit_report else None,
                    json.dumps(job.executive_brief) if job.executive_brief else None,
                    json.dumps(job.intermediate_results),
                    json.dumps(job.execution_log),
                    job.error_message,
                    1 if job.audit_failed else 0,
                    job.audit_error,
                    json.dumps(job.agent_models),
                    1 if job.gap_analysis_approved else 0,
                    json.dumps(job.interview_answers),
                    job_id,
                ))
                conn.commit()
            finally:
                conn.close()
            
            return job

    def list_jobs(self, limit: int = 10, offset: int = 0) -> list[Job]:
        """List jobs with pagination."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            return [_row_to_job(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def delete_job(self, job_id: str) -> bool:
        """Delete a job by ID."""
        with self._lock:
            if job_id in self._active_jobs:
                del self._active_jobs[job_id]
        
        conn = self._get_conn()
        try:
            cursor = conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()


# Global job queue instance
job_queue = JobQueue()
