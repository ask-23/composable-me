"""Pydantic models for the Hydra web API."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class JobState(str, Enum):
    """Job execution states matching HydraWorkflow states."""
    INITIALIZED = "initialized"
    GAP_ANALYSIS = "gap_analysis"
    INTERROGATION = "interrogation"
    DIFFERENTIATION = "differentiation"
    TAILORING = "tailoring"
    ATS_OPTIMIZATION = "ats_optimization"
    AUDITING = "auditing"
    COMPLETED = "completed"
    FAILED = "failed"


class AuditStatus(str, Enum):
    """Audit result status."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    AUDIT_CRASHED = "AUDIT_CRASHED"


class CreateJobRequest(BaseModel):
    """Request to create a new job."""
    job_description: str = Field(..., min_length=10, description="Job description text")
    resume: str = Field(..., min_length=10, description="Resume text")
    source_documents: str = Field(default="", description="Supporting documents")
    model: Optional[str] = Field(default=None, description="LLM model override")
    max_audit_retries: int = Field(default=2, ge=0, le=5, description="Max audit retries")


class CreateJobResponse(BaseModel):
    """Response after creating a job."""
    job_id: str
    status: str = "queued"
    created_at: datetime


class FinalDocuments(BaseModel):
    """Final generated documents."""
    resume: str = ""
    cover_letter: str = ""


class AuditReport(BaseModel):
    """Audit report structure."""
    resume_audit: Optional[dict[str, Any]] = None
    cover_letter_audit: Optional[dict[str, Any]] = None
    final_status: Optional[AuditStatus] = None
    retry_count: int = 0
    rejection_reason: Optional[str] = None
    crash_error: Optional[str] = None


class JobResponse(BaseModel):
    """Full job status response."""
    job_id: str
    state: JobState
    success: bool
    progress_percent: int = 0
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    final_documents: Optional[FinalDocuments] = None
    audit_report: Optional[AuditReport] = None
    intermediate_results: Optional[dict[str, Any]] = None
    execution_log: list[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    audit_failed: bool = False
    audit_error: Optional[str] = None
    agent_models: Optional[dict[str, str]] = Field(default=None, description="Models used by each agent")


class SSEEvent(BaseModel):
    """Server-Sent Event payload."""
    event: str
    data: dict[str, Any]
