"""
Unit tests for agent modules to reach 90%+ coverage.

Covers:
- ExecutiveSynthesizerAgent (executive_synthesizer.py)
- DifferentiatorAgent (differentiator.py)
- InterrogatorPrepperAgent (interrogator_prepper.py)
- TailoringAgent (tailoring_agent.py)
- model_config.py
- llm_client.py
- telemetry.py
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock

from crewai import LLM

from runtime.crewai.base_agent import ValidationError


def _make_llm():
    return LLM(model="gpt-4", api_key="test-key")


# ============================================================================
# ExecutiveSynthesizerAgent Tests
# ============================================================================

@pytest.mark.unit
class TestExecutiveSynthesizerAgent:
    @pytest.fixture
    def agent(self):
        from runtime.crewai.agents.executive_synthesizer import ExecutiveSynthesizerAgent
        return ExecutiveSynthesizerAgent(_make_llm())

    def test_init(self, agent):
        assert agent.role == "Executive Synthesizer"
        assert agent._custom_prompt is not None
        assert "Executive Synthesizer" in agent._custom_prompt

    def test_get_executive_prompt(self, agent):
        prompt = agent._get_executive_prompt()
        assert "decision" in prompt.lower()
        assert "STRONG_PROCEED" in prompt

    @patch('runtime.crewai.base_agent.Crew')
    def test_execute_success(self, mock_crew_class, agent):
        mock_crew = Mock()
        mock_crew.kickoff.return_value = '{"agent":"Executive Synthesizer","confidence":0.9,"decision":{"recommendation":"PROCEED","fit_score":75,"rationale":"Good fit"}}'
        mock_crew_class.return_value = mock_crew

        context = {
            "job_description": "JD text",
            "resume": "Resume text",
            "gap_analysis": {"gaps": []},
            "interview_notes": "notes",
            "differentiation": {"differentiators": []},
            "tailored_resume": "resume",
            "tailored_cover_letter": "letter",
            "audit_report": {"status": "APPROVED"},
        }
        result = agent.execute(context)
        assert result["decision"]["recommendation"] == "PROCEED"

    @patch('runtime.crewai.base_agent.Crew')
    def test_execute_missing_context_keys(self, mock_crew_class, agent):
        """Execute with missing context keys uses defaults ('Not provided'/'Not available')"""
        mock_crew = Mock()
        mock_crew.kickoff.return_value = '{"agent":"Executive Synthesizer","confidence":0.9,"decision":{"recommendation":"PASS","fit_score":30}}'
        mock_crew_class.return_value = mock_crew

        result = agent.execute({})
        assert "decision" in result

    # --- _validate_schema tests ---

    def test_validate_schema_valid_decision(self, agent):
        data = {"decision": {"recommendation": "PROCEED", "fit_score": 75, "rationale": "ok"}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PROCEED"

    def test_validate_schema_strong_proceed(self, agent):
        data = {"decision": {"recommendation": "STRONG_PROCEED", "fit_score": 90}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "STRONG_PROCEED"

    def test_validate_schema_nested_in_executive_brief(self, agent):
        data = {"executive_brief": {"decision": {"recommendation": "PASS", "fit_score": 20}}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PASS"

    def test_validate_schema_nested_in_summary(self, agent):
        data = {"summary": {"decision": {"recommendation": "PROCEED", "fit_score": 70}}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PROCEED"

    def test_validate_schema_nested_in_analysis(self, agent):
        data = {"analysis": {"decision": {"recommendation": "PROCEED_WITH_CAUTION", "fit_score": 55}}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PROCEED_WITH_CAUTION"

    def test_validate_schema_nested_in_result(self, agent):
        data = {"result": {"decision": {"recommendation": "PROCEED", "fit_score": 70}}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PROCEED"

    def test_validate_schema_nested_in_output(self, agent):
        data = {"output": {"decision": {"recommendation": "PASS", "fit_score": 10}}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PASS"

    def test_validate_schema_nested_in_brief(self, agent):
        data = {"brief": {"decision": {"recommendation": "PROCEED", "fit_score": 70}}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PROCEED"

    def test_validate_schema_flat_recommendation(self, agent):
        """recommendation at root level, no 'decision' key"""
        data = {"recommendation": "PROCEED", "fit_score": 70, "rationale": "Good match"}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PROCEED"
        assert data["decision"]["fit_score"] == 70

    def test_validate_schema_infer_from_fit_score_high(self, agent):
        """No decision or recommendation, but fit_score >= 80 -> STRONG_PROCEED"""
        data = {"fit_score": 85}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "STRONG_PROCEED"

    def test_validate_schema_infer_from_fit_score_medium(self, agent):
        data = {"fit_score": 70}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PROCEED"

    def test_validate_schema_infer_from_fit_score_caution(self, agent):
        data = {"fit_score": 55}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PROCEED_WITH_CAUTION"

    def test_validate_schema_infer_from_fit_score_low(self, agent):
        data = {"fit_score": 30}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PASS"

    def test_validate_schema_infer_from_score_key(self, agent):
        data = {"score": 90}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "STRONG_PROCEED"

    def test_validate_schema_infer_from_match_score(self, agent):
        data = {"match_score": 40}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PASS"

    def test_validate_schema_string_fit_score(self, agent):
        data = {"fit_score": "75%"}
        agent._validate_schema(data)
        assert data["decision"]["fit_score"] == 75

    def test_validate_schema_invalid_string_fit_score(self, agent):
        data = {"fit_score": "abc"}
        agent._validate_schema(data)
        assert data["decision"]["fit_score"] == 50  # Default mid-range

    def test_validate_schema_no_decision_infers_pass(self, agent):
        """When no decision found, infers from fit_score (defaults to 0 -> PASS)"""
        data = {"some_key": "some_value"}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PASS"
        assert data["decision"]["fit_score"] == 0

    def test_validate_schema_decision_missing_recommendation(self, agent):
        data = {"decision": {"fit_score": 70}}
        with pytest.raises(ValidationError, match="must include 'recommendation'"):
            agent._validate_schema(data)

    def test_validate_schema_decision_verdict_alias(self, agent):
        data = {"decision": {"verdict": "PROCEED", "fit_score": 70}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PROCEED"

    def test_validate_schema_decision_status_alias(self, agent):
        data = {"decision": {"status": "PASS", "fit_score": 20}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PASS"

    def test_validate_schema_decision_result_alias(self, agent):
        data = {"decision": {"result": "PROCEED", "fit_score": 70}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PROCEED"

    def test_validate_schema_normalize_caution(self, agent):
        data = {"decision": {"recommendation": "CAUTION", "fit_score": 50}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PROCEED_WITH_CAUTION"

    def test_validate_schema_normalize_reject(self, agent):
        data = {"decision": {"recommendation": "REJECT", "fit_score": 10}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PASS"

    def test_validate_schema_normalize_no(self, agent):
        data = {"decision": {"recommendation": "NO", "fit_score": 10}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PASS"

    def test_validate_schema_normalize_yes(self, agent):
        data = {"decision": {"recommendation": "YES", "fit_score": 70}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PROCEED"

    def test_validate_schema_normalize_approved(self, agent):
        data = {"decision": {"recommendation": "APPROVED", "fit_score": 70}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PROCEED"

    def test_validate_schema_normalize_strong_yes(self, agent):
        data = {"decision": {"recommendation": "STRONG_YES", "fit_score": 90}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "STRONG_PROCEED"

    def test_validate_schema_unknown_recommendation_defaults(self, agent):
        data = {"decision": {"recommendation": "MAYBE", "fit_score": 60}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PROCEED"  # Default

    def test_validate_schema_decision_as_string(self, agent):
        data = {"decision": "PROCEED"}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PROCEED"

    def test_validate_schema_decision_as_invalid_string(self, agent):
        data = {"decision": "MAYBE_LATER"}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PROCEED"  # Default

    def test_validate_schema_decision_invalid_type(self, agent):
        data = {"decision": 42}
        with pytest.raises(ValidationError, match="must be a dict or string"):
            agent._validate_schema(data)

    def test_validate_schema_fit_score_at_root_promoted(self, agent):
        data = {"decision": {"recommendation": "PROCEED"}, "fit_score": 80}
        agent._validate_schema(data)
        assert data["decision"]["fit_score"] == 80

    def test_validate_schema_fit_score_missing_defaults_zero(self, agent):
        data = {"decision": {"recommendation": "PROCEED"}}
        agent._validate_schema(data)
        assert data["decision"]["fit_score"] == 0

    def test_validate_schema_fit_score_string_in_decision(self, agent):
        data = {"decision": {"recommendation": "PROCEED", "fit_score": "85%"}}
        agent._validate_schema(data)
        assert data["decision"]["fit_score"] == 85

    def test_validate_schema_fit_score_invalid_string_in_decision(self, agent):
        data = {"decision": {"recommendation": "PROCEED", "fit_score": "high"}}
        agent._validate_schema(data)
        assert data["decision"]["fit_score"] == 0

    def test_validate_schema_normalize_hyphen_spaces(self, agent):
        """Tests normalization of hyphens and spaces in recommendation"""
        data = {"decision": {"recommendation": "proceed-with-caution", "fit_score": 55}}
        agent._validate_schema(data)
        assert data["decision"]["recommendation"] == "PROCEED_WITH_CAUTION"


# ============================================================================
# DifferentiatorAgent Tests
# ============================================================================

@pytest.mark.unit
class TestDifferentiatorAgent:
    @pytest.fixture
    def agent(self):
        from runtime.crewai.agents.differentiator import DifferentiatorAgent
        with patch('runtime.crewai.base_agent.Path.read_text', return_value="Test prompt"):
            return DifferentiatorAgent(_make_llm())

    def test_init(self, agent):
        assert agent.role == "Differentiator"

    def test_execute_missing_job_description(self, agent):
        with pytest.raises(ValidationError, match="job_description"):
            agent.execute({"resume": "r", "interview_notes": "n", "gap_analysis": "g"})

    def test_execute_missing_resume(self, agent):
        with pytest.raises(ValidationError, match="resume"):
            agent.execute({"job_description": "j", "interview_notes": "n", "gap_analysis": "g"})

    def test_execute_missing_interview_notes(self, agent):
        with pytest.raises(ValidationError, match="interview_notes"):
            agent.execute({"job_description": "j", "resume": "r", "gap_analysis": "g"})

    def test_execute_missing_gap_analysis(self, agent):
        with pytest.raises(ValidationError, match="gap_analysis"):
            agent.execute({"job_description": "j", "resume": "r", "interview_notes": "n"})

    @patch('runtime.crewai.base_agent.Crew')
    def test_execute_success(self, mock_crew_class, agent):
        mock_crew = Mock()
        mock_crew.kickoff.return_value = '{"agent":"Differentiator","confidence":0.9,"differentiators":["skill1"]}'
        mock_crew_class.return_value = mock_crew

        result = agent.execute({
            "job_description": "JD",
            "resume": "Resume",
            "interview_notes": "Notes",
            "gap_analysis": "Analysis",
        })
        assert "differentiators" in result

    def test_validate_schema(self, agent):
        """_validate_schema just calls super, should not raise for valid data"""
        data = {"some_key": "some_value"}
        agent._validate_schema(data)


# ============================================================================
# InterrogatorPrepperAgent Tests
# ============================================================================

@pytest.mark.unit
class TestInterrogatorPrepperAgent:
    @pytest.fixture
    def agent(self):
        from runtime.crewai.agents.interrogator_prepper import InterrogatorPrepperAgent
        with patch('runtime.crewai.base_agent.Path.read_text', return_value="Test prompt"):
            return InterrogatorPrepperAgent(_make_llm())

    def test_init(self, agent):
        assert agent.role == "Interrogator-Prepper"

    def test_execute_missing_job_description(self, agent):
        with pytest.raises(ValidationError, match="job_description"):
            agent.execute({"resume": "r", "gaps": [], "gap_analysis": "g"})

    def test_execute_missing_resume(self, agent):
        with pytest.raises(ValidationError, match="resume"):
            agent.execute({"job_description": "j", "gaps": [], "gap_analysis": "g"})

    def test_execute_missing_gaps(self, agent):
        with pytest.raises(ValidationError, match="gaps"):
            agent.execute({"job_description": "j", "resume": "r", "gap_analysis": "g"})

    def test_execute_missing_gap_analysis(self, agent):
        with pytest.raises(ValidationError, match="gap_analysis"):
            agent.execute({"job_description": "j", "resume": "r", "gaps": []})

    @patch('runtime.crewai.base_agent.Crew')
    def test_execute_success(self, mock_crew_class, agent):
        mock_crew = Mock()
        mock_crew.kickoff.return_value = '{"agent":"Interrogator-Prepper","confidence":0.9,"questions":[]}'
        mock_crew_class.return_value = mock_crew

        result = agent.execute({
            "job_description": "JD",
            "resume": "Resume",
            "gaps": ["gap1"],
            "gap_analysis": "Analysis",
        })
        assert "questions" in result

    def test_validate_schema(self, agent):
        data = {"some_key": "some_value"}
        agent._validate_schema(data)


# ============================================================================
# TailoringAgent Tests
# ============================================================================

@pytest.mark.unit
class TestTailoringAgent:
    @pytest.fixture
    def agent(self):
        from runtime.crewai.agents.tailoring_agent import TailoringAgent
        with patch('runtime.crewai.base_agent.Path.read_text', return_value="Test prompt"):
            return TailoringAgent(_make_llm())

    def test_init(self, agent):
        assert agent.role == "Tailoring Agent"

    def test_execute_missing_job_description(self, agent):
        with pytest.raises(ValidationError, match="job_description"):
            agent.execute({"resume": "r", "interview_notes": "n", "differentiators": [], "gap_analysis": "g"})

    def test_execute_missing_resume(self, agent):
        with pytest.raises(ValidationError, match="resume"):
            agent.execute({"job_description": "j", "interview_notes": "n", "differentiators": [], "gap_analysis": "g"})

    def test_execute_missing_interview_notes(self, agent):
        with pytest.raises(ValidationError, match="interview_notes"):
            agent.execute({"job_description": "j", "resume": "r", "differentiators": [], "gap_analysis": "g"})

    def test_execute_missing_differentiators(self, agent):
        with pytest.raises(ValidationError, match="differentiators"):
            agent.execute({"job_description": "j", "resume": "r", "interview_notes": "n", "gap_analysis": "g"})

    def test_execute_missing_gap_analysis(self, agent):
        with pytest.raises(ValidationError, match="gap_analysis"):
            agent.execute({"job_description": "j", "resume": "r", "interview_notes": "n", "differentiators": []})

    @patch('runtime.crewai.base_agent.Crew')
    def test_execute_success(self, mock_crew_class, agent):
        mock_crew = Mock()
        mock_crew.kickoff.return_value = '{"agent":"Tailoring Agent","confidence":0.9,"tailored_output":{"resume":"content"}}'
        mock_crew_class.return_value = mock_crew

        result = agent.execute({
            "job_description": "JD",
            "resume": "Resume",
            "interview_notes": "Notes",
            "differentiators": ["diff1"],
            "gap_analysis": "Analysis",
        })
        assert "tailored_output" in result

    def test_validate_schema(self, agent):
        data = {"some_key": "some_value"}
        agent._validate_schema(data)


# ============================================================================
# model_config Tests
# ============================================================================

@pytest.mark.unit
class TestModelConfig:

    def test_get_agent_model_info_known(self):
        from runtime.crewai.model_config import get_agent_model_info
        info = get_agent_model_info("gap_analyzer")
        assert info["provider"] == "chutes"
        assert "deepseek" in info["model"].lower()

    def test_get_agent_model_info_unknown(self):
        from runtime.crewai.model_config import get_agent_model_info
        info = get_agent_model_info("nonexistent_agent")
        assert info["provider"] == "unknown"
        assert info["model"] == "unknown"

    def test_get_all_required_env_vars(self):
        from runtime.crewai.model_config import get_all_required_env_vars
        vars = get_all_required_env_vars()
        assert "CHUTES_API_KEY" in vars
        assert "TOGETHER_API_KEY" in vars
        assert "ANTHROPIC_API_KEY" in vars

    @patch.dict(os.environ, {"CHUTES_API_KEY": "test-key"}, clear=False)
    def test_get_llm_for_agent_chutes(self):
        from runtime.crewai.model_config import get_llm_for_agent
        llm = get_llm_for_agent("gap_analyzer")
        assert llm is not None

    @patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}, clear=False)
    def test_get_llm_for_agent_together(self):
        from runtime.crewai.model_config import get_llm_for_agent
        llm = get_llm_for_agent("ats_optimizer")
        assert llm is not None

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
    def test_get_llm_for_agent_anthropic(self):
        from runtime.crewai.model_config import get_llm_for_agent
        llm = get_llm_for_agent("differentiator")
        assert llm is not None

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test"}, clear=False)
    def test_get_llm_for_agent_anthropic_via_openrouter(self):
        from runtime.crewai.model_config import get_llm_for_agent
        # Anthropic without ANTHROPIC_API_KEY falls back to OpenRouter
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            os.environ["OPENROUTER_API_KEY"] = "sk-or-test"
            llm = get_llm_for_agent("differentiator")
            assert llm is not None

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False)
    def test_get_llm_for_agent_openai(self):
        from runtime.crewai.model_config import get_llm_for_agent
        llm = get_llm_for_agent("auditor_suite")
        assert llm is not None

    @patch.dict(os.environ, {}, clear=True)
    def test_get_llm_for_agent_no_keys_raises(self):
        from runtime.crewai.model_config import get_llm_for_agent, LLMClientError
        with pytest.raises(LLMClientError, match="No valid API key"):
            get_llm_for_agent("gap_analyzer")

    @patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}, clear=True)
    def test_get_llm_for_agent_fallback_only(self):
        from runtime.crewai.model_config import get_llm_for_agent
        # differentiator primary is anthropic, fallback is together
        llm = get_llm_for_agent("differentiator", fallback_only=True)
        assert llm is not None

    @patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}, clear=True)
    def test_get_llm_for_agent_unknown_agent_fallback(self):
        from runtime.crewai.model_config import get_llm_for_agent
        llm = get_llm_for_agent("unknown_agent_type")
        assert llm is not None

    @patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}, clear=True)
    def test_get_llm_for_agent_last_resort_together(self):
        from runtime.crewai.model_config import get_llm_for_agent
        # gap_analyzer needs CHUTES_API_KEY, not available; should fall to last resort Together
        llm = get_llm_for_agent("gap_analyzer")
        assert llm is not None

    def test_create_llm_unknown_provider(self):
        from runtime.crewai.model_config import _create_llm, LLMClientError
        with pytest.raises(LLMClientError, match="Unknown provider"):
            _create_llm("unknown_provider", "model", 0.5, {})

    @patch.dict(os.environ, {}, clear=True)
    def test_create_llm_chutes_no_key(self):
        from runtime.crewai.model_config import _create_llm, LLMClientError
        with pytest.raises(LLMClientError, match="CHUTES_API_KEY"):
            _create_llm("chutes", "model", 0.5, {})

    @patch.dict(os.environ, {}, clear=True)
    def test_create_llm_anthropic_no_key(self):
        from runtime.crewai.model_config import _create_llm, LLMClientError
        with pytest.raises(LLMClientError, match="ANTHROPIC_API_KEY"):
            _create_llm("anthropic", "model", 0.5, {})

    @patch.dict(os.environ, {}, clear=True)
    def test_create_llm_together_no_key(self):
        from runtime.crewai.model_config import _create_llm, LLMClientError
        with pytest.raises(LLMClientError, match="TOGETHER_API_KEY"):
            _create_llm("together", "model", 0.5, {})

    @patch.dict(os.environ, {}, clear=True)
    def test_create_llm_openai_no_key(self):
        from runtime.crewai.model_config import _create_llm, LLMClientError
        with pytest.raises(LLMClientError, match="OPENAI_API_KEY"):
            _create_llm("openai", "model", 0.5, {})


# ============================================================================
# llm_client Tests
# ============================================================================

@pytest.mark.unit
class TestLLMClient:

    @patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}, clear=True)
    def test_get_llm_client_together(self):
        from runtime.crewai.llm_client import get_llm_client
        llm = get_llm_client()
        assert llm is not None

    @patch.dict(os.environ, {"CHUTES_API_KEY": "test-key"}, clear=True)
    def test_get_llm_client_chutes(self):
        from runtime.crewai.llm_client import get_llm_client
        llm = get_llm_client()
        assert llm is not None

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test"}, clear=True)
    def test_get_llm_client_openrouter(self):
        from runtime.crewai.llm_client import get_llm_client
        llm = get_llm_client()
        assert llm is not None

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "invalid-key"}, clear=True)
    def test_get_llm_client_invalid_openrouter_key(self):
        from runtime.crewai.llm_client import get_llm_client, LLMClientError
        with pytest.raises(LLMClientError, match="sk-or-"):
            get_llm_client()

    @patch.dict(os.environ, {}, clear=True)
    def test_get_llm_client_no_keys(self):
        from runtime.crewai.llm_client import get_llm_client, LLMClientError
        with pytest.raises(LLMClientError, match="API key is required"):
            get_llm_client()

    @patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}, clear=True)
    def test_get_llm_client_with_explicit_api_key(self):
        from runtime.crewai.llm_client import get_llm_client
        llm = get_llm_client(api_key="explicit-key")
        assert llm is not None

    @patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}, clear=True)
    def test_get_llm_client_with_model_override(self):
        from runtime.crewai.llm_client import get_llm_client
        llm = get_llm_client(model="custom-model")
        assert llm is not None

    def test_validate_model_name_valid(self):
        from runtime.crewai.llm_client import validate_model_name
        assert validate_model_name("anthropic/claude-sonnet-4.5") is True
        assert validate_model_name("openai/gpt-4") is True
        assert validate_model_name("google/gemini-pro") is True
        assert validate_model_name("meta/llama-3") is True

    def test_validate_model_name_invalid(self):
        from runtime.crewai.llm_client import validate_model_name
        assert validate_model_name("just-a-model") is False
        assert validate_model_name("unknown/model") is False
        assert validate_model_name("anthropic/") is False
        assert validate_model_name("too/many/parts") is False

    def test_get_available_models(self):
        from runtime.crewai.llm_client import get_available_models
        models = get_available_models()
        assert len(models) > 0
        assert "anthropic/claude-sonnet-4.5" in models

    def test_retry_handler_success_first(self):
        from runtime.crewai.llm_client import LLMRetryHandler
        handler = LLMRetryHandler(max_retries=2, base_delay=0.01)
        result = handler.execute_with_retry(lambda: "success")
        assert result == "success"

    def test_retry_handler_success_after_retry(self):
        from runtime.crewai.llm_client import LLMRetryHandler
        handler = LLMRetryHandler(max_retries=2, base_delay=0.01)
        call_count = [0]
        def flaky():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("fail")
            return "success"
        result = handler.execute_with_retry(flaky)
        assert result == "success"
        assert call_count[0] == 2

    def test_retry_handler_all_retries_fail(self):
        from runtime.crewai.llm_client import LLMRetryHandler, LLMClientError
        handler = LLMRetryHandler(max_retries=1, base_delay=0.01)
        with pytest.raises(LLMClientError, match="Failed after"):
            handler.execute_with_retry(lambda: (_ for _ in ()).throw(Exception("always fail")))


# ============================================================================
# Telemetry Tests
# ============================================================================

@pytest.mark.unit
class TestTelemetry:

    def test_noop_span(self):
        from runtime.crewai.telemetry import NoOpSpan
        span = NoOpSpan()
        # All methods should be callable without error
        span.set_attribute("key", "value")
        span.set_attributes({"key": "value"})
        span.add_event("event")
        span.add_event("event", {"attr": "val"})
        span.record_exception(Exception("test"))
        span.set_status("ok")
        span.end()
        assert span.is_recording is False

    @patch.dict(os.environ, {"OTEL_ENABLED": "false"}, clear=False)
    def test_get_tracer_disabled(self):
        from runtime.crewai.telemetry import get_tracer
        import runtime.crewai.telemetry as tel
        tel._tracer = None  # Reset cache
        tracer = get_tracer()
        assert tracer is None

    def test_trace_workflow_stage_noop(self):
        from runtime.crewai.telemetry import trace_workflow_stage, NoOpSpan
        with trace_workflow_stage("test_stage") as span:
            assert isinstance(span, NoOpSpan)

    def test_trace_workflow_stage_with_attributes(self):
        from runtime.crewai.telemetry import trace_workflow_stage, NoOpSpan
        with trace_workflow_stage("test_stage", {"key": "val"}) as span:
            assert isinstance(span, NoOpSpan)

    def test_trace_agent_execution_noop(self):
        from runtime.crewai.telemetry import trace_agent_execution, NoOpSpan
        with trace_agent_execution("Test Agent") as span:
            assert isinstance(span, NoOpSpan)

    def test_trace_agent_execution_with_attributes(self):
        from runtime.crewai.telemetry import trace_agent_execution, NoOpSpan
        with trace_agent_execution("Test Agent", {"key": "val"}) as span:
            assert isinstance(span, NoOpSpan)

    def test_trace_task_execution_noop(self):
        from runtime.crewai.telemetry import trace_task_execution, NoOpSpan
        with trace_task_execution("test_task", "Test Agent") as span:
            assert isinstance(span, NoOpSpan)

    def test_trace_task_execution_with_attributes(self):
        from runtime.crewai.telemetry import trace_task_execution, NoOpSpan
        with trace_task_execution("test_task", "Test Agent", {"key": "val"}) as span:
            assert isinstance(span, NoOpSpan)

    def test_record_agent_error_noop_span(self):
        from runtime.crewai.telemetry import record_agent_error, NoOpSpan
        # Should not raise
        record_agent_error(NoOpSpan(), Exception("test"), "Test Agent")

    def test_record_agent_error_none_span(self):
        from runtime.crewai.telemetry import record_agent_error
        # Should not raise
        record_agent_error(None, Exception("test"), "Test Agent")

    def test_record_agent_result_noop_span(self):
        from runtime.crewai.telemetry import record_agent_result, NoOpSpan
        # Should not raise
        record_agent_result(NoOpSpan(), {"confidence": 0.9}, "Test Agent")

    def test_record_agent_result_none_span(self):
        from runtime.crewai.telemetry import record_agent_result
        # Should not raise
        record_agent_result(None, {"confidence": 0.9}, "Test Agent")

    @patch.dict(os.environ, {"OTEL_ENABLED": "true"}, clear=False)
    def test_get_tracer_enabled(self):
        from runtime.crewai.telemetry import get_tracer
        import runtime.crewai.telemetry as tel
        tel._tracer = None  # Reset cache
        tracer = get_tracer()
        # Should return a real tracer when otel is available
        assert tracer is not None

    @patch.dict(os.environ, {"OTEL_ENABLED": "true"}, clear=False)
    def test_trace_workflow_stage_real(self):
        from runtime.crewai.telemetry import trace_workflow_stage, NoOpSpan
        import runtime.crewai.telemetry as tel
        tel._tracer = None
        with trace_workflow_stage("test_stage") as span:
            # Should be a real span, not NoOp
            assert not isinstance(span, NoOpSpan)
            span.set_attribute("test.key", "test_value")

    @patch.dict(os.environ, {"OTEL_ENABLED": "true"}, clear=False)
    def test_record_agent_error_real_span(self):
        from runtime.crewai.telemetry import trace_agent_execution, record_agent_error, NoOpSpan
        import runtime.crewai.telemetry as tel
        tel._tracer = None
        with trace_agent_execution("Test Agent") as span:
            record_agent_error(span, ValueError("test error"), "Test Agent")

    @patch.dict(os.environ, {"OTEL_ENABLED": "true"}, clear=False)
    def test_record_agent_result_real_span(self):
        from runtime.crewai.telemetry import trace_agent_execution, record_agent_result, NoOpSpan
        import runtime.crewai.telemetry as tel
        tel._tracer = None
        with trace_agent_execution("Test Agent") as span:
            record_agent_result(span, {"confidence": 0.95}, "Test Agent")

    @patch.dict(os.environ, {"OTEL_ENABLED": "true"}, clear=False)
    def test_record_agent_result_no_confidence(self):
        from runtime.crewai.telemetry import trace_agent_execution, record_agent_result
        import runtime.crewai.telemetry as tel
        tel._tracer = None
        with trace_agent_execution("Test Agent") as span:
            record_agent_result(span, {"no_confidence_key": "value"}, "Test Agent")

    @patch.dict(os.environ, {"OTEL_ENABLED": "1"}, clear=False)
    def test_get_tracer_enabled_with_1(self):
        from runtime.crewai.telemetry import get_tracer
        import runtime.crewai.telemetry as tel
        tel._tracer = None
        assert get_tracer() is not None

    @patch.dict(os.environ, {"OTEL_ENABLED": "yes"}, clear=False)
    def test_get_tracer_enabled_with_yes(self):
        from runtime.crewai.telemetry import get_tracer
        import runtime.crewai.telemetry as tel
        tel._tracer = None
        assert get_tracer() is not None

    def test_get_tracer_cached(self):
        """Second call returns cached tracer"""
        from runtime.crewai.telemetry import get_tracer
        import runtime.crewai.telemetry as tel
        tel._tracer = Mock()  # Set a fake cached tracer
        result = get_tracer()
        assert result is tel._tracer
        tel._tracer = None  # Clean up
