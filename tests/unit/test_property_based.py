"""
Property-based tests for Composable Me Hydra.

Uses hypothesis to generate arbitrary inputs and verify invariants
across data models, JSON validation, schema normalization, and LLM client validation.
"""

import json
import pytest
from hypothesis import given, assume, settings
from hypothesis import strategies as st
from datetime import datetime
from typing import Dict, Any
from unittest.mock import patch

from runtime.crewai.models import (
    Employment,
    Resume,
    JobDescription,
    Requirement,
    Classification,
    Differentiator,
    AuditIssue,
    WorkflowState,
    WorkflowStatus,
    ClassificationType,
    IssueSeverity,
    RequirementType,
    RequirementPriority,
    AgentExecution,
)
from runtime.crewai.base_agent import BaseHydraAgent, ValidationError
from runtime.crewai.agents.executive_synthesizer import ExecutiveSynthesizerAgent
from runtime.crewai.llm_client import validate_model_name
from crewai import LLM


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _TestAgent(BaseHydraAgent):
    """Concrete subclass of BaseHydraAgent for testing purposes."""

    role = "Test Agent"
    goal = "Test goal"
    expected_output = "Test output"

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ok"}


def _make_mock_llm() -> LLM:
    """Create a mock LLM that does not require real credentials."""
    return LLM(model="gpt-4", api_key="test-key")


def _make_workflow_state(
    status: WorkflowStatus = WorkflowStatus.INITIALIZED,
) -> WorkflowState:
    return WorkflowState(
        id="test-wf-1",
        status=status,
        current_stage="test",
    )


# ---------------------------------------------------------------------------
# Reusable hypothesis strategies
# ---------------------------------------------------------------------------

non_empty_text = st.text(min_size=1, max_size=200).filter(lambda s: s.strip())
optional_text = st.one_of(st.none(), non_empty_text)
keyword_list = st.lists(st.text(min_size=1, max_size=50), max_size=10)
achievement_list = st.lists(st.text(min_size=0, max_size=100), max_size=10)

requirement_type_st = st.sampled_from(list(RequirementType))
requirement_priority_st = st.sampled_from(list(RequirementPriority))
classification_type_st = st.sampled_from(list(ClassificationType))
issue_severity_st = st.sampled_from(list(IssueSeverity))
workflow_status_st = st.sampled_from(list(WorkflowStatus))

valid_confidence = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
invalid_confidence_low = st.floats(max_value=-0.001, allow_nan=False, allow_infinity=False)
invalid_confidence_high = st.floats(min_value=1.001, allow_nan=False, allow_infinity=False)

valid_audit_type = st.sampled_from(["truth", "tone", "ats", "compliance"])


# ============================================================================
# 1. Data Model Tests
# ============================================================================


@pytest.mark.property
class TestEmploymentProperty:
    """Property-based tests for Employment dataclass."""

    @given(
        company=non_empty_text,
        title=non_empty_text,
        start_date=non_empty_text,
        end_date=optional_text,
        achievements=achievement_list,
        technologies=keyword_list,
    )
    @settings(max_examples=100)
    def test_valid_employment_roundtrips(
        self, company, title, start_date, end_date, achievements, technologies
    ):
        emp = Employment(
            company=company,
            title=title,
            start_date=start_date,
            end_date=end_date,
            achievements=achievements,
            technologies=technologies,
        )
        assert emp.company == company
        assert emp.title == title
        assert emp.start_date == start_date

    @given(
        company=st.text(max_size=200),
        title=st.text(max_size=200),
        start_date=st.text(max_size=200),
        end_date=optional_text,
    )
    @settings(max_examples=100)
    def test_empty_required_fields_raise(self, company, title, start_date, end_date):
        assume(not company or not title or not start_date)
        with pytest.raises(ValueError, match="Employment must have"):
            Employment(company=company, title=title, start_date=start_date, end_date=end_date)


@pytest.mark.property
class TestResumeProperty:
    """Property-based tests for Resume dataclass."""

    @given(text=non_empty_text, skills=keyword_list)
    @settings(max_examples=100)
    def test_valid_resume(self, text, skills):
        r = Resume(text=text, skills=skills)
        assert r.text == text
        assert r.skills == skills

    @given(text=st.just(""))
    @settings(max_examples=5)
    def test_empty_text_raises(self, text):
        with pytest.raises(ValueError, match="Resume text cannot be empty"):
            Resume(text=text)


