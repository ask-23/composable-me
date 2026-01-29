"""Test that SSE complete event contains all required fields.

Verifies the DRY helper method `get_complete_event_payload()` returns
consistent data for both live completion and reconnection scenarios.
"""

import pytest
from web.backend.services.job_queue import Job
from web.backend.models import JobState


class TestSSECompleteEventFields:
    """Test SSE complete event payload completeness."""

    def test_complete_event_payload_has_all_fields(self):
        """Ensure get_complete_event_payload returns all required fields."""
        job = Job(
            id="test-123",
            state=JobState.COMPLETED,
            success=True,
            final_documents={"resume": "test resume", "cover_letter": "test letter"},
            audit_report={"final_status": "APPROVED", "retry_count": 0},
            executive_brief={"decision": {"recommendation": "PROCEED"}},
            audit_failed=False,
            audit_error=None,
            error_message=None,
            agent_models={"gap_analysis": "claude-3-5-sonnet"},
        )

        payload = job.get_complete_event_payload()

        # All fields must be present
        required_fields = [
            "job_id",
            "success",
            "state",
            "final_documents",
            "audit_report",
            "executive_brief",
            "audit_failed",
            "audit_error",
            "error_message",
            "agent_models",
        ]

        for field in required_fields:
            assert field in payload, f"Missing field: {field}"

        # Verify field values
        assert payload["job_id"] == "test-123"
        assert payload["success"] is True
        assert payload["state"] == "completed"
        assert payload["final_documents"]["resume"] == "test resume"
        assert payload["audit_report"]["final_status"] == "APPROVED"
        assert payload["executive_brief"]["decision"]["recommendation"] == "PROCEED"
        assert payload["audit_failed"] is False
        assert payload["agent_models"]["gap_analysis"] == "claude-3-5-sonnet"

    def test_complete_event_payload_with_failed_state(self):
        """Ensure failed jobs also have all fields including error_message."""
        job = Job(
            id="test-fail-456",
            state=JobState.FAILED,
            success=False,
            error_message="Workflow crashed",
            audit_failed=True,
            audit_error="Audit timed out",
        )

        payload = job.get_complete_event_payload()

        assert payload["job_id"] == "test-fail-456"
        assert payload["success"] is False
        assert payload["state"] == "failed"
        assert payload["error_message"] == "Workflow crashed"
        assert payload["audit_failed"] is True
        assert payload["audit_error"] == "Audit timed out"

    def test_complete_event_payload_with_rejected_audit(self):
        """Ensure rejected audit jobs have correct audit_failed and audit_error."""
        job = Job(
            id="test-reject-789",
            state=JobState.COMPLETED,
            success=True,
            final_documents={"resume": "content", "cover_letter": "content"},
            audit_report={
                "final_status": "REJECTED",
                "retry_count": 2,
                "rejection_reason": "Unverified claims",
            },
            executive_brief={"decision": {"recommendation": "PROCEED_WITH_CAUTION"}},
            audit_failed=True,
            audit_error="Document failed audit after maximum retries",
        )

        payload = job.get_complete_event_payload()

        assert payload["state"] == "completed"
        assert payload["audit_failed"] is True
        assert payload["audit_error"] == "Document failed audit after maximum retries"
        assert payload["audit_report"]["final_status"] == "REJECTED"
        assert payload["executive_brief"]["decision"]["recommendation"] == "PROCEED_WITH_CAUTION"

    def test_complete_event_state_serialization(self):
        """Ensure state enum is serialized as string value."""
        job = Job(id="test-enum", state=JobState.COMPLETED)

        payload = job.get_complete_event_payload()

        # Must be string "completed", not enum or "JobState.COMPLETED"
        assert payload["state"] == "completed"
        assert isinstance(payload["state"], str)

    def test_complete_event_with_none_values(self):
        """Ensure None values are preserved (not converted to empty dicts)."""
        job = Job(
            id="test-none",
            state=JobState.COMPLETED,
            success=True,
            final_documents=None,
            audit_report=None,
            executive_brief=None,
        )

        payload = job.get_complete_event_payload()

        # None values should remain None
        assert payload["final_documents"] is None
        assert payload["audit_report"] is None
        assert payload["executive_brief"] is None
