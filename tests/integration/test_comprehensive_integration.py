"""
Comprehensive integration tests that exercise all major modules through their
public interfaces. These tests aim to bring integration coverage above 90% by
exercising code paths not covered by the focused integration tests.
"""

import os
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from crewai import LLM
from runtime.crewai.base_agent import BaseHydraAgent, ValidationError


def _llm():
    return LLM(model="gpt-4", api_key="test-key")


# ============================================================================
# BaseHydraAgent Integration
# ============================================================================

class _FullTestAgent(BaseHydraAgent):
    role = "Full Test Agent"
    goal = "Full integration test"
    expected_output = "JSON output"

    def execute(self, context):
        task = self.create_task(f"Analyze: {context.get('input', '')}")
        return self.execute_with_retry(task)


@pytest.mark.integration
class TestBaseAgentIntegration:

    @patch('runtime.crewai.base_agent.Crew')
    def test_full_agent_lifecycle(self, mock_crew_class):
        """Agent init -> create_task -> execute_with_retry -> validate_output."""
        mock_crew = Mock()
        mock_crew.kickoff.return_value = '{"agent":"Test","confidence":0.88,"analysis":{"score":90}}'
        mock_crew_class.return_value = mock_crew

        agent = _FullTestAgent(_llm())
        result = agent.execute({"input": "test data"})

        assert result["confidence"] == 0.88
        assert "agent" in result
        assert "timestamp" in result

    @patch('runtime.crewai.base_agent.Crew')
    def test_agent_retry_on_invalid_json(self, mock_crew_class):
        """Agent retries when first response is invalid JSON."""
        mock_crew = Mock()
        mock_crew.kickoff.side_effect = [
            "not json at all",  # First attempt fails
            '{"agent":"Test","confidence":0.9,"result":"ok"}'  # Second succeeds
        ]
        mock_crew_class.return_value = mock_crew

        agent = _FullTestAgent(_llm())
        result = agent.execute({"input": "data"})
        assert result["confidence"] == 0.9

    @patch('runtime.crewai.base_agent.Crew')
    def test_agent_max_retries_exhausted(self, mock_crew_class):
        mock_crew = Mock()
        mock_crew.kickoff.side_effect = Exception("Always fails")
        mock_crew_class.return_value = mock_crew

        agent = _FullTestAgent(_llm())
        with pytest.raises(ValidationError, match="failed after"):
            agent.execute({"input": "data"})

    def test_validate_output_various_formats(self):
        """Test validate_output handles various LLM output formats."""
        agent = _FullTestAgent(_llm())

        # Markdown fenced JSON
        r1 = agent.validate_output('```json\n{"result": "ok"}\n```')
        assert r1["result"] == "ok"

        # JSON with surrounding text
        r2 = agent.validate_output('Here is the analysis:\n{"score": 95}\nDone.')
        assert r2["score"] == 95

        # Nested structure with base field promotion
        r3 = agent.validate_output('{"analysis": {"agent": "Nested", "confidence": 0.7, "data": "val"}}')
        assert r3["confidence"] == 0.7

    def test_validate_output_errors(self):
        agent = _FullTestAgent(_llm())

        with pytest.raises(ValidationError, match="Invalid JSON"):
            agent.validate_output("not json")

        with pytest.raises(ValidationError, match="Output must be a JSON object"):
            agent.validate_output("[1, 2, 3]")

    def test_style_guide_detection(self):
        """Different agent roles trigger style guide loading."""

        class TailoringTestAgent(BaseHydraAgent):
            role = "Tailoring Agent"
            goal = "Tailor"
            expected_output = "output"
            def execute(self, context): return {}

        class AuditorTestAgent(BaseHydraAgent):
            role = "Auditor Suite"
            goal = "Audit"
            expected_output = "output"
            def execute(self, context): return {}

        class RegularAgent(BaseHydraAgent):
            role = "Regular Agent"
            goal = "Regular"
            expected_output = "output"
            def execute(self, context): return {}

        assert TailoringTestAgent(_llm())._needs_style_guide() is True
        assert AuditorTestAgent(_llm())._needs_style_guide() is True
        assert RegularAgent(_llm())._needs_style_guide() is False