@pytest.mark.property
class TestJobDescriptionProperty:
    """Property-based tests for JobDescription dataclass."""

    @given(text=non_empty_text, company=optional_text, role=optional_text)
    @settings(max_examples=100)
    def test_valid_job_description(self, text, company, role):
        jd = JobDescription(text=text, company=company, role=role)
        assert jd.text == text

    @given(text=st.just(""))
    @settings(max_examples=5)
    def test_empty_text_raises(self, text):
        with pytest.raises(ValueError, match="Job description text cannot be empty"):
            JobDescription(text=text)


@pytest.mark.property
class TestRequirementProperty:
    """Property-based tests for Requirement dataclass."""

    @given(
        text=non_empty_text,
        req_type=requirement_type_st,
        priority=requirement_priority_st,
        keywords=keyword_list,
    )
    @settings(max_examples=100)
    def test_valid_requirement(self, text, req_type, priority, keywords):
        r = Requirement(text=text, type=req_type, priority=priority, keywords=keywords)
        assert r.text == text
        assert r.type == req_type
        assert r.priority == priority

    @given(
        req_type=requirement_type_st,
        priority=requirement_priority_st,
    )
    @settings(max_examples=20)
    def test_empty_text_raises(self, req_type, priority):
        with pytest.raises(ValueError, match="Requirement text cannot be empty"):
            Requirement(text="", type=req_type, priority=priority)


@pytest.mark.property
class TestClassificationProperty:
    """Property-based tests for Classification dataclass."""

    @given(
        text=non_empty_text,
        req_type=requirement_type_st,
        priority=requirement_priority_st,
        category=classification_type_st,
        confidence=valid_confidence,
        evidence=optional_text,
        framing=optional_text,
    )
    @settings(max_examples=100)
    def test_valid_classification(
        self, text, req_type, priority, category, confidence, evidence, framing
    ):
        req = Requirement(text=text, type=req_type, priority=priority)
        c = Classification(
            requirement=req,
            category=category,
            confidence=confidence,
            evidence=evidence,
            framing=framing,
        )
        assert 0.0 <= c.confidence <= 1.0
        assert c.category == category

    @given(confidence=invalid_confidence_low)
    @settings(max_examples=50)
    def test_confidence_below_zero_raises(self, confidence):
        req = Requirement(text="test", type=RequirementType.EXPLICIT, priority=RequirementPriority.MUST_HAVE)
        with pytest.raises(ValueError, match="Confidence must be between"):
            Classification(requirement=req, category=ClassificationType.DIRECT_MATCH, confidence=confidence)

    @given(confidence=invalid_confidence_high)
    @settings(max_examples=50)
    def test_confidence_above_one_raises(self, confidence):
        req = Requirement(text="test", type=RequirementType.EXPLICIT, priority=RequirementPriority.MUST_HAVE)
        with pytest.raises(ValueError, match="Confidence must be between"):
            Classification(requirement=req, category=ClassificationType.DIRECT_MATCH, confidence=confidence)


@pytest.mark.property
class TestDifferentiatorProperty:
    """Property-based tests for Differentiator dataclass."""

    @given(
        hook=non_empty_text,
        evidence=non_empty_text,
        resonance=non_empty_text,
        relevance_score=valid_confidence,
    )
    @settings(max_examples=100)
    def test_valid_differentiator(self, hook, evidence, resonance, relevance_score):
        d = Differentiator(
            hook=hook,
            evidence=evidence,
            resonance=resonance,
            relevance_score=relevance_score,
        )
        assert d.hook == hook
        assert 0.0 <= d.relevance_score <= 1.0

    @given(
        hook=st.text(max_size=200),
        evidence=st.text(max_size=200),
        resonance=st.text(max_size=200),
    )
    @settings(max_examples=100)
    def test_empty_required_fields_raise(self, hook, evidence, resonance):
        assume(not hook or not evidence or not resonance)
        with pytest.raises(ValueError, match="Differentiator must have"):
            Differentiator(hook=hook, evidence=evidence, resonance=resonance)

    @given(score=invalid_confidence_low)
    @settings(max_examples=50)
    def test_relevance_below_zero_raises(self, score):
        with pytest.raises(ValueError, match="Relevance score must be between"):
            Differentiator(hook="h", evidence="e", resonance="r", relevance_score=score)

    @given(score=invalid_confidence_high)
    @settings(max_examples=50)
    def test_relevance_above_one_raises(self, score):
        with pytest.raises(ValueError, match="Relevance score must be between"):
            Differentiator(hook="h", evidence="e", resonance="r", relevance_score=score)


