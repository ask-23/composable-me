"""SQLite-backed persistent database for Hydra.

This module provides a normalized schema for storing:
- Jobs (job listings)
- Job descriptions (full JD text linked to jobs)
- Runs (pipeline execution records linked to jobs)
- Interviews (Q&A linked to runs)
- Artifacts (generated outputs linked to runs)

All operations follow strict data integrity rules:
- Never fabricate field values
- Never overwrite existing records unless explicitly told
- Store missing data as NULL, do not guess
- Reads reflect stored data exactly
"""

import json
import os
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Literal, Optional


# Database path - uses same data directory as job_queue
_DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "hydra.db"
HYDRA_DB_PATH = Path(os.environ.get("HYDRA_DB_PATH_V2", str(_DEFAULT_DB_PATH)))


def _ensure_db_dir():
    """Ensure the data directory exists."""
    HYDRA_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _init_db():
    """Initialize the database schema if needed."""
    _ensure_db_dir()
    conn = sqlite3.connect(str(HYDRA_DB_PATH))

    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys = ON")

    # Jobs table - stores job listing metadata
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            source TEXT,
            url TEXT,
            company TEXT,
            role_title TEXT,
            location TEXT,
            remote_policy TEXT,
            employment_type TEXT,
            compensation_text TEXT,
            status TEXT
        )
    """)

    # Job descriptions table - stores full JD text linked to jobs
    conn.execute("""
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            jd_text TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)

    # Runs table - stores pipeline execution records
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            model_router TEXT,
            config TEXT,
            outcome TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)

    # Interviews table - stores interview Q&A linked to runs
    conn.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            questions TEXT,
            answers TEXT,
            structured_notes TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
    """)

    # Artifacts table - stores generated outputs linked to runs
    conn.execute("""
        CREATE TABLE IF NOT EXISTS artifacts (
            id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            kind TEXT,
            content TEXT,
            metadata TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
    """)

    # Create indexes for common lookups
    conn.execute("CREATE INDEX IF NOT EXISTS idx_job_descriptions_job_id ON job_descriptions(job_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_job_id ON runs(job_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_interviews_run_id ON interviews(run_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_run_id ON artifacts(run_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_kind ON artifacts(kind)")

    conn.commit()
    conn.close()


# Initialize DB on module load
_init_db()


# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------

@dataclass
class JobRecord:
    """Represents a job listing."""
    id: str
    created_at: datetime
    source: Optional[str] = None
    url: Optional[str] = None
    company: Optional[str] = None
    role_title: Optional[str] = None
    location: Optional[str] = None
    remote_policy: Optional[str] = None
    employment_type: Optional[str] = None
    compensation_text: Optional[str] = None
    status: Optional[str] = None


@dataclass
class JobDescriptionRecord:
    """Represents a job description linked to a job."""
    id: str
    job_id: str
    created_at: datetime
    jd_text: Optional[str] = None


@dataclass
class RunRecord:
    """Represents a pipeline execution run."""
    id: str
    job_id: str
    created_at: datetime
    model_router: Optional[dict[str, Any]] = None
    config: Optional[dict[str, Any]] = None
    outcome: Optional[str] = None


@dataclass
class InterviewRecord:
    """Represents interview questions and answers."""
    id: str
    run_id: str
    created_at: datetime
    questions: Optional[list[Any]] = None
    answers: Optional[list[Any]] = None
    structured_notes: Optional[dict[str, Any]] = None


# Valid artifact kinds
ArtifactKind = Literal["resume", "cover_letter", "audit_report", "recruiter_reply"]


@dataclass
class ArtifactRecord:
    """Represents a generated artifact."""
    id: str
    run_id: str
    created_at: datetime
    kind: Optional[ArtifactKind] = None
    content: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


# -----------------------------------------------------------------------------
# Serialization Helpers
# -----------------------------------------------------------------------------

def _serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO string for storage."""
    return dt.isoformat() if dt else None


def _deserialize_datetime(s: Optional[str]) -> Optional[datetime]:
    """Convert ISO string back to datetime."""
    return datetime.fromisoformat(s) if s else None


def _serialize_json(obj: Any) -> Optional[str]:
    """Convert object to JSON string for storage."""
    return json.dumps(obj) if obj is not None else None


def _deserialize_json(s: Optional[str]) -> Optional[Any]:
    """Convert JSON string back to object."""
    return json.loads(s) if s else None


def _generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


# -----------------------------------------------------------------------------
# Database Service
# -----------------------------------------------------------------------------

class HydraDatabase:
    """Thread-safe SQLite-backed storage for Hydra data.

    Behavior rules:
    - Only write records when explicitly instructed
    - Never fabricate field values
    - Never overwrite existing records unless explicitly told to update
    - If a referenced job_id or run_id does not exist, raise an error
    - Store missing data as NULL, do not guess
    - Reads reflect stored data exactly
    """

    def __init__(self):
        self._lock = Lock()

    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection with foreign keys enabled."""
        conn = sqlite3.connect(str(HYDRA_DB_PATH))
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # -------------------------------------------------------------------------
    # Jobs CRUD
    # -------------------------------------------------------------------------

    def create_job(
        self,
        source: Optional[str] = None,
        url: Optional[str] = None,
        company: Optional[str] = None,
        role_title: Optional[str] = None,
        location: Optional[str] = None,
        remote_policy: Optional[str] = None,
        employment_type: Optional[str] = None,
        compensation_text: Optional[str] = None,
        status: Optional[str] = None,
    ) -> JobRecord:
        """Create and store a new job record."""
        job_id = _generate_uuid()
        created_at = datetime.now()

        job = JobRecord(
            id=job_id,
            created_at=created_at,
            source=source,
            url=url,
            company=company,
            role_title=role_title,
            location=location,
            remote_policy=remote_policy,
            employment_type=employment_type,
            compensation_text=compensation_text,
            status=status,
        )

        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    INSERT INTO jobs (
                        id, created_at, source, url, company, role_title,
                        location, remote_policy, employment_type,
                        compensation_text, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job.id,
                    _serialize_datetime(job.created_at),
                    job.source,
                    job.url,
                    job.company,
                    job.role_title,
                    job.location,
                    job.remote_policy,
                    job.employment_type,
                    job.compensation_text,
                    job.status,
                ))
                conn.commit()
            finally:
                conn.close()

        return job

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        """Get a job by ID. Returns None if not found."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                return JobRecord(
                    id=row[0],
                    created_at=_deserialize_datetime(row[1]) or datetime.now(),
                    source=row[2],
                    url=row[3],
                    company=row[4],
                    role_title=row[5],
                    location=row[6],
                    remote_policy=row[7],
                    employment_type=row[8],
                    compensation_text=row[9],
                    status=row[10],
                )
            return None
        finally:
            conn.close()

    def update_job(self, job_id: str, **kwargs) -> Optional[JobRecord]:
        """Update a job record. Only updates provided fields."""
        with self._lock:
            job = self.get_job(job_id)
            if not job:
                return None

            # Only update provided fields
            allowed_fields = {
                'source', 'url', 'company', 'role_title', 'location',
                'remote_policy', 'employment_type', 'compensation_text', 'status'
            }

            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
            if not updates:
                return job

            set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
            values = list(updates.values()) + [job_id]

            conn = self._get_conn()
            try:
                conn.execute(f"UPDATE jobs SET {set_clause} WHERE id = ?", values)
                conn.commit()
            finally:
                conn.close()

            return self.get_job(job_id)

    def list_jobs(self, limit: int = 100, offset: int = 0) -> list[JobRecord]:
        """List jobs with pagination, ordered by created_at DESC."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            jobs = []
            for row in cursor.fetchall():
                jobs.append(JobRecord(
                    id=row[0],
                    created_at=_deserialize_datetime(row[1]) or datetime.now(),
                    source=row[2],
                    url=row[3],
                    company=row[4],
                    role_title=row[5],
                    location=row[6],
                    remote_policy=row[7],
                    employment_type=row[8],
                    compensation_text=row[9],
                    status=row[10],
                ))
            return jobs
        finally:
            conn.close()

    def delete_job(self, job_id: str) -> bool:
        """Delete a job by ID. Returns True if deleted."""
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()

    def job_exists(self, job_id: str) -> bool:
        """Check if a job exists."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT 1 FROM jobs WHERE id = ?", (job_id,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Job Descriptions CRUD
    # -------------------------------------------------------------------------

    def create_job_description(
        self,
        job_id: str,
        jd_text: Optional[str] = None,
    ) -> JobDescriptionRecord:
        """Create and store a new job description.

        Raises ValueError if job_id does not exist.
        """
        if not self.job_exists(job_id):
            raise ValueError(f"Job with id '{job_id}' does not exist. Cannot create job_description.")

        desc_id = _generate_uuid()
        created_at = datetime.now()

        record = JobDescriptionRecord(
            id=desc_id,
            job_id=job_id,
            created_at=created_at,
            jd_text=jd_text,
        )

        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    INSERT INTO job_descriptions (id, job_id, created_at, jd_text)
                    VALUES (?, ?, ?, ?)
                """, (
                    record.id,
                    record.job_id,
                    _serialize_datetime(record.created_at),
                    record.jd_text,
                ))
                conn.commit()
            finally:
                conn.close()

        return record

    def get_job_description(self, desc_id: str) -> Optional[JobDescriptionRecord]:
        """Get a job description by ID."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT * FROM job_descriptions WHERE id = ?", (desc_id,))
            row = cursor.fetchone()
            if row:
                return JobDescriptionRecord(
                    id=row[0],
                    job_id=row[1],
                    created_at=_deserialize_datetime(row[2]) or datetime.now(),
                    jd_text=row[3],
                )
            return None
        finally:
            conn.close()

    def get_job_descriptions_by_job(self, job_id: str) -> list[JobDescriptionRecord]:
        """Get all job descriptions for a job."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT * FROM job_descriptions WHERE job_id = ? ORDER BY created_at DESC",
                (job_id,)
            )
            records = []
            for row in cursor.fetchall():
                records.append(JobDescriptionRecord(
                    id=row[0],
                    job_id=row[1],
                    created_at=_deserialize_datetime(row[2]) or datetime.now(),
                    jd_text=row[3],
                ))
            return records
        finally:
            conn.close()

    def update_job_description(self, desc_id: str, jd_text: str) -> Optional[JobDescriptionRecord]:
        """Update a job description's text."""
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "UPDATE job_descriptions SET jd_text = ? WHERE id = ?",
                    (jd_text, desc_id)
                )
                conn.commit()
            finally:
                conn.close()

        return self.get_job_description(desc_id)

    def delete_job_description(self, desc_id: str) -> bool:
        """Delete a job description by ID."""
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.execute("DELETE FROM job_descriptions WHERE id = ?", (desc_id,))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()

    # -------------------------------------------------------------------------
    # Runs CRUD
    # -------------------------------------------------------------------------

    def create_run(
        self,
        job_id: str,
        model_router: Optional[dict[str, Any]] = None,
        config: Optional[dict[str, Any]] = None,
        outcome: Optional[str] = None,
    ) -> RunRecord:
        """Create and store a new run record.

        Raises ValueError if job_id does not exist.
        """
        if not self.job_exists(job_id):
            raise ValueError(f"Job with id '{job_id}' does not exist. Cannot create run.")

        run_id = _generate_uuid()
        created_at = datetime.now()

        record = RunRecord(
            id=run_id,
            job_id=job_id,
            created_at=created_at,
            model_router=model_router,
            config=config,
            outcome=outcome,
        )

        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    INSERT INTO runs (id, job_id, created_at, model_router, config, outcome)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    record.id,
                    record.job_id,
                    _serialize_datetime(record.created_at),
                    _serialize_json(record.model_router),
                    _serialize_json(record.config),
                    record.outcome,
                ))
                conn.commit()
            finally:
                conn.close()

        return record

    def get_run(self, run_id: str) -> Optional[RunRecord]:
        """Get a run by ID."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
            row = cursor.fetchone()
            if row:
                return RunRecord(
                    id=row[0],
                    job_id=row[1],
                    created_at=_deserialize_datetime(row[2]) or datetime.now(),
                    model_router=_deserialize_json(row[3]),
                    config=_deserialize_json(row[4]),
                    outcome=row[5],
                )
            return None
        finally:
            conn.close()

    def get_runs_by_job(self, job_id: str) -> list[RunRecord]:
        """Get all runs for a job."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT * FROM runs WHERE job_id = ? ORDER BY created_at DESC",
                (job_id,)
            )
            records = []
            for row in cursor.fetchall():
                records.append(RunRecord(
                    id=row[0],
                    job_id=row[1],
                    created_at=_deserialize_datetime(row[2]) or datetime.now(),
                    model_router=_deserialize_json(row[3]),
                    config=_deserialize_json(row[4]),
                    outcome=row[5],
                ))
            return records
        finally:
            conn.close()

    def update_run(self, run_id: str, **kwargs) -> Optional[RunRecord]:
        """Update a run record. Only updates provided fields."""
        with self._lock:
            run = self.get_run(run_id)
            if not run:
                return None

            allowed_fields = {'model_router', 'config', 'outcome'}
            updates = {}

            for k, v in kwargs.items():
                if k in allowed_fields:
                    if k in ('model_router', 'config'):
                        updates[k] = _serialize_json(v)
                    else:
                        updates[k] = v

            if not updates:
                return run

            set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
            values = list(updates.values()) + [run_id]

            conn = self._get_conn()
            try:
                conn.execute(f"UPDATE runs SET {set_clause} WHERE id = ?", values)
                conn.commit()
            finally:
                conn.close()

            return self.get_run(run_id)

    def delete_run(self, run_id: str) -> bool:
        """Delete a run by ID."""
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()

    def run_exists(self, run_id: str) -> bool:
        """Check if a run exists."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT 1 FROM runs WHERE id = ?", (run_id,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def list_runs(self, limit: int = 100, offset: int = 0) -> list[RunRecord]:
        """List runs with pagination, ordered by created_at DESC."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT * FROM runs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            records = []
            for row in cursor.fetchall():
                records.append(RunRecord(
                    id=row[0],
                    job_id=row[1],
                    created_at=_deserialize_datetime(row[2]) or datetime.now(),
                    model_router=_deserialize_json(row[3]),
                    config=_deserialize_json(row[4]),
                    outcome=row[5],
                ))
            return records
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Interviews CRUD
    # -------------------------------------------------------------------------

    def create_interview(
        self,
        run_id: str,
        questions: Optional[list[Any]] = None,
        answers: Optional[list[Any]] = None,
        structured_notes: Optional[dict[str, Any]] = None,
    ) -> InterviewRecord:
        """Create and store a new interview record.

        Raises ValueError if run_id does not exist.
        """
        if not self.run_exists(run_id):
            raise ValueError(f"Run with id '{run_id}' does not exist. Cannot create interview.")

        interview_id = _generate_uuid()
        created_at = datetime.now()

        record = InterviewRecord(
            id=interview_id,
            run_id=run_id,
            created_at=created_at,
            questions=questions,
            answers=answers,
            structured_notes=structured_notes,
        )

        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    INSERT INTO interviews (id, run_id, created_at, questions, answers, structured_notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    record.id,
                    record.run_id,
                    _serialize_datetime(record.created_at),
                    _serialize_json(record.questions),
                    _serialize_json(record.answers),
                    _serialize_json(record.structured_notes),
                ))
                conn.commit()
            finally:
                conn.close()

        return record

    def get_interview(self, interview_id: str) -> Optional[InterviewRecord]:
        """Get an interview by ID."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT * FROM interviews WHERE id = ?", (interview_id,))
            row = cursor.fetchone()
            if row:
                return InterviewRecord(
                    id=row[0],
                    run_id=row[1],
                    created_at=_deserialize_datetime(row[2]) or datetime.now(),
                    questions=_deserialize_json(row[3]),
                    answers=_deserialize_json(row[4]),
                    structured_notes=_deserialize_json(row[5]),
                )
            return None
        finally:
            conn.close()

    def get_interviews_by_run(self, run_id: str) -> list[InterviewRecord]:
        """Get all interviews for a run."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT * FROM interviews WHERE run_id = ? ORDER BY created_at DESC",
                (run_id,)
            )
            records = []
            for row in cursor.fetchall():
                records.append(InterviewRecord(
                    id=row[0],
                    run_id=row[1],
                    created_at=_deserialize_datetime(row[2]) or datetime.now(),
                    questions=_deserialize_json(row[3]),
                    answers=_deserialize_json(row[4]),
                    structured_notes=_deserialize_json(row[5]),
                ))
            return records
        finally:
            conn.close()

    def update_interview(self, interview_id: str, **kwargs) -> Optional[InterviewRecord]:
        """Update an interview record. Only updates provided fields."""
        with self._lock:
            interview = self.get_interview(interview_id)
            if not interview:
                return None

            allowed_fields = {'questions', 'answers', 'structured_notes'}
            updates = {}

            for k, v in kwargs.items():
                if k in allowed_fields:
                    updates[k] = _serialize_json(v)

            if not updates:
                return interview

            set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
            values = list(updates.values()) + [interview_id]

            conn = self._get_conn()
            try:
                conn.execute(f"UPDATE interviews SET {set_clause} WHERE id = ?", values)
                conn.commit()
            finally:
                conn.close()

            return self.get_interview(interview_id)

    def delete_interview(self, interview_id: str) -> bool:
        """Delete an interview by ID."""
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.execute("DELETE FROM interviews WHERE id = ?", (interview_id,))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()

    def list_interviews(self, limit: int = 100, offset: int = 0) -> list[InterviewRecord]:
        """List interviews with pagination, ordered by created_at DESC."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT * FROM interviews ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            records = []
            for row in cursor.fetchall():
                records.append(InterviewRecord(
                    id=row[0],
                    run_id=row[1],
                    created_at=_deserialize_datetime(row[2]) or datetime.now(),
                    questions=_deserialize_json(row[3]),
                    answers=_deserialize_json(row[4]),
                    structured_notes=_deserialize_json(row[5]),
                ))
            return records
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Artifacts CRUD
    # -------------------------------------------------------------------------

    def create_artifact(
        self,
        run_id: str,
        kind: Optional[ArtifactKind] = None,
        content: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ArtifactRecord:
        """Create and store a new artifact record.

        Raises ValueError if run_id does not exist.

        Valid kinds: resume, cover_letter, audit_report, recruiter_reply
        """
        if not self.run_exists(run_id):
            raise ValueError(f"Run with id '{run_id}' does not exist. Cannot create artifact.")

        artifact_id = _generate_uuid()
        created_at = datetime.now()

        record = ArtifactRecord(
            id=artifact_id,
            run_id=run_id,
            created_at=created_at,
            kind=kind,
            content=content,
            metadata=metadata,
        )

        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    INSERT INTO artifacts (id, run_id, created_at, kind, content, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    record.id,
                    record.run_id,
                    _serialize_datetime(record.created_at),
                    record.kind,
                    record.content,
                    _serialize_json(record.metadata),
                ))
                conn.commit()
            finally:
                conn.close()

        return record

    def get_artifact(self, artifact_id: str) -> Optional[ArtifactRecord]:
        """Get an artifact by ID."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,))
            row = cursor.fetchone()
            if row:
                return ArtifactRecord(
                    id=row[0],
                    run_id=row[1],
                    created_at=_deserialize_datetime(row[2]) or datetime.now(),
                    kind=row[3],
                    content=row[4],
                    metadata=_deserialize_json(row[5]),
                )
            return None
        finally:
            conn.close()

    def get_artifacts_by_run(self, run_id: str) -> list[ArtifactRecord]:
        """Get all artifacts for a run."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT * FROM artifacts WHERE run_id = ? ORDER BY created_at DESC",
                (run_id,)
            )
            records = []
            for row in cursor.fetchall():
                records.append(ArtifactRecord(
                    id=row[0],
                    run_id=row[1],
                    created_at=_deserialize_datetime(row[2]) or datetime.now(),
                    kind=row[3],
                    content=row[4],
                    metadata=_deserialize_json(row[5]),
                ))
            return records
        finally:
            conn.close()

    def get_artifacts_by_kind(self, kind: ArtifactKind, limit: int = 100) -> list[ArtifactRecord]:
        """Get artifacts filtered by kind."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT * FROM artifacts WHERE kind = ? ORDER BY created_at DESC LIMIT ?",
                (kind, limit)
            )
            records = []
            for row in cursor.fetchall():
                records.append(ArtifactRecord(
                    id=row[0],
                    run_id=row[1],
                    created_at=_deserialize_datetime(row[2]) or datetime.now(),
                    kind=row[3],
                    content=row[4],
                    metadata=_deserialize_json(row[5]),
                ))
            return records
        finally:
            conn.close()

    def update_artifact(self, artifact_id: str, **kwargs) -> Optional[ArtifactRecord]:
        """Update an artifact record. Only updates provided fields."""
        with self._lock:
            artifact = self.get_artifact(artifact_id)
            if not artifact:
                return None

            allowed_fields = {'kind', 'content', 'metadata'}
            updates = {}

            for k, v in kwargs.items():
                if k in allowed_fields:
                    if k == 'metadata':
                        updates[k] = _serialize_json(v)
                    else:
                        updates[k] = v

            if not updates:
                return artifact

            set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
            values = list(updates.values()) + [artifact_id]

            conn = self._get_conn()
            try:
                conn.execute(f"UPDATE artifacts SET {set_clause} WHERE id = ?", values)
                conn.commit()
            finally:
                conn.close()

            return self.get_artifact(artifact_id)

    def delete_artifact(self, artifact_id: str) -> bool:
        """Delete an artifact by ID."""
        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.execute("DELETE FROM artifacts WHERE id = ?", (artifact_id,))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()

    def list_artifacts(self, limit: int = 100, offset: int = 0) -> list[ArtifactRecord]:
        """List artifacts with pagination, ordered by created_at DESC."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "SELECT * FROM artifacts ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            records = []
            for row in cursor.fetchall():
                records.append(ArtifactRecord(
                    id=row[0],
                    run_id=row[1],
                    created_at=_deserialize_datetime(row[2]) or datetime.now(),
                    kind=row[3],
                    content=row[4],
                    metadata=_deserialize_json(row[5]),
                ))
            return records
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def count_jobs(self) -> int:
        """Count total number of jobs."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM jobs")
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def count_runs(self) -> int:
        """Count total number of runs."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM runs")
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def count_artifacts(self) -> int:
        """Count total number of artifacts."""
        conn = self._get_conn()
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM artifacts")
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_database_stats(self) -> dict[str, int]:
        """Get counts for all tables."""
        conn = self._get_conn()
        try:
            stats = {}
            for table in ['jobs', 'job_descriptions', 'runs', 'interviews', 'artifacts']:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            return stats
        finally:
            conn.close()


# Global database instance
hydra_db = HydraDatabase()