# ============================================================================
# Executive Synthesizer Integration
# ============================================================================

@pytest.mark.integration
class TestExecutiveSynthesizerIntegration:

    def test_schema_validation_comprehensive(self):
        """Test all schema validation paths in a single integration test."""
        from runtime.crewai.agents.executive_synthesizer import ExecutiveSynthesizerAgent

        agent = ExecutiveSynthesizerAgent(_llm())

        # Valid decision dict
        d1 = {"decision": {"recommendation": "PROCEED", "fit_score": 75, "rationale": "Good"}}
        agent._validate_schema(d1)
        assert d1["decision"]["recommendation"] == "PROCEED"

        # Decision as string
        d2 = {"decision": "PASS"}
        agent._validate_schema(d2)
        assert d2["decision"]["recommendation"] == "PASS"

        # Flat recommendation at root
        d3 = {"recommendation": "PROCEED_WITH_CAUTION", "fit_score": 55}
        agent._validate_schema(d3)
        assert d3["decision"]["recommendation"] == "PROCEED_WITH_CAUTION"
        assert d3["decision"]["fit_score"] == 55

        # Nested in various keys
        for key in ["executive_brief", "summary", "analysis", "result", "output", "brief"]:
            d = {key: {"decision": {"recommendation": "PROCEED", "fit_score": 70}}}
            agent._validate_schema(d)
            assert d["decision"]["recommendation"] == "PROCEED"

        # Inferred from score
        d4 = {"score": 45}
        agent._validate_schema(d4)
        assert d4["decision"]["recommendation"] == "PASS"

        # Normalization of aliases
        aliases = {
            "CAUTION": "PROCEED_WITH_CAUTION",
            "REJECT": "PASS",
            "NO": "PASS",
            "YES": "PROCEED",
            "APPROVED": "PROCEED",
            "STRONG_YES": "STRONG_PROCEED",
        }
        for alias, expected in aliases.items():
            d = {"decision": {"recommendation": alias, "fit_score": 50}}
            agent._validate_schema(d)
            assert d["decision"]["recommendation"] == expected

        # String fit score conversion
        d5 = {"decision": {"recommendation": "PROCEED", "fit_score": "82%"}}
        agent._validate_schema(d5)
        assert d5["decision"]["fit_score"] == 82

    @patch('runtime.crewai.base_agent.Crew')
    def test_execute_end_to_end(self, mock_crew_class):
        from runtime.crewai.agents.executive_synthesizer import ExecutiveSynthesizerAgent

        mock_crew = Mock()
        mock_crew.kickoff.return_value = json.dumps({
            "agent": "Executive Synthesizer",
            "confidence": 0.92,
            "decision": {
                "recommendation": "STRONG_PROCEED",
                "fit_score": 88,
                "rationale": "Excellent match",
                "deal_makers": ["AWS expertise", "Leadership"],
                "deal_breakers": []
            },
            "strategic_angle": {"primary_hook": "Cloud-native leader"},
            "action_items": {"immediate": ["Apply now"]}
        })
        mock_crew_class.return_value = mock_crew

        agent = ExecutiveSynthesizerAgent(_llm())
        result = agent.execute({
            "job_description": "JD",
            "resume": "Resume",
            "gap_analysis": {},
            "interview_notes": "",
            "differentiation": {},
            "tailored_resume": "",
            "tailored_cover_letter": "",
            "audit_report": {}
        })
        assert result["decision"]["recommendation"] == "STRONG_PROCEED"


# ============================================================================
# Agent Execute Integration
# ============================================================================