@pytest.mark.property
class TestAuditIssueProperty:
    """Property-based tests for AuditIssue dataclass."""

    @given(
        issue_type=valid_audit_type,
        severity=issue_severity_st,
        location=non_empty_text,
        description=non_empty_text,
        fix=non_empty_text,
    )
    @settings(max_examples=100)
    def test_valid_audit_issue(self, issue_type, severity, location, description, fix):
        ai = AuditIssue(
            type=issue_type,
            severity=severity,
            location=location,
            description=description,
            fix=fix,
        )
        assert ai.type in {"truth", "tone", "ats", "compliance"}
        assert ai.severity == severity

    @given(
        bad_type=st.text(min_size=1, max_size=50).filter(
            lambda s: s not in {"truth", "tone", "ats", "compliance"}
        ),
        severity=issue_severity_st,
    )
    @settings(max_examples=100)
    def test_invalid_type_raises(self, bad_type, severity):
        with pytest.raises(ValueError, match="Issue type must be one of"):
            AuditIssue(
                type=bad_type,
                severity=severity,
                location="loc",
                description="desc",
                fix="fix",
            )


# ============================================================================
# 2. WorkflowState Transition Tests
# ============================================================================


# Encode the valid transition graph for property tests
VALID_TRANSITIONS: Dict[WorkflowStatus, set] = {
    WorkflowStatus.INITIALIZED: {WorkflowStatus.RESEARCHING, WorkflowStatus.ANALYZING},
    WorkflowStatus.RESEARCHING: {WorkflowStatus.ANALYZING},
    WorkflowStatus.ANALYZING: {WorkflowStatus.AWAITING_GREENLIGHT},
    WorkflowStatus.AWAITING_GREENLIGHT: {WorkflowStatus.INTERVIEWING, WorkflowStatus.ARCHIVED},
    WorkflowStatus.INTERVIEWING: {WorkflowStatus.DIFFERENTIATING},
    WorkflowStatus.DIFFERENTIATING: {WorkflowStatus.GENERATING},
    WorkflowStatus.GENERATING: {WorkflowStatus.OPTIMIZING},
    WorkflowStatus.OPTIMIZING: {WorkflowStatus.AUDITING},
    WorkflowStatus.AUDITING: {WorkflowStatus.COMPLETE, WorkflowStatus.RETRYING, WorkflowStatus.FAILED},
    WorkflowStatus.RETRYING: {WorkflowStatus.GENERATING},
}

# Terminal/sink states with no valid outgoing transitions
TERMINAL_STATES = {WorkflowStatus.COMPLETE, WorkflowStatus.FAILED, WorkflowStatus.ARCHIVED}


