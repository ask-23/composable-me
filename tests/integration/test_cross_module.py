"""
Integration tests for cross-module interactions.

Tests the interplay between LLM client, model config, telemetry, agents,
CLI, and crew modules to ensure they work together correctly.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from runtime.crewai.base_agent import BaseHydraAgent


class _TestAgent(BaseHydraAgent):
    role = "Integration Test Agent"
    goal = "Test integration"
    expected_output = "JSON output"

    def execute(self, context):
        return {"result": "test"}


def _mock_llm():
    from crewai import LLM
    return LLM(model="gpt-4", api_key="test-key")


# ============================================================================
# 1. LLM Client + Model Config Integration
# ============================================================================

@pytest.mark.integration
class TestLLMConfigIntegration:
    """Test LLM client and model config work together."""

    @patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}, clear=True)
    def test_model_config_creates_usable_llm(self):
        """get_llm_for_agent returns an LLM that can be used to create agents."""
        from runtime.crewai.model_config import get_llm_for_agent
        llm = get_llm_for_agent("ats_optimizer")
        # Should be usable to create an agent
        agent = _TestAgent(llm)
        assert agent.llm is llm

    @patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}, clear=True)
    def test_all_agent_types_get_llm(self):
        """All configured agent types should get an LLM (via fallback if needed)."""
        from runtime.crewai.model_config import AGENT_MODELS, get_llm_for_agent
        for agent_type in AGENT_MODELS:
            llm = get_llm_for_agent(agent_type)
            assert llm is not None, f"Failed to get LLM for {agent_type}"

    @patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}, clear=True)
    def test_llm_client_and_model_config_produce_same_result(self):
        """Both modules should produce working LLMs."""
        from runtime.crewai.llm_client import get_llm_client
        from runtime.crewai.model_config import get_llm_for_agent

        llm1 = get_llm_client()
        llm2 = get_llm_for_agent("ats_optimizer")

        # Both should be LLM instances
        assert llm1 is not None
        assert llm2 is not None

    @patch.dict(os.environ, {}, clear=True)
    def test_both_modules_fail_gracefully_without_keys(self):
        """Both modules should raise clear errors when no API keys are set."""
        from runtime.crewai.llm_client import LLMClientError as LLC
        from runtime.crewai.llm_client import get_llm_client
        from runtime.crewai.model_config import LLMClientError as MLC
        from runtime.crewai.model_config import get_llm_for_agent

        with pytest.raises(LLC):
            get_llm_client()
        with pytest.raises(MLC):
            get_llm_for_agent("gap_analyzer")

    def test_retry_handler_with_llm_client_error(self):
        """Retry handler properly wraps LLM client errors."""
        from runtime.crewai.llm_client import LLMClientError, LLMRetryHandler
        handler = LLMRetryHandler(max_retries=1, base_delay=0.01)

        with pytest.raises(LLMClientError, match="Failed after"):
            handler.execute_with_retry(lambda: (_ for _ in ()).throw(ValueError("api error")))

    @patch.dict(os.environ, {"TOGETHER_API_KEY": "tgp_v1_test"}, clear=True)
    def test_model_config_fallback_chain(self):
        """Agents with anthropic primary should fall through to together fallback."""
        from runtime.crewai.model_config import get_llm_for_agent
        # differentiator primary is anthropic, but we only have TOGETHER_API_KEY
        llm = get_llm_for_agent("differentiator")
        assert llm is not None


# ============================================================================
# 2. Telemetry + Workflow Integration
# ============================================================================

@pytest.mark.integration
class TestTelemetryIntegration:
    """Test telemetry works correctly with workflow stages."""

    def test_noop_telemetry_doesnt_break_workflow(self):
        """Workflow should work fine when telemetry is disabled."""
        import runtime.crewai.telemetry as tel
        from runtime.crewai.telemetry import NoOpSpan, trace_workflow_stage
        tel._tracer = None  # Reset cached tracer

        with patch.dict(os.environ, {"OTEL_ENABLED": "false"}, clear=False):
            tel._tracer = None
            with trace_workflow_stage("test_stage") as span:
                assert isinstance(span, NoOpSpan)
            span.set_attribute("test", "value")
            span.add_event("test_event")
            span.set_attributes({"a": 1, "b": 2})

    @patch.dict(os.environ, {"OTEL_ENABLED": "true"}, clear=False)
    def test_real_telemetry_workflow_stage(self):
        """Real telemetry spans record attributes correctly."""
        import runtime.crewai.telemetry as tel
        from runtime.crewai.telemetry import NoOpSpan, trace_workflow_stage
        tel._tracer = None

        with trace_workflow_stage("gap_analysis", {"max_retries": 2}) as span:
            assert not isinstance(span, NoOpSpan)
            span.set_attribute("stage.gaps_found", 5)
            span.set_attribute("stage.confidence", 0.95)

    @patch.dict(os.environ, {"OTEL_ENABLED": "true"}, clear=False)
    def test_telemetry_agent_execution_trace(self):
        """Agent execution tracing works end-to-end."""
        import runtime.crewai.telemetry as tel
        from runtime.crewai.telemetry import (
            NoOpSpan,
            record_agent_error,
            record_agent_result,
            trace_agent_execution,
        )
        tel._tracer = None

        with trace_agent_execution("Gap Analyzer", {"job_id": "test-123"}) as span:
            assert not isinstance(span, NoOpSpan)
            record_agent_result(span, {"confidence": 0.9, "gaps": []}, "Gap Analyzer")

        # Error case
        with trace_agent_execution("Auditor Suite") as span:
            record_agent_error(span, ValueError("test"), "Auditor Suite")

    @patch.dict(os.environ, {"OTEL_ENABLED": "true"}, clear=False)
    def test_telemetry_task_execution_trace(self):
        """Task execution tracing with attributes."""
        import runtime.crewai.telemetry as tel
        from runtime.crewai.telemetry import NoOpSpan, trace_task_execution
        tel._tracer = None

        with trace_task_execution("analyze_gaps", "Gap Analyzer", {"retry": 0}) as span:
            assert not isinstance(span, NoOpSpan)
            span.set_attribute("task.result", "success")

    def test_telemetry_tracer_caching(self):
        """Tracer should be cached after first creation."""
        import runtime.crewai.telemetry as tel

        fake_tracer = Mock()
        tel._tracer = fake_tracer

        result = tel.get_tracer()
        assert result is fake_tracer

        tel._tracer = None  # Clean up


# ============================================================================
# 3. Agent + Base Agent Integration
# ============================================================================

@pytest.mark.integration
class TestAgentIntegration:
    """Test agents work correctly through BaseHydraAgent."""

    def test_agent_creates_crewai_agent(self):
        """BaseHydraAgent.create_agent produces a valid CrewAI Agent."""
        agent = _TestAgent(_mock_llm())
        crewai_agent = agent.create_agent()
        assert crewai_agent.role == "Integration Test Agent"
        assert crewai_agent.goal == "Test integration"

    def test_agent_creates_crewai_task(self):
        """BaseHydraAgent.create_task produces a valid CrewAI Task."""
        agent = _TestAgent(_mock_llm())
        task = agent.create_task("Analyze the job description")
        assert "Analyze the job description" in task.description
        assert "valid JSON" in task.description

    @patch('runtime.crewai.base_agent.Crew')
    def test_agent_execute_with_retry_integration(self, mock_crew_class):
        """execute_with_retry properly orchestrates Crew execution and validation."""
        mock_crew = Mock()
        mock_crew.kickoff.return_value = '{"agent":"Test","confidence":0.85,"result":"analyzed"}'
        mock_crew_class.return_value = mock_crew

        agent = _TestAgent(_mock_llm())
        task = agent.create_task("Test task")
        result = agent.execute_with_retry(task)

        assert result["confidence"] == 0.85
        assert "agent" in result


    def test_all_agent_types_init_with_mock_llm(self):
        """All agent types can be initialized with a mock LLM."""
        from runtime.crewai.agents.executive_synthesizer import ExecutiveSynthesizerAgent

        llm = _mock_llm()

        # Executive synthesizer uses prompt_path=None
        exec_agent = ExecutiveSynthesizerAgent(llm)
        assert exec_agent.role == "Executive Synthesizer"

        # Other agents need prompt files - mock the file read
        with patch('runtime.crewai.base_agent.Path.read_text', return_value="Test prompt"):
            from runtime.crewai.agents.differentiator import DifferentiatorAgent
            from runtime.crewai.agents.interrogator_prepper import InterrogatorPrepperAgent
            from runtime.crewai.agents.tailoring_agent import TailoringAgent

            diff = DifferentiatorAgent(llm)
            assert diff.role == "Differentiator"

            interr = InterrogatorPrepperAgent(llm)
            assert interr.role == "Interrogator-Prepper"

            tailor = TailoringAgent(llm)
            assert tailor.role == "Tailoring Agent"


# ============================================================================
# 4. CLI + Workflow Integration
# ============================================================================

@pytest.mark.integration
class TestCLIWorkflowIntegration:
    """Test CLI functions work with workflow components."""

    def test_cli_read_file(self):
        """_read_file reads real files correctly."""
        from runtime.crewai.cli import _read_file

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content\nLine 2")
            f.flush()

            content = _read_file(Path(f.name))
            assert content == "Test content\nLine 2"
            os.unlink(f.name)

    def test_cli_read_file_missing(self):
        from runtime.crewai.cli import _read_file
        with pytest.raises(FileNotFoundError):
            _read_file(Path("/nonexistent/path.txt"))

    def test_cli_read_sources(self):
        """_read_sources reads all files in a directory."""
        from runtime.crewai.cli import _read_sources

        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "resume.md").write_text("# Resume")
            (Path(tmpdir) / "cover.md").write_text("Dear Manager")

            content = _read_sources(Path(tmpdir))
            assert "resume.md" in content
            assert "# Resume" in content
            assert "cover.md" in content

    def test_cli_read_sources_empty_dir(self):
        from runtime.crewai.cli import _read_sources
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="No UTF-8"):
                _read_sources(Path(tmpdir))

    def test_cli_read_sources_not_dir(self):
        from runtime.crewai.cli import _read_sources
        with tempfile.NamedTemporaryFile(delete=False) as f:
            with pytest.raises(ValueError, match="must be a directory"):
                _read_sources(Path(f.name))
            os.unlink(f.name)

    def test_cli_build_parser_defaults(self):
        from runtime.crewai.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["--jd", "job.txt", "--resume", "resume.md"])
        assert args.jd == "job.txt"
        assert args.resume == "resume.md"
        assert args.out == "output/"
        assert args.verbose is False
        assert args.interactive is False



# ============================================================================
# 5. Crew Module Integration
# ============================================================================

@pytest.mark.integration


# ============================================================================
# 6. Quick Crew Integration
# ============================================================================

@pytest.mark.integration


# ============================================================================
# 7. Model Validation Integration
# ============================================================================

@pytest.mark.integration
class TestModelValidationIntegration:
    """Test LLM model validation functions."""

    def test_validate_model_name_all_available(self):
        """All models in get_available_models should pass validation."""
        from runtime.crewai.llm_client import get_available_models, validate_model_name
        for model in get_available_models():
            assert validate_model_name(model), f"{model} should be valid"

    def test_model_config_agent_info(self):
        """get_agent_model_info returns consistent data for all agents."""
        from runtime.crewai.model_config import AGENT_MODELS, get_agent_model_info
        for agent_type in AGENT_MODELS:
            info = get_agent_model_info(agent_type)
            assert "provider" in info
            assert "model" in info
            assert "rationale" in info
            assert info["provider"] != "unknown"