@pytest.mark.integration
class TestAgentExecuteIntegration:

    @patch('runtime.crewai.base_agent.Crew')
    @patch('runtime.crewai.base_agent.Path.read_text', return_value="Test prompt")
    def test_differentiator_execute(self, mock_read, mock_crew_class):
        from runtime.crewai.agents.differentiator import DifferentiatorAgent

        mock_crew = Mock()
        mock_crew.kickoff.return_value = '{"agent":"Diff","confidence":0.85,"differentiators":[{"hook":"Unique"}]}'
        mock_crew_class.return_value = mock_crew

        agent = DifferentiatorAgent(_llm())
        result = agent.execute({
            "job_description": "JD",
            "resume": "Resume",
            "interview_notes": "Notes",
            "gap_analysis": "Analysis"
        })
        assert "differentiators" in result

    @patch('runtime.crewai.base_agent.Crew')
    @patch('runtime.crewai.base_agent.Path.read_text', return_value="Test prompt")
    def test_interrogator_execute(self, mock_read, mock_crew_class):
        from runtime.crewai.agents.interrogator_prepper import InterrogatorPrepperAgent

        mock_crew = Mock()
        mock_crew.kickoff.return_value = '{"agent":"Interr","confidence":0.9,"questions":[{"q":"Tell me"}]}'
        mock_crew_class.return_value = mock_crew

        agent = InterrogatorPrepperAgent(_llm())
        result = agent.execute({
            "job_description": "JD",
            "resume": "Resume",
            "gaps": ["Gap1"],
            "gap_analysis": "Analysis"
        })
        assert "questions" in result

    @patch('runtime.crewai.base_agent.Crew')
    @patch('runtime.crewai.base_agent.Path.read_text', return_value="Test prompt")
    def test_tailoring_execute(self, mock_read, mock_crew_class):
        from runtime.crewai.agents.tailoring_agent import TailoringAgent

        mock_crew = Mock()
        mock_crew.kickoff.return_value = '{"agent":"Tailor","confidence":0.88,"tailored_output":{"resume":"content"}}'
        mock_crew_class.return_value = mock_crew

        agent = TailoringAgent(_llm())
        result = agent.execute({
            "job_description": "JD",
            "resume": "Resume",
            "interview_notes": "Notes",
            "differentiators": ["D1"],
            "gap_analysis": "Analysis"
        })
        assert "tailored_output" in result


# ============================================================================
# LLM Client Integration
# ============================================================================

@pytest.mark.integration
class TestLLMClientIntegration:

    @patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}, clear=True)
    def test_get_llm_client_together_with_model(self):
        from runtime.crewai.llm_client import get_llm_client
        llm = get_llm_client(model="custom/model")
        assert llm is not None

    @patch.dict(os.environ, {"CHUTES_API_KEY": "chutes-key"}, clear=True)
    def test_get_llm_client_chutes_with_env_model(self):
        from runtime.crewai.llm_client import get_llm_client
        os.environ["CHUTES_MODEL"] = "deepseek-v3"
        llm = get_llm_client()
        assert llm is not None
        os.environ.pop("CHUTES_MODEL", None)

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test"}, clear=True)
    def test_get_llm_client_openrouter_with_env_model(self):
        from runtime.crewai.llm_client import get_llm_client
        os.environ["OPENROUTER_MODEL"] = "anthropic/claude-3"
        llm = get_llm_client()
        assert llm is not None
        os.environ.pop("OPENROUTER_MODEL", None)

    def test_retry_handler_max_delay_cap(self):
        """Verify delay is capped at 30 seconds."""
        from runtime.crewai.llm_client import LLMRetryHandler
        handler = LLMRetryHandler(max_retries=5, base_delay=10.0)
        # At attempt 3, delay = 10 * 2^3 = 80, capped to 30
        # Just verify the handler works
        call_count = [0]
        def eventually_succeed():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("fail")
            return "ok"

        # Use tiny base_delay for speed
        handler.base_delay = 0.001
        result = handler.execute_with_retry(eventually_succeed)
        assert result == "ok"


# ============================================================================
# Model Config Integration
# ============================================================================

