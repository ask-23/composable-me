"""
Integration tests for multi-component interactions in Composable Me.

These tests exercise real state machines and data model logic with mocked
agent executions (no real LLM or database calls). The goal is to verify
cross-component data flow, state transitions, error propagation, and
output integrity.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
import yaml

from runtime.crewai.base_agent import ValidationError
from runtime.crewai.hydra_workflow import (
    HydraWorkflow,
    WorkflowPaused,
    WorkflowResult,
    WorkflowState as HydraWorkflowState,
)
from runtime.crewai.models import (
    AgentExecution,
    AuditIssue,
    Classification,
    ClassificationType,
    Differentiator,
    Employment,
    IssueSeverity,
    JobDescription,
    Requirement,
    RequirementPriority,
    RequirementType,
    Resume,
    WorkflowState,
    WorkflowStatus,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _agent_patches():
    """Context manager that patches all agent constructors."""
    return (
        patch("runtime.crewai.hydra_workflow.GapAnalyzerAgent"),
        patch("runtime.crewai.hydra_workflow.InterrogatorPrepperAgent"),
        patch("runtime.crewai.hydra_workflow.DifferentiatorAgent"),
        patch("runtime.crewai.hydra_workflow.TailoringAgent"),
        patch("runtime.crewai.hydra_workflow.ATSOptimizerAgent"),
        patch("runtime.crewai.hydra_workflow.AuditorSuiteAgent"),
        patch("runtime.crewai.hydra_workflow.ExecutiveSynthesizerAgent"),
    )


def _make_workflow(**kwargs) -> HydraWorkflow:
    """Create a HydraWorkflow with all agent constructors mocked."""
    patches = _agent_patches()
    for p in patches:
        p.start()
    mock_llm = Mock()
    mock_llm.model = "test-model"
    defaults = {"use_per_agent_models": False}
    defaults.update(kwargs)
    workflow = HydraWorkflow(mock_llm, **defaults)
    for p in patches:
        p.stop()
    return workflow


def _base_context(**overrides) -> Dict[str, Any]:
    """Return a minimal valid workflow context with optional overrides."""
    ctx = {
        "job_description": "Senior Platform Engineer requiring AWS, Python, Terraform",
        "resume": "10 years experience with AWS, Python, and infrastructure automation",
        "source_documents": "Original resume with verified experience at Acme Corp",
        "target_role": "Senior Platform Engineer",
        "gap_analysis_approved": True,
        "interview_answers": [
            {"question": "Describe your AWS experience", "answer": "5 years production AWS"}
        ],
    }
    ctx.update(overrides)
    return ctx


def _gap_result(**overrides) -> Dict[str, Any]:
    result = {
        "agent": "Gap Analyzer",
        "timestamp": "2025-12-06T18:45:00Z",
        "confidence": 0.92,
        "gaps": [
            {"skill": "Terraform modules", "severity": "medium"},
            {"skill": "Kubernetes", "severity": "low"},
        ],
        "requirements_analysis": {"direct_matches": 5, "gaps": 2},
    }
    result.update(overrides)
    return result


def _interrogation_result(**overrides) -> Dict[str, Any]:
    result = {
        "agent": "Interrogator-Prepper",
        "timestamp": "2025-12-06T18:46:00Z",
        "confidence": 0.90,
        "questions": [
            {"id": "q1", "question": "Describe Terraform module usage"},
            {"id": "q2", "question": "Kubernetes orchestration experience"},
        ],
        "interview_notes": [
            {"question_id": "q1", "answer": "Built reusable modules for 3 teams"}
        ],
    }
    result.update(overrides)
    return result


def _differentiation_result(**overrides) -> Dict[str, Any]:
    result = {
        "agent": "Differentiator",
        "timestamp": "2025-12-06T18:47:00Z",
        "confidence": 0.88,
        "differentiators": [
            {"hook": "Platform reliability", "evidence": "99.99% uptime", "score": 0.95},
            {"hook": "Cost optimization", "evidence": "Saved $2M annually", "score": 0.90},
        ],
    }
    result.update(overrides)
    return result


def _tailoring_result(**overrides) -> Dict[str, Any]:
    result = {
        "agent": "Tailoring Agent",
        "timestamp": "2025-12-06T18:48:00Z",
        "confidence": 0.93,
        "tailored_output": {
            "resume": {"content": "# John Doe\n\nSenior Platform Engineer with 10 years..."},
            "cover_letter": {"content": "Dear Hiring Manager,\n\nI am writing to apply..."},
        },
    }
    result.update(overrides)
    return result


def _ats_result(**overrides) -> Dict[str, Any]:
    result = {
        "agent": "ATS Optimizer",
        "timestamp": "2025-12-06T18:49:00Z",
        "confidence": 0.95,
        "ats_report": {
            "ats_score": 92,
            "optimized_resume": "# John Doe\n\nATS-optimized resume content...",
            "optimized_cover_letter": "ATS-optimized cover letter content...",
            "keyword_matches": ["AWS", "Python", "Terraform"],
        },
    }
    result.update(overrides)
    return result


def _audit_approved(**overrides) -> Dict[str, Any]:
    result = {
        "agent": "Auditor Suite",
        "timestamp": "2025-12-06T18:50:00Z",
        "confidence": 0.98,
        "approval": {"approved": True, "reason": "All checks passed"},
        "issues": [],
    }
    result.update(overrides)
    return result


def _audit_rejected(**overrides) -> Dict[str, Any]:
    result = {
        "agent": "Auditor Suite",
        "timestamp": "2025-12-06T18:50:00Z",
        "confidence": 0.80,
        "approval": {"approved": False, "reason": "Truth violation detected"},
        "issues": [{"type": "truth", "severity": "blocking", "description": "Unverified claim"}],
    }
    result.update(overrides)
    return result


def _executive_brief(**overrides) -> Dict[str, Any]:
    result = {
        "agent": "Executive Synthesizer",
        "timestamp": "2025-12-06T18:51:00Z",
        "confidence": 0.91,
        "decision": {
            "recommendation": "STRONG_APPLY",
            "fit_score": 87,
            "rationale": "Strong alignment with 8 of 10 requirements",
            "deal_makers": ["AWS depth", "Cost optimization track record"],
            "deal_breakers": [],
        },
        "action_items": {
            "immediate": ["Submit application", "Prepare STAR stories for Kubernetes gap"],
        },
    }
    result.update(overrides)
    return result


def _wire_all_agents(workflow, gap=None, interrogation=None, differentiation=None,
                     tailoring=None, ats=None, audit=None, executive=None):
    """Wire mock return values for every agent on the workflow."""
    workflow.gap_analyzer.execute.return_value = gap or _gap_result()
    workflow.interrogator_prepper.execute.return_value = interrogation or _interrogation_result()
    workflow.differentiator.execute.return_value = differentiation or _differentiation_result()
    workflow.tailoring_agent.execute.return_value = tailoring or _tailoring_result()
    workflow.ats_optimizer.execute.return_value = ats or _ats_result()
    workflow.auditor_suite.execute.return_value = audit or _audit_approved()
    workflow.executive_synthesizer.execute.return_value = executive or _executive_brief()


# ===========================================================================
# 1. Full HydraWorkflow Pipeline
# ===========================================================================

@pytest.mark.integration
class TestWorkflowPipeline:
    """Test the complete HydraWorkflow with mocked agents but real state machine."""

    def test_complete_successful_pipeline(self):
        """All agents succeed, audit passes on first try."""
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        ctx = _base_context()

        result = workflow.execute(ctx)

        assert result.success is True
        assert result.state == HydraWorkflowState.COMPLETED
        assert result.final_documents is not None
        assert result.final_documents["resume"] != ""
        assert result.final_documents["cover_letter"] != ""
        assert result.audit_report["final_status"] == "APPROVED"
        assert result.audit_report["retry_count"] == 0
        assert result.audit_failed is False
        assert result.audit_error is None
        assert result.executive_brief is not None
        assert result.agent_models is not None

    def test_pipeline_audit_retry_then_pass(self):
        """First audit rejects, second audit approves."""
        workflow = _make_workflow(max_audit_retries=2)
        _wire_all_agents(workflow)
        # Resume audit: reject then approve. Cover letter audit: approve always.
        workflow.auditor_suite.execute.side_effect = [
            _audit_rejected(),   # resume audit attempt 1
            _audit_approved(),   # cover letter audit attempt 1 (still runs)
            _audit_approved(),   # resume audit attempt 2
            _audit_approved(),   # cover letter audit attempt 2
        ]
        ctx = _base_context()

        result = workflow.execute(ctx)

        assert result.success is True
        assert result.state == HydraWorkflowState.COMPLETED
        assert result.audit_report["retry_count"] >= 1

    def test_pipeline_audit_crash_preserves_documents(self):
        """Auditor throws exception on all attempts -- documents still returned."""
        workflow = _make_workflow(max_audit_retries=1)
        _wire_all_agents(workflow)
        workflow.auditor_suite.execute.side_effect = RuntimeError("LLM timeout")
        ctx = _base_context()

        result = workflow.execute(ctx)

        assert result.success is True
        assert result.audit_failed is True
        assert "Audit crashed" in result.audit_error
        assert result.audit_report["final_status"] == "AUDIT_CRASHED"
        assert result.final_documents is not None
        # Intermediate results from earlier stages should be preserved
        assert "gap_analysis" in result.intermediate_results
        assert "tailoring" in result.intermediate_results
        assert "ats_optimization" in result.intermediate_results

    def test_pipeline_pauses_at_gap_analysis_review(self):
        """Without gap_analysis_approved the workflow pauses."""
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        ctx = _base_context(gap_analysis_approved=False)
        # Remove interview_answers so the only pause point is gap analysis
        ctx.pop("interview_answers", None)

        result = workflow.execute(ctx)

        assert result.success is True  # pause is a successful pause
        assert result.state == HydraWorkflowState.GAP_ANALYSIS_REVIEW
        assert "Gap Analysis" in result.error_message
        assert "gap_analysis" in result.intermediate_results

    def test_pipeline_pauses_at_interrogation_review(self):
        """With gap_analysis_approved but no interview_answers, pauses at interrogation."""
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        ctx = _base_context(gap_analysis_approved=True)
        del ctx["interview_answers"]

        result = workflow.execute(ctx)

        assert result.success is True
        assert result.state == HydraWorkflowState.INTERROGATION_REVIEW
        assert "interview" in result.error_message.lower()
        assert "gap_analysis" in result.intermediate_results
        assert "interrogation" in result.intermediate_results

    def test_pipeline_resumes_from_pause_with_previous_results(self):
        """Resume workflow from a pause by providing previous_results."""
        workflow = _make_workflow()
        _wire_all_agents(workflow)

        # Simulate a previous run that completed gap_analysis and interrogation
        previous = {
            "gap_analysis": _gap_result(),
            "interrogation": _interrogation_result(),
        }
        ctx = _base_context(
            previous_results=previous,
            gap_analysis_approved=True,
            interview_answers=[{"question_id": "q1", "answer": "Detailed answer"}],
        )

        result = workflow.execute(ctx)

        assert result.success is True
        assert result.state == HydraWorkflowState.COMPLETED
        # Gap analyzer and interrogator should NOT have been called again
        workflow.gap_analyzer.execute.assert_not_called()
        workflow.interrogator_prepper.execute.assert_not_called()
        # Downstream agents should have been called
        workflow.differentiator.execute.assert_called_once()
        workflow.tailoring_agent.execute.assert_called_once()

    def test_pipeline_with_fallback_llm_activation(self):
        """Primary agent fails, fallback succeeds."""
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        # Gap analyzer fails on first call, succeeds on second (fallback path)
        workflow.gap_analyzer.execute.side_effect = [
            RuntimeError("Primary model unavailable"),
            _gap_result(),
        ]
        ctx = _base_context()

        result = workflow.execute(ctx)

        assert result.success is True
        assert result.state == HydraWorkflowState.COMPLETED
        # Fallback should have been attempted
        assert workflow.gap_analyzer.execute.call_count == 2

    def test_pipeline_agent_failure_at_gap_analysis(self):
        """Gap analysis failure crashes the workflow."""
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        workflow.gap_analyzer.execute.side_effect = Exception("Fatal gap error")
        # Also make fallback fail
        workflow.fallback_llm = None
        ctx = _base_context()

        result = workflow.execute(ctx)

        assert result.success is False
        assert result.state == HydraWorkflowState.FAILED
        assert "gap" in result.error_message.lower() or "Fatal" in result.error_message

    def test_pipeline_agent_failure_at_differentiation(self):
        """Differentiation failure crashes the workflow."""
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        workflow.differentiator.execute.side_effect = Exception("Differentiator crashed")
        ctx = _base_context()

        result = workflow.execute(ctx)

        assert result.success is False
        assert result.state == HydraWorkflowState.FAILED
        assert "Differentiator" in result.error_message

    def test_pipeline_agent_failure_at_tailoring(self):
        """Tailoring failure crashes the workflow."""
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        workflow.tailoring_agent.execute.side_effect = Exception("Tailoring timeout")
        ctx = _base_context()

        result = workflow.execute(ctx)

        assert result.success is False
        assert result.state == HydraWorkflowState.FAILED
        assert "Tailoring" in result.error_message

    def test_pipeline_agent_failure_at_ats_optimization(self):
        """ATS optimization failure crashes the workflow."""
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        workflow.ats_optimizer.execute.side_effect = Exception("ATS model error")
        ctx = _base_context()

        result = workflow.execute(ctx)

        assert result.success is False
        assert result.state == HydraWorkflowState.FAILED
        assert "ATS" in result.error_message

    def test_pipeline_intermediate_results_accumulate(self):
        """Each stage stores its output in intermediate_results."""
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        ctx = _base_context()

        result = workflow.execute(ctx)

        assert result.success is True
        ir = result.intermediate_results
        expected_stages = [
            "gap_analysis",
            "interrogation",
            "differentiation",
            "tailoring",
            "ats_optimization",
            "executive_synthesis",
        ]
        for stage in expected_stages:
            assert stage in ir, f"Missing intermediate result for stage: {stage}"

    def test_pipeline_execution_log_captures_all_stages(self):
        """Execution log should mention each major stage."""
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        ctx = _base_context()

        result = workflow.execute(ctx)

        log_text = "\n".join(result.execution_log)
        assert "Gap Analysis" in log_text
        assert "Interrogation" in log_text
        assert "Differentiation" in log_text
        assert "Tailoring" in log_text
        assert "ATS Optimization" in log_text
        assert "Audit" in log_text
        assert "Executive Synthesis" in log_text

    def test_pipeline_agent_models_tracked(self):
        """agent_models dict should be populated for every agent type."""
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        ctx = _base_context()

        result = workflow.execute(ctx)

        assert result.agent_models is not None
        # The workflow assigns models during __init__; fallback model should appear
        assert len(result.agent_models) > 0


# ===========================================================================
# 2. WorkflowState Machine (from models.py)
# ===========================================================================

@pytest.mark.integration
class TestWorkflowStateMachine:
    """Test the WorkflowState dataclass transition logic end-to-end."""

    def _make_state(self, status=WorkflowStatus.INITIALIZED) -> WorkflowState:
        return WorkflowState(
            id="test-workflow-001",
            status=status,
            current_stage="init",
        )

    def test_full_valid_transition_chain(self):
        """Walk through the entire happy-path transition chain."""
        state = self._make_state()
        chain = [
            WorkflowStatus.RESEARCHING,
            WorkflowStatus.ANALYZING,
            WorkflowStatus.AWAITING_GREENLIGHT,
            WorkflowStatus.INTERVIEWING,
            WorkflowStatus.DIFFERENTIATING,
            WorkflowStatus.GENERATING,
            WorkflowStatus.OPTIMIZING,
            WorkflowStatus.AUDITING,
            WorkflowStatus.COMPLETE,
        ]
        for next_status in chain:
            state.transition(next_status)
            assert state.status == next_status

    def test_full_chain_skip_researching(self):
        """INITIALIZED can go directly to ANALYZING."""
        state = self._make_state()
        state.transition(WorkflowStatus.ANALYZING)
        assert state.status == WorkflowStatus.ANALYZING

    def test_retry_path(self):
        """AUDITING -> RETRYING -> GENERATING is valid."""
        state = self._make_state()
        # Walk to AUDITING first
        for s in [
            WorkflowStatus.RESEARCHING,
            WorkflowStatus.ANALYZING,
            WorkflowStatus.AWAITING_GREENLIGHT,
            WorkflowStatus.INTERVIEWING,
            WorkflowStatus.DIFFERENTIATING,
            WorkflowStatus.GENERATING,
            WorkflowStatus.OPTIMIZING,
            WorkflowStatus.AUDITING,
        ]:
            state.transition(s)

        state.transition(WorkflowStatus.RETRYING)
        assert state.status == WorkflowStatus.RETRYING
        state.transition(WorkflowStatus.GENERATING)
        assert state.status == WorkflowStatus.GENERATING

    def test_archive_path(self):
        """AWAITING_GREENLIGHT -> ARCHIVED is valid."""
        state = self._make_state()
        state.transition(WorkflowStatus.RESEARCHING)
        state.transition(WorkflowStatus.ANALYZING)
        state.transition(WorkflowStatus.AWAITING_GREENLIGHT)
        state.transition(WorkflowStatus.ARCHIVED)
        assert state.status == WorkflowStatus.ARCHIVED

    def test_auditing_to_failed(self):
        """AUDITING -> FAILED is valid."""
        state = self._make_state()
        for s in [
            WorkflowStatus.RESEARCHING,
            WorkflowStatus.ANALYZING,
            WorkflowStatus.AWAITING_GREENLIGHT,
            WorkflowStatus.INTERVIEWING,
            WorkflowStatus.DIFFERENTIATING,
            WorkflowStatus.GENERATING,
            WorkflowStatus.OPTIMIZING,
            WorkflowStatus.AUDITING,
        ]:
            state.transition(s)
        state.transition(WorkflowStatus.FAILED)
        assert state.status == WorkflowStatus.FAILED

    def test_invalid_transition_initialized_to_complete(self):
        state = self._make_state()
        with pytest.raises(ValueError, match="Invalid transition"):
            state.transition(WorkflowStatus.COMPLETE)

    def test_invalid_transition_researching_to_interviewing(self):
        state = self._make_state()
        state.transition(WorkflowStatus.RESEARCHING)
        with pytest.raises(ValueError, match="Invalid transition"):
            state.transition(WorkflowStatus.INTERVIEWING)

    def test_invalid_transition_complete_to_anything(self):
        """COMPLETE is a terminal state -- no outgoing transitions."""
        state = self._make_state()
        for s in [
            WorkflowStatus.RESEARCHING,
            WorkflowStatus.ANALYZING,
            WorkflowStatus.AWAITING_GREENLIGHT,
            WorkflowStatus.INTERVIEWING,
            WorkflowStatus.DIFFERENTIATING,
            WorkflowStatus.GENERATING,
            WorkflowStatus.OPTIMIZING,
            WorkflowStatus.AUDITING,
            WorkflowStatus.COMPLETE,
        ]:
            state.transition(s)

        with pytest.raises(ValueError, match="Invalid transition"):
            state.transition(WorkflowStatus.INITIALIZED)

    def test_invalid_transition_archived_to_anything(self):
        """ARCHIVED is a terminal state."""
        state = self._make_state()
        state.transition(WorkflowStatus.RESEARCHING)
        state.transition(WorkflowStatus.ANALYZING)
        state.transition(WorkflowStatus.AWAITING_GREENLIGHT)
        state.transition(WorkflowStatus.ARCHIVED)

        with pytest.raises(ValueError, match="Invalid transition"):
            state.transition(WorkflowStatus.INTERVIEWING)

    def test_log_agent_execution_stores_correct_data(self):
        state = self._make_state()
        inputs = {"job_description": "Test JD"}
        output = {"gaps": ["Terraform"]}

        state.log_agent_execution("gap_analyzer", inputs, output, success=True)

        assert len(state.audit_trail) == 1
        execution = state.audit_trail[0]
        assert execution.agent_name == "gap_analyzer"
        assert execution.inputs == inputs
        assert execution.output == output
        assert execution.success is True
        assert execution.error is None
        assert execution.retry_count == 0
        assert isinstance(execution.timestamp, datetime)
        # Output should also be stored in agent_outputs
        assert state.agent_outputs["gap_analyzer"] == output

    def test_log_agent_execution_with_error(self):
        state = self._make_state()
        state.increment_retry("auditor")

        state.log_agent_execution(
            "auditor", {"doc": "resume"}, {}, success=False, error="Timeout"
        )

        execution = state.audit_trail[0]
        assert execution.success is False
        assert execution.error == "Timeout"
        assert execution.retry_count == 1

    def test_log_error_records_timestamps_and_types(self):
        state = self._make_state()
        error = ValueError("Bad input")

        state.log_error(error)

        assert len(state.errors) == 1
        entry = state.errors[0]
        assert entry["type"] == "ValueError"
        assert "Bad input" in entry["error"]
        assert "timestamp" in entry

    def test_log_error_multiple(self):
        state = self._make_state()
        state.log_error(ValueError("First"))
        state.log_error(RuntimeError("Second"))

        assert len(state.errors) == 2
        assert state.errors[0]["type"] == "ValueError"
        assert state.errors[1]["type"] == "RuntimeError"

    def test_increment_retry_updates_counts(self):
        state = self._make_state()

        assert state.get_retry_count("auditor") == 0
        state.increment_retry("auditor")
        assert state.get_retry_count("auditor") == 1
        state.increment_retry("auditor")
        assert state.get_retry_count("auditor") == 2
        # Different agent stays at 0
        assert state.get_retry_count("gap_analyzer") == 0

    def test_updated_at_changes_on_transition(self):
        state = self._make_state()
        original_updated = state.updated_at

        state.transition(WorkflowStatus.RESEARCHING)

        assert state.updated_at >= original_updated

    def test_log_user_interaction(self):
        state = self._make_state()
        state.log_user_interaction("gap_approval", {"approved": True})

        assert len(state.user_interactions) == 1
        assert state.user_interactions[0]["type"] == "gap_approval"
        assert state.user_interactions[0]["data"]["approved"] is True


# ===========================================================================
# 3. Data Model Round-Trip
# ===========================================================================

@pytest.mark.integration
class TestDataModelRoundTrip:
    """Test creating data models, manipulating them, and verifying invariants."""

    def test_employment_to_resume_chain(self):
        emp1 = Employment(
            company="Acme Corp",
            title="Senior Engineer",
            start_date="2020-01",
            end_date="2023-06",
            achievements=["Led migration to AWS", "Reduced costs by 40%"],
            technologies=["Python", "AWS", "Terraform"],
        )
        emp2 = Employment(
            company="StartupCo",
            title="Staff Engineer",
            start_date="2023-07",
            end_date=None,
            achievements=["Built platform from scratch"],
            technologies=["Go", "Kubernetes"],
        )
        resume = Resume(
            text="# John Doe\nExperienced engineer...",
            format="markdown",
            employment_history=[emp1, emp2],
            skills=["Python", "AWS", "Terraform", "Go", "Kubernetes"],
        )

        assert len(resume.employment_history) == 2
        assert resume.employment_history[0].company == "Acme Corp"
        assert resume.employment_history[1].end_date is None
        assert "Python" in resume.skills
        assert resume.format == "markdown"

    def test_employment_validation(self):
        with pytest.raises(ValueError, match="company"):
            Employment(company="", title="Engineer", start_date="2020-01", end_date=None)

    def test_resume_validation_empty_text(self):
        with pytest.raises(ValueError, match="empty"):
            Resume(text="")

    def test_job_description_to_requirement_to_classification_chain(self):
        jd = JobDescription(
            text="We need a Senior Platform Engineer with AWS and Terraform",
            company="TechCorp",
            role="Senior Platform Engineer",
            requirements=["5+ years AWS", "Terraform expertise", "Team leadership"],
        )
        req1 = Requirement(
            text="5+ years AWS experience",
            type=RequirementType.EXPLICIT,
            priority=RequirementPriority.MUST_HAVE,
            keywords=["AWS", "cloud"],
        )
        req2 = Requirement(
            text="Terraform expertise",
            type=RequirementType.EXPLICIT,
            priority=RequirementPriority.MUST_HAVE,
            keywords=["Terraform", "IaC"],
        )
        req3 = Requirement(
            text="Collaborative team player",
            type=RequirementType.CULTURAL,
            priority=RequirementPriority.NICE_TO_HAVE,
            keywords=["teamwork"],
        )

        cls1 = Classification(
            requirement=req1,
            category=ClassificationType.DIRECT_MATCH,
            evidence="8 years AWS in resume",
            confidence=0.95,
        )
        cls2 = Classification(
            requirement=req2,
            category=ClassificationType.ADJACENT,
            evidence="Used Pulumi, similar to Terraform",
            confidence=0.60,
        )
        cls3 = Classification(
            requirement=req3,
            category=ClassificationType.GAP,
            confidence=0.30,
        )

        assert jd.company == "TechCorp"
        assert len(jd.requirements) == 3
        assert cls1.category == ClassificationType.DIRECT_MATCH
        assert cls2.category == ClassificationType.ADJACENT
        assert cls3.evidence is None
        assert cls1.confidence > cls2.confidence > cls3.confidence

    def test_job_description_validation_empty_text(self):
        with pytest.raises(ValueError, match="empty"):
            JobDescription(text="")

    def test_requirement_validation_empty_text(self):
        with pytest.raises(ValueError, match="empty"):
            Requirement(
                text="", type=RequirementType.EXPLICIT, priority=RequirementPriority.MUST_HAVE
            )

    def test_classification_confidence_bounds(self):
        req = Requirement(
            text="AWS", type=RequirementType.EXPLICIT, priority=RequirementPriority.MUST_HAVE
        )
        with pytest.raises(ValueError, match="Confidence"):
            Classification(requirement=req, category=ClassificationType.DIRECT_MATCH, confidence=1.5)
        with pytest.raises(ValueError, match="Confidence"):
            Classification(requirement=req, category=ClassificationType.DIRECT_MATCH, confidence=-0.1)

    def test_differentiator_with_various_scores(self):
        d1 = Differentiator(
            hook="Platform reliability expert",
            evidence="Achieved 99.99% uptime across 50 services",
            resonance="Directly addresses their scaling concerns",
            relevance_score=0.95,
        )
        d2 = Differentiator(
            hook="Cost optimization leader",
            evidence="Reduced cloud spend by $2M annually",
            resonance="Budget-conscious engineering culture",
            relevance_score=0.0,
        )
        d3 = Differentiator(
            hook="Open source contributor",
            evidence="Maintained Terraform provider with 10k stars",
            resonance="Community engagement valued by company",
            relevance_score=1.0,
        )

        assert d1.relevance_score == 0.95
        assert d2.relevance_score == 0.0
        assert d3.relevance_score == 1.0

    def test_differentiator_validation_missing_fields(self):
        with pytest.raises(ValueError, match="hook"):
            Differentiator(hook="", evidence="data", resonance="reason")

    def test_differentiator_score_out_of_range(self):
        with pytest.raises(ValueError, match="Relevance score"):
            Differentiator(
                hook="Test", evidence="data", resonance="reason", relevance_score=1.5
            )

    def test_audit_issue_with_all_valid_types(self):
        valid_types = ["truth", "tone", "ats", "compliance"]
        for issue_type in valid_types:
            issue = AuditIssue(
                type=issue_type,
                severity=IssueSeverity.WARNING,
                location="resume.section.skills",
                description=f"Issue of type {issue_type}",
                fix=f"Fix for {issue_type}",
            )
            assert issue.type == issue_type

    def test_audit_issue_invalid_type(self):
        with pytest.raises(ValueError, match="Issue type"):
            AuditIssue(
                type="invalid_type",
                severity=IssueSeverity.BLOCKING,
                location="resume",
                description="Bad",
                fix="Fix",
            )

    def test_audit_issue_severity_levels(self):
        for severity in IssueSeverity:
            issue = AuditIssue(
                type="truth",
                severity=severity,
                location="cover_letter.paragraph.2",
                description="Test",
                fix="Fix",
            )
            assert issue.severity == severity

    def test_agent_execution_record(self):
        now = datetime.now()
        execution = AgentExecution(
            agent_name="gap_analyzer",
            timestamp=now,
            inputs={"jd": "test"},
            output={"gaps": []},
            success=True,
            retry_count=0,
        )
        assert execution.agent_name == "gap_analyzer"
        assert execution.timestamp == now
        assert execution.success is True
        assert execution.error is None


# ===========================================================================
# 4. CLI Output Writing
# ===========================================================================

@pytest.mark.integration
class TestCLIOutputWriting:
    """Test _write_output_files with a real temp directory."""

    def _make_result(self, **overrides):
        """Build a WorkflowResult-like object for testing."""
        defaults = {
            "final_documents": {
                "resume": "# John Doe\nResume content here",
                "cover_letter": "Dear Hiring Manager,\nCover letter here",
            },
            "audit_report": {
                "final_status": "APPROVED",
                "resume_audit": {"approved": True},
            },
            "execution_log": [
                "[2025-12-06T18:45:00] Starting workflow",
                "[2025-12-06T18:50:00] Workflow completed",
            ],
            "intermediate_results": {
                "gap_analysis": {"gaps": ["Terraform"]},
                "tailoring": {"confidence": 0.93},
            },
        }
        defaults.update(overrides)

        result = Mock()
        for key, value in defaults.items():
            setattr(result, key, value)
        return result

    def test_creates_correct_files(self):
        from runtime.crewai.cli import _write_output_files

        result = self._make_result()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "output"
            _write_output_files(out_dir, result)

            assert (out_dir / "resume.md").exists()
            assert (out_dir / "cover_letter.md").exists()
            assert (out_dir / "audit_report.yaml").exists()
            assert (out_dir / "execution_log.txt").exists()

            resume_text = (out_dir / "resume.md").read_text()
            assert "John Doe" in resume_text

            cover_text = (out_dir / "cover_letter.md").read_text()
            assert "Hiring Manager" in cover_text

            audit_yaml = yaml.safe_load((out_dir / "audit_report.yaml").read_text())
            assert audit_yaml["final_status"] == "APPROVED"

            log_text = (out_dir / "execution_log.txt").read_text()
            assert "Starting workflow" in log_text

    def test_writes_intermediate_results_when_flag_is_true(self):
        from runtime.crewai.cli import _write_output_files

        result = self._make_result()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "output"
            _write_output_files(out_dir, result, include_intermediate=True)

            intermediate_dir = out_dir / "intermediate"
            assert intermediate_dir.exists()
            assert (intermediate_dir / "gap_analysis.yaml").exists()
            assert (intermediate_dir / "tailoring.yaml").exists()

            gap_yaml = yaml.safe_load((intermediate_dir / "gap_analysis.yaml").read_text())
            assert "Terraform" in gap_yaml["gaps"]

    def test_no_intermediate_dir_when_flag_is_false(self):
        from runtime.crewai.cli import _write_output_files

        result = self._make_result()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "output"
            _write_output_files(out_dir, result, include_intermediate=False)

            assert not (out_dir / "intermediate").exists()

    def test_handles_missing_optional_fields(self):
        from runtime.crewai.cli import _write_output_files

        result = self._make_result(
            final_documents=None,
            audit_report=None,
            execution_log=None,
            intermediate_results=None,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "output"
            _write_output_files(out_dir, result)

            # Files should still be created (with empty/default content)
            assert (out_dir / "resume.md").exists()
            assert (out_dir / "resume.md").read_text() == ""
            assert (out_dir / "cover_letter.md").exists()
            assert (out_dir / "audit_report.yaml").exists()

    def test_handles_empty_documents(self):
        from runtime.crewai.cli import _write_output_files

        result = self._make_result(
            final_documents={"resume": "", "cover_letter": ""},
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "output"
            _write_output_files(out_dir, result)

            assert (out_dir / "resume.md").read_text() == ""
            assert (out_dir / "cover_letter.md").read_text() == ""


# ===========================================================================
# 5. Workflow + Executive Synthesis Integration
# ===========================================================================

@pytest.mark.integration
class TestWorkflowExecutiveSynthesis:
    """Mock all agents to return structured JSON, run workflow, verify executive brief."""

    def test_executive_brief_has_valid_decision_structure(self):
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        ctx = _base_context()

        result = workflow.execute(ctx)

        assert result.executive_brief is not None
        decision = result.executive_brief.get("decision", {})
        assert "recommendation" in decision
        assert "fit_score" in decision
        assert "rationale" in decision
        assert isinstance(decision.get("deal_makers"), list)
        assert isinstance(decision.get("deal_breakers"), list)

    def test_all_intermediate_results_preserved(self):
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        ctx = _base_context()

        result = workflow.execute(ctx)

        ir = result.intermediate_results
        assert "gap_analysis" in ir
        assert "interrogation" in ir
        assert "differentiation" in ir
        assert "tailoring" in ir
        assert "ats_optimization" in ir
        assert "executive_synthesis" in ir

    def test_agent_models_tracked_for_all_agents(self):
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        ctx = _base_context()

        result = workflow.execute(ctx)

        assert result.agent_models is not None
        # All agent types should have a model entry
        expected_agents = [
            "gap_analyzer",
            "interrogator_prepper",
            "differentiator",
            "tailoring_agent",
            "ats_optimizer",
            "auditor_suite",
            "executive_synthesizer",
        ]
        for agent_type in expected_agents:
            assert agent_type in result.agent_models, f"Missing model for {agent_type}"

    def test_executive_synthesis_receives_all_stage_data(self):
        """Verify that executive synthesizer is called with data from all prior stages."""
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        ctx = _base_context()

        result = workflow.execute(ctx)

        # The executive synthesizer should have been called
        workflow.executive_synthesizer.execute.assert_called_once()
        call_args = workflow.executive_synthesizer.execute.call_args[0][0]

        # Verify it received context from multiple stages
        assert "gap_analysis" in call_args
        assert "interview_notes" in call_args
        assert "differentiation" in call_args
        assert "ats_optimization" in call_args
        assert "audit_report" in call_args
        assert "job_description" in call_args

    def test_executive_synthesis_failure_produces_fallback_brief(self):
        """If executive synthesis fails, a fallback brief should be returned."""
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        workflow.executive_synthesizer.execute.side_effect = Exception("Schema validation error")
        ctx = _base_context()

        result = workflow.execute(ctx)

        assert result.success is True
        assert result.executive_brief is not None
        # Fallback should have a decision with PROCEED recommendation
        decision = result.executive_brief.get("decision", {})
        assert decision["recommendation"] == "PROCEED"
        assert decision["fit_score"] == 70
        assert "synthesis_error" in result.executive_brief


# ===========================================================================
# 6. Error Propagation
# ===========================================================================

@pytest.mark.integration
class TestErrorPropagation:
    """Test that errors at each stage propagate correctly."""

    def test_validation_error_in_context_validation(self):
        """Missing required context key raises ValidationError caught by workflow."""
        workflow = _make_workflow()
        ctx = {"job_description": "JD only"}  # missing resume and source_documents

        result = workflow.execute(ctx)

        assert result.success is False
        assert result.state == HydraWorkflowState.FAILED
        assert "Missing required context key" in result.error_message

    def test_agent_execution_error_in_gap_analysis(self):
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        workflow.gap_analyzer.execute.side_effect = Exception("Gap analysis LLM error")
        ctx = _base_context()

        result = workflow.execute(ctx)

        assert result.success is False
        assert result.state == HydraWorkflowState.FAILED
        assert "Gap analysis LLM error" in result.error_message
        # No intermediate results beyond what ran
        assert "tailoring" not in (result.intermediate_results or {})

    def test_agent_execution_error_in_tailoring(self):
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        workflow.tailoring_agent.execute.side_effect = Exception("Tailoring model OOM")
        ctx = _base_context()

        result = workflow.execute(ctx)

        assert result.success is False
        assert result.state == HydraWorkflowState.FAILED
        assert "Tailoring model OOM" in result.error_message
        # Earlier stages should have completed
        ir = result.intermediate_results or {}
        assert "gap_analysis" in ir
        assert "interrogation" in ir
        assert "differentiation" in ir
        # Tailoring and later should not be present
        assert "tailoring" not in ir
        assert "ats_optimization" not in ir

    def test_audit_crash_vs_audit_rejection(self):
        """Audit crash and audit rejection produce different statuses."""
        # Test rejection
        workflow_rej = _make_workflow(max_audit_retries=0)
        _wire_all_agents(workflow_rej)
        workflow_rej.auditor_suite.execute.return_value = _audit_rejected()
        ctx = _base_context()

        result_rej = workflow_rej.execute(ctx)
        assert result_rej.success is True
        assert result_rej.audit_failed is True
        assert result_rej.audit_report["final_status"] == "REJECTED"

        # Test crash
        workflow_crash = _make_workflow(max_audit_retries=0)
        _wire_all_agents(workflow_crash)
        workflow_crash.auditor_suite.execute.side_effect = RuntimeError("Connection reset")

        result_crash = workflow_crash.execute(ctx)
        assert result_crash.success is True
        assert result_crash.audit_failed is True
        assert result_crash.audit_report["final_status"] == "AUDIT_CRASHED"
        assert "Connection reset" in result_crash.audit_error

    def test_error_preserves_partial_intermediate_results(self):
        """When a mid-pipeline stage fails, earlier results are still available."""
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        workflow.ats_optimizer.execute.side_effect = Exception("ATS service down")
        ctx = _base_context()

        result = workflow.execute(ctx)

        assert result.success is False
        ir = result.intermediate_results or {}
        assert "gap_analysis" in ir
        assert "interrogation" in ir
        assert "differentiation" in ir
        assert "tailoring" in ir
        assert "ats_optimization" not in ir

    def test_cross_stage_data_flow_on_success(self):
        """Verify data flows correctly from gap_analysis through to tailoring."""
        workflow = _make_workflow()
        custom_gap = _gap_result(
            gaps=[{"skill": "Kubernetes", "severity": "high"}],
            confidence=0.99,
        )
        _wire_all_agents(workflow, gap=custom_gap)
        ctx = _base_context()

        result = workflow.execute(ctx)

        assert result.success is True
        # Differentiator should have received the gap result
        diff_call_args = workflow.differentiator.execute.call_args[0][0]
        assert "gap_analysis" in diff_call_args
        assert diff_call_args["gap_analysis"]["confidence"] == 0.99

        # Tailoring should have received differentiation output
        tailor_call_args = workflow.tailoring_agent.execute.call_args[0][0]
        assert "differentiation" in tailor_call_args
        assert "gap_analysis" in tailor_call_args

    def test_interrogation_answers_flow_to_downstream_stages(self):
        """Interview answers from context are passed through to differentiation and tailoring."""
        workflow = _make_workflow()
        _wire_all_agents(workflow)
        custom_answers = [
            {"question_id": "q1", "answer": "Built Terraform modules for 3 teams"},
        ]
        ctx = _base_context(interview_answers=custom_answers)

        result = workflow.execute(ctx)

        assert result.success is True
        # The interrogation result should contain the interview answers
        interrogation = result.intermediate_results["interrogation"]
        assert interrogation.get("interview_notes") == custom_answers