@pytest.mark.property
class TestWorkflowStateProperty:
    """Property-based tests for WorkflowState transitions and logging."""

    @given(
        from_status=workflow_status_st,
        to_status=workflow_status_st,
    )
    @settings(max_examples=200)
    def test_valid_transitions_succeed_invalid_raise(self, from_status, to_status):
        ws = _make_workflow_state(from_status)
        valid_targets = VALID_TRANSITIONS.get(from_status, set())

        if to_status in valid_targets:
            ws.transition(to_status)
            assert ws.status == to_status
        else:
            with pytest.raises(ValueError, match="Invalid transition"):
                ws.transition(to_status)

    @given(agent_name=non_empty_text, data=st.dictionaries(st.text(min_size=1, max_size=20), st.text(max_size=50), max_size=5))
    @settings(max_examples=100)
    def test_log_agent_execution_appends(self, agent_name, data):
        ws = _make_workflow_state()
        initial_len = len(ws.audit_trail)
        ws.log_agent_execution(agent_name=agent_name, inputs=data, output=data)
        assert len(ws.audit_trail) == initial_len + 1
        assert ws.audit_trail[-1].agent_name == agent_name
        assert ws.agent_outputs[agent_name] == data

    @given(agent_name=non_empty_text)
    @settings(max_examples=100)
    def test_increment_retry_monotonic(self, agent_name):
        ws = _make_workflow_state()
        assert ws.get_retry_count(agent_name) == 0
        ws.increment_retry(agent_name)
        assert ws.get_retry_count(agent_name) == 1
        ws.increment_retry(agent_name)
        assert ws.get_retry_count(agent_name) == 2

    @given(
        interaction_type=non_empty_text,
        data=st.dictionaries(st.text(min_size=1, max_size=20), st.text(max_size=50), max_size=5),
    )
    @settings(max_examples=100)
    def test_log_user_interaction_appends(self, interaction_type, data):
        ws = _make_workflow_state()
        initial_len = len(ws.user_interactions)
        ws.log_user_interaction(interaction_type, data)
        assert len(ws.user_interactions) == initial_len + 1
        assert ws.user_interactions[-1]["type"] == interaction_type
        assert ws.user_interactions[-1]["data"] == data

    @given(error_msg=non_empty_text)
    @settings(max_examples=100)
    def test_log_error_appends(self, error_msg):
        ws = _make_workflow_state()
        initial_len = len(ws.errors)
        ws.log_error(ValueError(error_msg))
        assert len(ws.errors) == initial_len + 1
        assert ws.errors[-1]["error"] == error_msg
        assert ws.errors[-1]["type"] == "ValueError"

    def test_random_valid_transition_sequence(self):
        """Walk through a full valid path from INITIALIZED to COMPLETE."""
        # One specific valid path through the state machine
        path = [
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
        ws = _make_workflow_state(WorkflowStatus.INITIALIZED)
        for target in path:
            ws.transition(target)
        assert ws.status == WorkflowStatus.COMPLETE

    def test_retry_loop_path(self):
        """Walk through a path with a retry loop."""
        ws = _make_workflow_state(WorkflowStatus.INITIALIZED)
        ws.transition(WorkflowStatus.RESEARCHING)
        ws.transition(WorkflowStatus.ANALYZING)
        ws.transition(WorkflowStatus.AWAITING_GREENLIGHT)
        ws.transition(WorkflowStatus.INTERVIEWING)
        ws.transition(WorkflowStatus.DIFFERENTIATING)
        ws.transition(WorkflowStatus.GENERATING)
        ws.transition(WorkflowStatus.OPTIMIZING)
        ws.transition(WorkflowStatus.AUDITING)
        # Retry loop
        ws.transition(WorkflowStatus.RETRYING)
        ws.transition(WorkflowStatus.GENERATING)
        ws.transition(WorkflowStatus.OPTIMIZING)
        ws.transition(WorkflowStatus.AUDITING)
        ws.transition(WorkflowStatus.COMPLETE)
        assert ws.status == WorkflowStatus.COMPLETE

    @given(to_status=workflow_status_st)
    @settings(max_examples=50)
    def test_terminal_states_reject_all_transitions(self, to_status):
        for terminal in TERMINAL_STATES:
            ws = _make_workflow_state(terminal)
            with pytest.raises(ValueError, match="Invalid transition"):
                ws.transition(to_status)


# ============================================================================
# 3. BaseHydraAgent JSON Validation Tests
# ============================================================================


@pytest.mark.property
class TestBaseAgentValidateOutputProperty:
    """Property tests for BaseHydraAgent.validate_output."""

    @given(
        agent_name=non_empty_text,
        confidence=valid_confidence,
        extra_key=non_empty_text,
        extra_val=non_empty_text,
    )
    @settings(max_examples=100)
    def test_valid_json_dict_always_has_required_keys(
        self, agent_name, confidence, extra_key, extra_val
    ):
        agent = _TestAgent(llm=_make_mock_llm(), prompt_path=None)
        payload = {
            "agent": agent_name,
            "timestamp": "2025-01-01T00:00:00Z",
            "confidence": confidence,
            extra_key: extra_val,
        }
        raw = json.dumps(payload)
        result = agent.validate_output(raw)

        assert "agent" in result
        assert "timestamp" in result
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

    @given(confidence=st.one_of(
        st.floats(allow_nan=False, allow_infinity=False),
        st.integers(),
        st.text(max_size=20),
    ))
    @settings(max_examples=100)
    def test_confidence_always_clamped(self, confidence):
        agent = _TestAgent(llm=_make_mock_llm(), prompt_path=None)
        payload = {"agent": "test", "timestamp": "2025-01-01T00:00:00Z", "confidence": confidence}
        raw = json.dumps(payload)
        result = agent.validate_output(raw)
        assert isinstance(result["confidence"], float)
        assert 0.0 <= result["confidence"] <= 1.0

    @given(data=st.dictionaries(
        st.text(min_size=1, max_size=30),
        st.one_of(st.text(max_size=50), st.integers(), st.floats(allow_nan=False, allow_infinity=False)),
        min_size=1,
        max_size=10,
    ))
    @settings(max_examples=100)
    def test_arbitrary_dict_does_not_crash(self, data):
        agent = _TestAgent(llm=_make_mock_llm(), prompt_path=None)
        raw = json.dumps(data)
        result = agent.validate_output(raw)
        # Should always produce a dict with the required keys filled in
        assert isinstance(result, dict)
        assert "agent" in result
        assert "timestamp" in result
        assert "confidence" in result

    @given(non_dict=st.one_of(
        st.lists(st.integers(), max_size=5),
        st.just("plain string"),
        st.just(42),
        st.just(True),
    ))
    @settings(max_examples=20)
    def test_non_dict_json_raises_validation_error(self, non_dict):
        agent = _TestAgent(llm=_make_mock_llm(), prompt_path=None)
        raw = json.dumps(non_dict)
        with pytest.raises(ValidationError, match="must be a JSON object"):
            agent.validate_output(raw)

    @given(garbage=st.text(min_size=1, max_size=100).filter(lambda s: "{" not in s))
    @settings(max_examples=50)
    def test_non_json_string_raises_validation_error(self, garbage):
        agent = _TestAgent(llm=_make_mock_llm(), prompt_path=None)
        with pytest.raises(ValidationError):
            agent.validate_output(garbage)

    def test_markdown_wrapped_json_is_extracted(self):
        agent = _TestAgent(llm=_make_mock_llm(), prompt_path=None)
        payload = {"agent": "test", "confidence": 0.9, "timestamp": "2025-01-01T00:00:00Z"}
        raw = f"```json\n{json.dumps(payload)}\n```"
        result = agent.validate_output(raw)
        assert result["agent"] == "test"
        assert result["confidence"] == 0.9

    def test_defaults_filled_when_missing(self):
        agent = _TestAgent(llm=_make_mock_llm(), prompt_path=None)
        raw = json.dumps({"some_data": "value"})
        result = agent.validate_output(raw)
        assert result["agent"] == "Test Agent"
        assert "timestamp" in result
        assert isinstance(result["confidence"], float)


# ============================================================================
# 4. Executive Synthesizer Schema Validation Tests
# ============================================================================


@pytest.mark.property
class TestExecutiveSynthesizerSchemaProperty:
    """Property tests for ExecutiveSynthesizerAgent._validate_schema."""

    VALID_RECOMMENDATIONS = {"STRONG_PROCEED", "PROCEED", "PROCEED_WITH_CAUTION", "PASS"}

    def _make_agent(self) -> ExecutiveSynthesizerAgent:
        return ExecutiveSynthesizerAgent(llm=_make_mock_llm())

    @given(
        recommendation=st.sampled_from(["STRONG_PROCEED", "PROCEED", "PROCEED_WITH_CAUTION", "PASS"]),
        fit_score=st.integers(min_value=0, max_value=100),
    )
    @settings(max_examples=100)
    def test_valid_recommendation_preserved(self, recommendation, fit_score):
        agent = self._make_agent()
        data = {
            "decision": {
                "recommendation": recommendation,
                "fit_score": fit_score,
                "rationale": "test rationale",
            }
        }
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == recommendation

    @given(
        rec=st.sampled_from(["CAUTION", "REJECT", "NO", "YES", "APPROVED", "STRONG_YES"]),
    )
    @settings(max_examples=50)
    def test_recommendation_normalized_to_valid_set(self, rec):
        agent = self._make_agent()
        data = {
            "decision": {
                "recommendation": rec,
                "fit_score": 50,
            }
        }
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] in self.VALID_RECOMMENDATIONS

    @given(fit_score=st.one_of(
        st.integers(),
        st.text(min_size=1, max_size=10).filter(lambda s: s.replace("%", "").lstrip("-").isdigit()),
    ))
    @settings(max_examples=100)
    def test_fit_score_always_numeric(self, fit_score):
        agent = self._make_agent()
        data = {
            "decision": {
                "recommendation": "PROCEED",
                "fit_score": fit_score,
            }
        }
        agent._validate_schema(data)
        result_score = data["decision"]["fit_score"]
        assert isinstance(result_score, (int, float))

    @given(decision_str=st.sampled_from(["STRONG_PROCEED", "PROCEED", "PROCEED_WITH_CAUTION", "PASS"]))
    @settings(max_examples=20)
    def test_flat_string_decision_normalized(self, decision_str):
        agent = self._make_agent()
        data = {"decision": decision_str}
        agent._validate_schema(data)
        assert isinstance(data["decision"], dict)
        assert data["decision"]["recommendation"] in self.VALID_RECOMMENDATIONS

    def test_missing_decision_infers_from_fit_score(self):
        """When no decision field exists, the schema validator infers from fit_score (default 0 -> PASS)."""
        agent = self._make_agent()
        data = {"some_field": "some_value"}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PASS"
        assert data["decision"]["fit_score"] == 0

    def test_decision_dict_without_recommendation_raises(self):
        agent = self._make_agent()
        data = {"decision": {"fit_score": 75}}
        with pytest.raises(ValidationError, match="must include 'recommendation'"):
            agent._validate_schema(data)

    @given(
        nested_key=st.sampled_from(["executive_brief", "summary", "analysis", "result", "output", "brief"]),
        recommendation=st.sampled_from(["STRONG_PROCEED", "PROCEED", "PROCEED_WITH_CAUTION", "PASS"]),
    )
    @settings(max_examples=50)
    def test_nested_decision_is_found(self, nested_key, recommendation):
        agent = self._make_agent()
        data = {
            nested_key: {
                "decision": {
                    "recommendation": recommendation,
                    "fit_score": 75,
                }
            }
        }
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] in self.VALID_RECOMMENDATIONS

    @given(fit_score=st.integers(min_value=0, max_value=100))
    @settings(max_examples=50)
    def test_root_level_recommendation_promoted(self, fit_score):
        agent = self._make_agent()
        data = {
            "recommendation": "PROCEED",
            "fit_score": fit_score,
            "rationale": "test",
        }
        agent._validate_schema(data)
        assert isinstance(data["decision"], dict)
        assert data["decision"]["recommendation"] in self.VALID_RECOMMENDATIONS

    @given(fit_score=st.integers(min_value=0, max_value=100))
    @settings(max_examples=50)
    def test_inferred_recommendation_from_score(self, fit_score):
        agent = self._make_agent()
        data = {"fit_score": fit_score}
        agent._validate_schema(data)
        rec = data["decision"]["recommendation"]
        assert rec in self.VALID_RECOMMENDATIONS
        # Verify the inference logic
        if fit_score >= 80:
            assert rec == "STRONG_PROCEED"
        elif fit_score >= 65:
            assert rec == "PROCEED"
        elif fit_score >= 50:
            assert rec == "PROCEED_WITH_CAUTION"
        else:
            assert rec == "PASS"


