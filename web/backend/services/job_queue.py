"""In-memory job queue for tracking workflow execution."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from threading import Lock
import uuid
import asyncio

from web.backend.models import JobState


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

    # For SSE updates
    _event_queue: asyncio.Queue = field(default_factory=asyncio.Queue, repr=False)

    def get_progress_percent(self) -> int:
        """Calculate progress percentage based on current state."""
        stage_progress = {
            JobState.INITIALIZED: 0,
            JobState.GAP_ANALYSIS: 15,
            JobState.INTERROGATION: 30,
            JobState.DIFFERENTIATION: 45,
            JobState.TAILORING: 60,
            JobState.ATS_OPTIMIZATION: 75,
            JobState.AUDITING: 90,
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


class JobQueue:
    """Thread-safe in-memory job storage."""

    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = Lock()

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
            self._jobs[job_id] = job

        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        with self._lock:
            return self._jobs.get(job_id)

    def update_job(self, job_id: str, **kwargs) -> Optional[Job]:
        """Update job fields."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                for key, value in kwargs.items():
                    if hasattr(job, key):
                        setattr(job, key, value)
            return job

    def list_jobs(self, limit: int = 10, offset: int = 0) -> list[Job]:
        """List jobs with pagination."""
        with self._lock:
            jobs = sorted(
                self._jobs.values(),
                key=lambda j: j.created_at,
                reverse=True
            )
            return jobs[offset:offset + limit]

    def delete_job(self, job_id: str) -> bool:
        """Delete a job by ID."""
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
            return False


# Global job queue instance
job_queue = JobQueue()
