"""
Integration tests for the full Hydra workflow using the real agent stack.

These tests call the actual HydraWorkflow and require a live OpenRouter API key.
Set OPENROUTER_API_KEY before running to enable them.
"""

import os
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from runtime.crewai.hydra_workflow import HydraWorkflow, ValidationError
from runtime.crewai.llm_client import get_llm_client, LLMClientError


requires_api_key = pytest.mark.skipif(
    not (os.environ.get("OPENROUTER_API_KEY") or os.environ.get("TOGETHER_API_KEY") or os.environ.get("CHUTES_API_KEY")),
    reason="API key not set (OPENROUTER_API_KEY, TOGETHER_API_KEY, or CHUTES_API_KEY required)",
)


def _load_examples():
    """Load sample JD and resume text from examples/."""
    root = Path(__file__).resolve().parents[2]
    jd_path = root / "examples" / "sample_jd.md"
    resume_path = root / "examples" / "sample_resume.md"

    return jd_path.read_text(), resume_path.read_text()


@requires_api_key
def test_full_workflow_happy_path_live():
    """Happy path: run full workflow and expect approved documents."""
    jd_text, resume_text = _load_examples()

    llm = get_llm_client()
    workflow = HydraWorkflow(llm)

    context = {
        "job_description": jd_text,
        "resume": resume_text,
        "source_documents": resume_text,
        "target_role": "Sample Role",
    }

    result = workflow.execute(context)

    assert result.success, f"Workflow failed: {result.error_message}"
    assert result.final_documents is not None
    assert result.final_documents.get("resume")
    assert result.final_documents.get("cover_letter")
    assert result.audit_report is not None
    assert result.audit_report.get("final_status") == "APPROVED"


@requires_api_key
def test_full_workflow_reports_retry_information():
    """Workflow should surface audit retry information when present."""
    jd_text, resume_text = _load_examples()

    llm = get_llm_client()
    workflow = HydraWorkflow(llm, max_audit_retries=2)

    context = {
        "job_description": jd_text,
        "resume": resume_text,
        "source_documents": resume_text,
        "target_role": "Sample Role",
    }

    result = workflow.execute(context)

    if result.success:
        retry_count = result.audit_report.get("retry_count", 0)
        assert 0 <= retry_count <= workflow.max_audit_retries
    else:
        # If the live LLM returns an unfixable output, ensure we see a clear error
        assert "failed" in (result.error_message or "").lower()


def test_full_workflow_handles_missing_context_gracefully():
    """Workflow should error cleanly when required context keys are absent."""
    workflow = HydraWorkflow(llm=None)

    bad_context = {
        "job_description": "JD only",
        # resume missing
        "source_documents": "",
    }

    result = workflow.execute(bad_context)

    assert result.success is False
    assert result.state.value == "failed"
    assert "resume" in (result.error_message or "")