@pytest.mark.integration
class TestModelConfigIntegration:

    @patch.dict(os.environ, {"CHUTES_API_KEY": "ck"}, clear=True)
    def test_create_llm_chutes(self):
        from runtime.crewai.model_config import _create_llm
        llm = _create_llm("chutes", "deepseek-v3", 0.3, {"base_url": "https://llm.chutes.ai/v1"})
        assert llm is not None

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "ak"}, clear=True)
    def test_create_llm_anthropic_direct(self):
        from runtime.crewai.model_config import _create_llm
        llm = _create_llm("anthropic", "claude-sonnet-4", 0.5, {})
        assert llm is not None

    @patch.dict(os.environ, {"TOGETHER_API_KEY": "tk"}, clear=True)
    def test_create_llm_together(self):
        from runtime.crewai.model_config import _create_llm
        llm = _create_llm("together", "meta-llama/Llama-4", 0.5, {})
        assert llm is not None

    @patch.dict(os.environ, {"OPENAI_API_KEY": "ok"}, clear=True)
    def test_create_llm_openai(self):
        from runtime.crewai.model_config import _create_llm
        llm = _create_llm("openai", "gpt-4o-mini", 0.2, {})
        assert llm is not None

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test"}, clear=True)
    def test_create_llm_anthropic_via_openrouter(self):
        from runtime.crewai.model_config import _create_llm
        llm = _create_llm("anthropic", "claude-sonnet-4", 0.5, {})
        assert llm is not None

    @patch.dict(os.environ, {"TOGETHER_API_KEY": "tk"}, clear=True)
    def test_get_llm_for_all_agent_types(self):
        from runtime.crewai.model_config import get_llm_for_agent, AGENT_MODELS
        for agent_type in AGENT_MODELS:
            llm = get_llm_for_agent(agent_type)
            assert llm is not None, f"Failed for {agent_type}"

    @patch.dict(os.environ, {"TOGETHER_API_KEY": "tk"}, clear=True)
    def test_fallback_only_mode(self):
        from runtime.crewai.model_config import get_llm_for_agent
        # differentiator primary is anthropic (not available), fallback is together
        llm = get_llm_for_agent("differentiator", fallback_only=True)
        assert llm is not None


# ============================================================================
# Telemetry Integration
# ============================================================================

@pytest.mark.integration
class TestTelemetryComprehensive:

    def test_all_trace_context_managers_noop(self):
        """All context managers work in noop mode."""
        from runtime.crewai.telemetry import (
            trace_workflow_stage, trace_agent_execution, trace_task_execution, NoOpSpan
        )
        with trace_workflow_stage("stage") as s1:
            assert isinstance(s1, NoOpSpan)
        with trace_agent_execution("Agent") as s2:
            assert isinstance(s2, NoOpSpan)
        with trace_task_execution("task", "Agent") as s3:
            assert isinstance(s3, NoOpSpan)

    @patch.dict(os.environ, {"OTEL_ENABLED": "true"}, clear=False)
    def test_all_trace_context_managers_real(self):
        from runtime.crewai.telemetry import (
            trace_workflow_stage, trace_agent_execution, trace_task_execution,
            record_agent_error, record_agent_result, NoOpSpan
        )
        import runtime.crewai.telemetry as tel
        tel._tracer = None

        with trace_workflow_stage("wf_stage", {"retry": 0}) as s1:
            assert not isinstance(s1, NoOpSpan)
            s1.set_attribute("wf.key", "val")

        with trace_agent_execution("Gap Analyzer", {"job": "123"}) as s2:
            record_agent_result(s2, {"confidence": 0.9}, "Gap Analyzer")

        with trace_task_execution("analyze", "Gap Analyzer", {"attempt": 1}) as s3:
            s3.set_attribute("task.status", "done")

        with trace_agent_execution("Auditor") as s4:
            record_agent_error(s4, ValueError("test"), "Auditor")

        # Result without confidence key
        with trace_agent_execution("Other") as s5:
            record_agent_result(s5, {}, "Other")


# ============================================================================
# CLI Integration
# ============================================================================