# ============================================================================
# 5. LLM Client validate_model_name Tests
# ============================================================================


@pytest.mark.property
class TestValidateModelNameProperty:
    """Property tests for validate_model_name."""

    @given(
        provider=st.sampled_from(["anthropic", "openai", "google", "meta"]),
        model_name=st.text(min_size=1, max_size=100).filter(lambda s: "/" not in s),
    )
    @settings(max_examples=100)
    def test_valid_format_returns_true(self, provider, model_name):
        assert validate_model_name(f"{provider}/{model_name}") is True

    @given(provider=st.sampled_from(["anthropic", "openai", "google", "meta"]))
    @settings(max_examples=20)
    def test_empty_model_name_returns_false(self, provider):
        assert validate_model_name(f"{provider}/") is False

    @given(
        provider=st.text(min_size=1, max_size=50).filter(
            lambda s: s not in {"anthropic", "openai", "google", "meta"} and "/" not in s
        ),
        model_name=st.text(min_size=1, max_size=50).filter(lambda s: "/" not in s),
    )
    @settings(max_examples=100)
    def test_invalid_provider_returns_false(self, provider, model_name):
        assert validate_model_name(f"{provider}/{model_name}") is False

    @given(model=st.text(max_size=100).filter(lambda s: s.count("/") != 1))
    @settings(max_examples=100)
    def test_wrong_format_returns_false(self, model):
        assert validate_model_name(model) is False

    @given(arbitrary=st.text(max_size=200))
    @settings(max_examples=200)
    def test_never_crashes(self, arbitrary):
        result = validate_model_name(arbitrary)
        assert isinstance(result, bool)
