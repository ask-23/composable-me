"""Postgres-backed persistence for Hydra core artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from psycopg.types.json import Json

from web.backend.db import get_conn


@dataclass(frozen=True)
class ArtifactWriteResult:
    db_row: dict[str, Any]
    file_path: Optional[Path]


class HydraDB:
    """Lightweight CRUD wrapper for Hydra's Postgres schema."""

    def create_job(
        self,
        *,
        company: str,
        role_title: str,
        source: Optional[str] = None,
        url: Optional[str] = None,
        location: Optional[str] = None,
        remote_policy: Optional[str] = None,
        employment_type: Optional[str] = None,
        compensation_text: Optional[str] = None,
        status: str = "new",
    ) -> dict[str, Any]:
        with get_conn() as conn:
            row = conn.execute(
                """
                INSERT INTO jobs (
                    source, url, company, role_title, location, remote_policy,
                    employment_type, compensation_text, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    source,
                    url,
                    company,
                    role_title,
                    location,
                    remote_policy,
                    employment_type,
                    compensation_text,
                    status,
                ),
            ).fetchone()
            conn.commit()
            return dict(row)

    def get_job(self, job_id: str) -> Optional[dict[str, Any]]:
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = %s", (job_id,)).fetchone()
            return dict(row) if row else None

    def create_job_description(self, *, job_id: str, jd_text: str) -> dict[str, Any]:
        with get_conn() as conn:
            row = conn.execute(
                """
                INSERT INTO job_descriptions (job_id, jd_text)
                VALUES (%s, %s)
                RETURNING *
                """,
                (job_id, jd_text),
            ).fetchone()
            conn.commit()
            return dict(row)

    def list_job_descriptions(self, job_id: str) -> list[dict[str, Any]]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM job_descriptions WHERE job_id = %s ORDER BY created_at",
                (job_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def create_run(
        self,
        *,
        job_id: str,
        model_router: Optional[dict[str, Any]] = None,
        config: Optional[dict[str, Any]] = None,
        outcome: Optional[str] = None,
    ) -> dict[str, Any]:
        with get_conn() as conn:
            row = conn.execute(
                """
                INSERT INTO runs (job_id, model_router, config, outcome)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (
                    job_id,
                    Json(model_router) if model_router is not None else None,
                    Json(config) if config is not None else None,
                    outcome,
                ),
            ).fetchone()
            conn.commit()
            return dict(row)

    def list_runs(self, job_id: str) -> list[dict[str, Any]]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM runs WHERE job_id = %s ORDER BY created_at",
                (job_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def update_run(
        self,
        *,
        run_id: str,
        model_router: Optional[dict[str, Any]] = None,
        config: Optional[dict[str, Any]] = None,
        outcome: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        with get_conn() as conn:
            row = conn.execute(
                """
                UPDATE runs
                SET model_router = %s,
                    config = %s,
                    outcome = %s
                WHERE id = %s
                RETURNING *
                """,
                (
                    Json(model_router) if model_router is not None else None,
                    Json(config) if config is not None else None,
                    outcome,
                    run_id,
                ),
            ).fetchone()
            conn.commit()
            return dict(row) if row else None

    def create_interview(
        self,
        *,
        run_id: str,
        questions: list[Any],
        answers: list[Any],
        structured_notes: dict[str, Any],
    ) -> dict[str, Any]:
        with get_conn() as conn:
            row = conn.execute(
                """
                INSERT INTO interviews (run_id, questions, answers, structured_notes)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (
                    run_id,
                    Json(questions),
                    Json(answers),
                    Json(structured_notes),
                ),
            ).fetchone()
            conn.commit()
            return dict(row)

    def list_interviews(self, run_id: str) -> list[dict[str, Any]]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM interviews WHERE run_id = %s ORDER BY created_at",
                (run_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def create_artifact(
        self,
        *,
        run_id: str,
        kind: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        with get_conn() as conn:
            row = conn.execute(
                """
                INSERT INTO artifacts (run_id, kind, content, metadata)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (
                    run_id,
                    kind,
                    content,
                    Json(metadata) if metadata is not None else None,
                ),
            ).fetchone()
            conn.commit()
            return dict(row)

    def list_artifacts(self, run_id: str) -> list[dict[str, Any]]:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM artifacts WHERE run_id = %s ORDER BY created_at",
                (run_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def write_artifact_to_disk(
        self,
        *,
        base_dir: Path,
        company: str,
        role_title: str,
        run_id: str,
        kind: str,
        content: str,
    ) -> Path:
        """Write artifact content to disk and return the file path."""
        safe_company = company.strip().replace(" ", "_")
        safe_role = role_title.strip().replace(" ", "_")
        output_dir = base_dir / safe_company / safe_role / run_id
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{kind}.md"
        path = output_dir / filename
        path.write_text(content)
        return path

    def create_artifact_with_disk_write(
        self,
        *,
        base_dir: Path,
        company: str,
        role_title: str,
        run_id: str,
        kind: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ArtifactWriteResult:
        """Write artifact to disk and persist a DB record with the path in metadata."""
        file_path = self.write_artifact_to_disk(
            base_dir=base_dir,
            company=company,
            role_title=role_title,
            run_id=run_id,
            kind=kind,
            content=content,
        )
        stored_metadata = dict(metadata or {})
        stored_metadata.setdefault("path", str(file_path))

        row = self.create_artifact(
            run_id=run_id,
            kind=kind,
            content=content,
            metadata=stored_metadata,
        )
        return ArtifactWriteResult(db_row=row, file_path=file_path)


hydra_db = HydraDB()
