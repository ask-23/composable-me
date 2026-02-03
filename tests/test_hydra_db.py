"""Tests for the Hydra database schema and CRUD operations."""

import os
import sys
import tempfile
import pytest

# Set up test database path before importing
_test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
os.environ['HYDRA_DB_PATH_V2'] = _test_db.name

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.backend.services.hydra_db import (
    HydraDatabase,
    JobRecord,
    JobDescriptionRecord,
    RunRecord,
    InterviewRecord,
    ArtifactRecord,
)


@pytest.fixture
def db():
    """Create a fresh database instance for each test."""
    # Use a temporary database file
    test_db_path = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    os.environ['HYDRA_DB_PATH_V2'] = test_db_path.name

    # Re-import to get fresh instance with new path
    from web.backend.services import hydra_db
    hydra_db.HYDRA_DB_PATH = hydra_db.Path(test_db_path.name)
    hydra_db._init_db()

    database = HydraDatabase()
    yield database

    # Cleanup
    os.unlink(test_db_path.name)


class TestJobsCRUD:
    """Tests for jobs table operations."""

    def test_create_job(self, db):
        """Test creating a job record."""
        job = db.create_job(
            source="linkedin",
            company="Acme Corp",
            role_title="Software Engineer",
            location="San Francisco, CA",
            remote_policy="hybrid",
        )

        assert job.id is not None
        assert job.source == "linkedin"
        assert job.company == "Acme Corp"
        assert job.role_title == "Software Engineer"
        assert job.created_at is not None

    def test_get_job(self, db):
        """Test retrieving a job by ID."""
        created = db.create_job(company="Test Co")
        retrieved = db.get_job(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.company == "Test Co"

    def test_get_job_not_found(self, db):
        """Test retrieving a non-existent job."""
        result = db.get_job("non-existent-id")
        assert result is None

    def test_update_job(self, db):
        """Test updating a job record."""
        job = db.create_job(company="Old Name", status="active")
        updated = db.update_job(job.id, company="New Name", status="closed")

        assert updated.company == "New Name"
        assert updated.status == "closed"

    def test_list_jobs(self, db):
        """Test listing jobs with pagination."""
        for i in range(5):
            db.create_job(company=f"Company {i}")

        jobs = db.list_jobs(limit=3)
        assert len(jobs) == 3

        all_jobs = db.list_jobs(limit=10)
        assert len(all_jobs) == 5

    def test_delete_job(self, db):
        """Test deleting a job."""
        job = db.create_job(company="To Delete")
        assert db.delete_job(job.id) is True
        assert db.get_job(job.id) is None

    def test_job_exists(self, db):
        """Test checking job existence."""
        job = db.create_job()
        assert db.job_exists(job.id) is True
        assert db.job_exists("fake-id") is False


class TestJobDescriptionsCRUD:
    """Tests for job_descriptions table operations."""

    def test_create_job_description(self, db):
        """Test creating a job description."""
        job = db.create_job(company="Test")
        desc = db.create_job_description(
            job_id=job.id,
            jd_text="This is a job description..."
        )

        assert desc.id is not None
        assert desc.job_id == job.id
        assert desc.jd_text == "This is a job description..."

    def test_create_job_description_invalid_job(self, db):
        """Test that creating a job description with invalid job_id raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            db.create_job_description(job_id="invalid-id", jd_text="test")

    def test_get_job_descriptions_by_job(self, db):
        """Test retrieving all descriptions for a job."""
        job = db.create_job()
        db.create_job_description(job_id=job.id, jd_text="Version 1")
        db.create_job_description(job_id=job.id, jd_text="Version 2")

        descriptions = db.get_job_descriptions_by_job(job.id)
        assert len(descriptions) == 2


class TestRunsCRUD:
    """Tests for runs table operations."""

    def test_create_run(self, db):
        """Test creating a run record."""
        job = db.create_job()
        run = db.create_run(
            job_id=job.id,
            model_router={"primary": "gpt-4"},
            config={"max_retries": 3},
            outcome="success"
        )

        assert run.id is not None
        assert run.job_id == job.id
        assert run.model_router == {"primary": "gpt-4"}
        assert run.outcome == "success"

    def test_create_run_invalid_job(self, db):
        """Test that creating a run with invalid job_id raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            db.create_run(job_id="invalid-id")

    def test_get_runs_by_job(self, db):
        """Test retrieving all runs for a job."""
        job = db.create_job()
        db.create_run(job_id=job.id, outcome="success")
        db.create_run(job_id=job.id, outcome="failed")

        runs = db.get_runs_by_job(job.id)
        assert len(runs) == 2

    def test_update_run(self, db):
        """Test updating a run record."""
        job = db.create_job()
        run = db.create_run(job_id=job.id, outcome="pending")
        updated = db.update_run(run.id, outcome="completed")

        assert updated.outcome == "completed"


class TestInterviewsCRUD:
    """Tests for interviews table operations."""

    def test_create_interview(self, db):
        """Test creating an interview record."""
        job = db.create_job()
        run = db.create_run(job_id=job.id)
        interview = db.create_interview(
            run_id=run.id,
            questions=["Q1", "Q2"],
            answers=["A1", "A2"],
            structured_notes={"summary": "Good candidate"}
        )

        assert interview.id is not None
        assert interview.run_id == run.id
        assert interview.questions == ["Q1", "Q2"]
        assert interview.answers == ["A1", "A2"]

    def test_create_interview_invalid_run(self, db):
        """Test that creating an interview with invalid run_id raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            db.create_interview(run_id="invalid-id")

    def test_get_interviews_by_run(self, db):
        """Test retrieving all interviews for a run."""
        job = db.create_job()
        run = db.create_run(job_id=job.id)
        db.create_interview(run_id=run.id, questions=["Q1"])
        db.create_interview(run_id=run.id, questions=["Q2"])

        interviews = db.get_interviews_by_run(run.id)
        assert len(interviews) == 2


class TestArtifactsCRUD:
    """Tests for artifacts table operations."""

    def test_create_artifact(self, db):
        """Test creating an artifact record."""
        job = db.create_job()
        run = db.create_run(job_id=job.id)
        artifact = db.create_artifact(
            run_id=run.id,
            kind="resume",
            content="# John Doe\nSoftware Engineer",
            metadata={"format": "markdown", "version": 1}
        )

        assert artifact.id is not None
        assert artifact.run_id == run.id
        assert artifact.kind == "resume"
        assert artifact.content == "# John Doe\nSoftware Engineer"

    def test_create_artifact_invalid_run(self, db):
        """Test that creating an artifact with invalid run_id raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            db.create_artifact(run_id="invalid-id", kind="resume")

    def test_get_artifacts_by_run(self, db):
        """Test retrieving all artifacts for a run."""
        job = db.create_job()
        run = db.create_run(job_id=job.id)
        db.create_artifact(run_id=run.id, kind="resume", content="Resume")
        db.create_artifact(run_id=run.id, kind="cover_letter", content="Cover")

        artifacts = db.get_artifacts_by_run(run.id)
        assert len(artifacts) == 2

    def test_get_artifacts_by_kind(self, db):
        """Test retrieving artifacts filtered by kind."""
        job = db.create_job()
        run = db.create_run(job_id=job.id)
        db.create_artifact(run_id=run.id, kind="resume", content="R1")
        db.create_artifact(run_id=run.id, kind="resume", content="R2")
        db.create_artifact(run_id=run.id, kind="cover_letter", content="CL")

        resumes = db.get_artifacts_by_kind("resume")
        assert len(resumes) == 2

        cover_letters = db.get_artifacts_by_kind("cover_letter")
        assert len(cover_letters) == 1


class TestDatabaseStats:
    """Tests for database utility methods."""

    def test_count_methods(self, db):
        """Test count methods for tables."""
        assert db.count_jobs() == 0

        job = db.create_job()
        assert db.count_jobs() == 1

        run = db.create_run(job_id=job.id)
        assert db.count_runs() == 1

        db.create_artifact(run_id=run.id, kind="resume")
        assert db.count_artifacts() == 1

    def test_get_database_stats(self, db):
        """Test getting stats for all tables."""
        job = db.create_job()
        db.create_job_description(job_id=job.id, jd_text="Test")
        run = db.create_run(job_id=job.id)
        db.create_interview(run_id=run.id)
        db.create_artifact(run_id=run.id, kind="resume")

        stats = db.get_database_stats()

        assert stats['jobs'] == 1
        assert stats['job_descriptions'] == 1
        assert stats['runs'] == 1
        assert stats['interviews'] == 1
        assert stats['artifacts'] == 1


class TestNullHandling:
    """Tests for proper NULL handling (store missing data as NULL)."""

    def test_create_job_with_nulls(self, db):
        """Test that missing fields are stored as NULL, not guessed."""
        job = db.create_job()  # No fields provided

        retrieved = db.get_job(job.id)
        assert retrieved.source is None
        assert retrieved.company is None
        assert retrieved.role_title is None
        assert retrieved.url is None

    def test_create_run_with_nulls(self, db):
        """Test that missing run fields are stored as NULL."""
        job = db.create_job()
        run = db.create_run(job_id=job.id)  # Minimal fields

        retrieved = db.get_run(run.id)
        assert retrieved.model_router is None
        assert retrieved.config is None
        assert retrieved.outcome is None

    def test_create_artifact_with_nulls(self, db):
        """Test that missing artifact fields are stored as NULL."""
        job = db.create_job()
        run = db.create_run(job_id=job.id)
        artifact = db.create_artifact(run_id=run.id)  # Minimal

        retrieved = db.get_artifact(artifact.id)
        assert retrieved.kind is None
        assert retrieved.content is None
        assert retrieved.metadata is None