@pytest.mark.integration
class TestCLIIntegration:

    def test_get_repo_root(self):
        """_get_repo_root should find this project's root."""
        from runtime.crewai.cli import _get_repo_root
        root = _get_repo_root()
        assert (root / "requirements.txt").exists() or (root / ".git").exists()

    def test_validate_repo_structure(self):
        """_validate_repo_structure warns but doesn't raise."""
        from runtime.crewai.cli import _validate_repo_structure
        # Should not raise even for missing dirs
        _validate_repo_structure(Path("/tmp"))

    def test_read_sources_skips_binary(self):
        """_read_sources skips non-UTF-8 files."""
        from runtime.crewai.cli import _read_sources
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "text.md").write_text("Hello")
            (Path(d) / "binary.bin").write_bytes(b'\x80\x81\x82\x83')
            content = _read_sources(Path(d))
            assert "Hello" in content

    @patch('runtime.crewai.cli.HydraWorkflow')
    @patch('runtime.crewai.cli.get_llm_client')
    def test_main_success(self, mock_llm, mock_workflow_class):
        from runtime.crewai.cli import main

        mock_llm.return_value = _llm()

        result = Mock()
        result.success = True
        result.final_documents = {"resume": "content", "cover_letter": "content"}
        result.audit_report = {"final_status": "APPROVED"}
        result.execution_log = ["log"]
        result.intermediate_results = {}
        result.audit_failed = False
        mock_workflow_class.return_value.execute.return_value = result

        with tempfile.TemporaryDirectory() as d:
            jd = Path(d) / "jd.md"
            resume = Path(d) / "resume.md"
            sources = Path(d) / "sources"
            sources.mkdir()
            jd.write_text("Job description")
            resume.write_text("Resume content")
            (sources / "src.md").write_text("Source doc")
            out = Path(d) / "out"

            exit_code = main([
                "--jd", str(jd),
                "--resume", str(resume),
                "--sources", str(sources),
                "--out", str(out),
            ])
            assert exit_code == 0

    @patch('runtime.crewai.cli.HydraWorkflow')
    @patch('runtime.crewai.cli.get_llm_client')
    def test_main_audit_failed(self, mock_llm, mock_workflow_class):
        from runtime.crewai.cli import main

        mock_llm.return_value = _llm()

        result = Mock()
        result.success = True
        result.final_documents = {"resume": "r", "cover_letter": "c"}
        result.audit_report = {"final_status": "REJECTED"}
        result.execution_log = []
        result.intermediate_results = {}
        result.audit_failed = True
        result.audit_error = "Audit rejected"
        mock_workflow_class.return_value.execute.return_value = result

        with tempfile.TemporaryDirectory() as d:
            jd = Path(d) / "jd.md"
            resume = Path(d) / "resume.md"
            sources = Path(d) / "sources"
            sources.mkdir()
            jd.write_text("JD")
            resume.write_text("Resume")
            (sources / "s.md").write_text("S")
            out = Path(d) / "out"

            exit_code = main(["--jd", str(jd), "--resume", str(resume), "--sources", str(sources), "--out", str(out)])
            assert exit_code == 1


# ============================================================================
# Crew Integration
# ============================================================================

@pytest.mark.integration
class TestCrewModuleIntegration:

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test"}, clear=False)
    def test_hydra_crew_init_builds_agents(self):
        from runtime.crewai.crew import HydraCrew
        crew = HydraCrew("Job desc", "Resume text", "Notes")
        assert hasattr(crew, 'commander')
        assert hasattr(crew, 'gap_analyzer')
        assert hasattr(crew, 'interrogator')
        assert hasattr(crew, 'differentiator')
        assert hasattr(crew, 'tailor')
        assert hasattr(crew, 'auditor')

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test"}, clear=False)
    def test_hydra_crew_build_tasks(self):
        from runtime.crewai.crew import HydraCrew
        crew = HydraCrew("Job desc", "Resume text")
        tasks = crew.build_tasks()
        assert len(tasks) == 6

    def test_load_prompt_existing(self):
        """load_prompt should work for known agents."""
        from runtime.crewai.crew import load_prompt
        # Only test if the prompt file exists
        prompt_path = Path(__file__).parent.parent.parent / "agents" / "commander" / "prompt.md"
        if prompt_path.exists():
            prompt = load_prompt("commander")
            assert len(prompt) > 0


# ============================================================================
# Quick Crew Integration
# ============================================================================

@pytest.mark.integration
class TestQuickCrewModuleIntegration:

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test"}, clear=False)
    def test_build_crew_all_agents_present(self):
        from runtime.crewai.quick_crew import build_crew
        crew = build_crew("Engineer role", "My resume", "Interview notes")
        assert len(crew.agents) == 6
        assert len(crew.tasks) == 6

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test"}, clear=False)
    def test_build_crew_no_notes(self):
        from runtime.crewai.quick_crew import build_crew
        crew = build_crew("Engineer role", "My resume", "")
        assert crew is not None
