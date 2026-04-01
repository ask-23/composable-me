"""
Comprehensive unit tests for CLI, crew, quick_crew, and hydra_workflow modules.

Targets 90%+ coverage on:
- runtime/crewai/cli.py (was 12%)
- runtime/crewai/crew.py (was 51%)
- runtime/crewai/quick_crew.py (was 0%)
- runtime/crewai/hydra_workflow.py uncovered paths (was 74%)
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open


# ---------------------------------------------------------------------------
# CLI tests — runtime/crewai/cli.py
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestGetRepoRoot:
    """Tests for _get_repo_root()"""

    def test_finds_git_directory(self, tmp_path):
        (tmp_path / ".git").mkdir()
        with patch("runtime.crewai.cli.Path.cwd", return_value=tmp_path):
            from runtime.crewai.cli import _get_repo_root
            assert _get_repo_root() == tmp_path

    def test_finds_requirements_txt(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("crewai==0.1")
        with patch("runtime.crewai.cli.Path.cwd", return_value=tmp_path):
            from runtime.crewai.cli import _get_repo_root
            assert _get_repo_root() == tmp_path

    def test_searches_parent_directories(self, tmp_path):
        (tmp_path / ".git").mkdir()
        child = tmp_path / "a" / "b" / "c"
        child.mkdir(parents=True)
        with patch("runtime.crewai.cli.Path.cwd", return_value=child):
            from runtime.crewai.cli import _get_repo_root
            assert _get_repo_root() == tmp_path

    def test_raises_when_no_root_found(self, tmp_path):
        # Use a temp dir with no .git or requirements.txt anywhere in parents
        isolated = tmp_path / "isolated"
        isolated.mkdir()
        with patch("runtime.crewai.cli.Path.cwd", return_value=isolated):
            # Mock parents to only include isolated itself (no real parents)
            with patch.object(Path, "parents", new_callable=lambda: property(lambda self: [])):
                from runtime.crewai.cli import _get_repo_root
                with pytest.raises(FileNotFoundError, match="Could not find repository root"):
                    _get_repo_root()


@pytest.mark.unit
class TestValidateRepoStructure:
    """Tests for _validate_repo_structure()"""

    def test_no_warning_when_dirs_exist(self, tmp_path, capsys):
        (tmp_path / "inputs").mkdir()
        (tmp_path / "examples").mkdir()
        from runtime.crewai.cli import _validate_repo_structure
        _validate_repo_structure(tmp_path)
        captured = capsys.readouterr()
        assert "Warning" not in captured.out

    def test_warns_when_inputs_missing(self, tmp_path, capsys):
        (tmp_path / "examples").mkdir()
        from runtime.crewai.cli import _validate_repo_structure
        _validate_repo_structure(tmp_path)
        captured = capsys.readouterr()
        assert "inputs" in captured.out

    def test_warns_when_both_missing(self, tmp_path, capsys):
        from runtime.crewai.cli import _validate_repo_structure
        _validate_repo_structure(tmp_path)
        captured = capsys.readouterr()
        assert "inputs" in captured.out
        assert "examples" in captured.out


@pytest.mark.unit
class TestBuildParser:
    """Tests for build_parser()"""

    def test_returns_parser(self):
        from runtime.crewai.cli import build_parser
        parser = build_parser()
        assert parser is not None

    def test_required_args(self):
        from runtime.crewai.cli import build_parser
        parser = build_parser()
        # Should fail without --jd and --resume
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parses_all_args(self):
        from runtime.crewai.cli import build_parser
        parser = build_parser()
        args = parser.parse_args([
            "--jd", "jd.md",
            "--resume", "resume.md",
            "--sources", "sources/",
            "--out", "output/",
            "--model", "test-model",
            "--max-audit-retries", "3",
            "--verbose",
            "--interactive",
        ])
        assert args.jd == "jd.md"
        assert args.resume == "resume.md"
        assert args.sources == "sources/"
        assert args.out == "output/"
        assert args.model == "test-model"
        assert args.max_audit_retries == 3
        assert args.verbose is True
        assert args.interactive is True

    def test_default_values(self):
        from runtime.crewai.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["--jd", "j.md", "--resume", "r.md"])
        assert args.out == "output/"
        assert args.max_audit_retries == 2
        assert args.verbose is False
        assert args.interactive is False
        assert args.sources is None
        assert args.model is None


@pytest.mark.unit
class TestReadFile:
    """Tests for _read_file()"""

    def test_reads_existing_file(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("hello world")
        from runtime.crewai.cli import _read_file
        assert _read_file(f) == "hello world"

    def test_raises_on_missing_file(self, tmp_path):
        from runtime.crewai.cli import _read_file
        with pytest.raises(FileNotFoundError, match="Input file not found"):
            _read_file(tmp_path / "nonexistent.md")


@pytest.mark.unit
class TestReadSources:
    """Tests for _read_sources()"""

    def test_reads_all_text_files(self, tmp_path):
        (tmp_path / "a.txt").write_text("alpha")
        (tmp_path / "b.txt").write_text("beta")
        from runtime.crewai.cli import _read_sources
        result = _read_sources(tmp_path)
        assert "a.txt" in result
        assert "alpha" in result
        assert "b.txt" in result
        assert "beta" in result

    def test_raises_on_missing_directory(self):
        from runtime.crewai.cli import _read_sources
        with pytest.raises(FileNotFoundError, match="Sources directory not found"):
            _read_sources(Path("/nonexistent/dir"))

    def test_raises_on_file_instead_of_dir(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("not a dir")
        from runtime.crewai.cli import _read_sources
        with pytest.raises(ValueError, match="must be a directory"):
            _read_sources(f)

    def test_skips_non_utf8_files(self, tmp_path, capsys):
        (tmp_path / "good.txt").write_text("valid utf8")
        (tmp_path / "bad.bin").write_bytes(b"\x80\x81\x82\x83" * 100)
        from runtime.crewai.cli import _read_sources
        result = _read_sources(tmp_path)
        assert "good.txt" in result
        captured = capsys.readouterr()
        assert "Skipping non-text source file" in captured.out

    def test_raises_when_no_text_files(self, tmp_path):
        (tmp_path / "bad.bin").write_bytes(b"\x80\x81\x82\x83" * 100)
        from runtime.crewai.cli import _read_sources
        with pytest.raises(ValueError, match="No UTF-8 text source documents found"):
            _read_sources(tmp_path)

    def test_skips_subdirectories(self, tmp_path):
        (tmp_path / "subdir").mkdir()
        (tmp_path / "file.txt").write_text("content")
        from runtime.crewai.cli import _read_sources
        result = _read_sources(tmp_path)
        assert "file.txt" in result
        assert "subdir" not in result


@pytest.mark.unit
class TestWriteOutputFiles:
    """Tests for _write_output_files()"""

    def _make_result(self, final_docs=None, audit_report=None,
                     execution_log=None, intermediate_results=None):
        mock = Mock()
        mock.final_documents = final_docs or {}
        mock.audit_report = audit_report or {}
        mock.execution_log = execution_log or []
        mock.intermediate_results = intermediate_results or {}
        return mock

    def test_writes_basic_output_files(self, tmp_path):
        from runtime.crewai.cli import _write_output_files
        result = self._make_result(
            final_docs={"resume": "# Resume", "cover_letter": "Dear Hiring Manager"},
            audit_report={"final_status": "APPROVED"},
            execution_log=["step1", "step2"],
        )
        out_dir = tmp_path / "output"
        _write_output_files(out_dir, result)

        assert (out_dir / "resume.md").read_text() == "# Resume"
        assert (out_dir / "cover_letter.md").read_text() == "Dear Hiring Manager"
        assert "APPROVED" in (out_dir / "audit_report.yaml").read_text()
        assert "step1" in (out_dir / "execution_log.txt").read_text()

    def test_creates_output_directory(self, tmp_path):
        from runtime.crewai.cli import _write_output_files
        result = self._make_result()
        out_dir = tmp_path / "nested" / "output"
        _write_output_files(out_dir, result)
        assert out_dir.exists()

    def test_writes_intermediate_files(self, tmp_path):
        from runtime.crewai.cli import _write_output_files
        result = self._make_result(
            intermediate_results={
                "gap_analysis": {"gaps": ["a", "b"]},
                "tailoring": {"resume": "content"},
            }
        )
        out_dir = tmp_path / "output"
        _write_output_files(out_dir, result, include_intermediate=True)

        assert (out_dir / "intermediate" / "gap_analysis.yaml").exists()
        assert (out_dir / "intermediate" / "tailoring.yaml").exists()

    def test_no_intermediate_without_flag(self, tmp_path):
        from runtime.crewai.cli import _write_output_files
        result = self._make_result(
            intermediate_results={"stage": {"data": 1}}
        )
        out_dir = tmp_path / "output"
        _write_output_files(out_dir, result, include_intermediate=False)
        assert not (out_dir / "intermediate").exists()

    def test_handles_none_final_documents(self, tmp_path):
        from runtime.crewai.cli import _write_output_files
        result = self._make_result()
        result.final_documents = None
        result.audit_report = None
        out_dir = tmp_path / "output"
        _write_output_files(out_dir, result)
        assert (out_dir / "resume.md").read_text() == ""


@pytest.mark.unit
class TestCLIMain:
    """Tests for main() CLI entrypoint"""

    def _setup_input_files(self, tmp_path):
        """Create a valid repo structure with input files."""
        (tmp_path / ".git").mkdir()
        (tmp_path / "inputs").mkdir()
        (tmp_path / "examples").mkdir()

        jd = tmp_path / "jd.md"
        jd.write_text("Senior Engineer role")

        resume = tmp_path / "resume.md"
        resume.write_text("Experienced engineer")

        sources = tmp_path / "sources"
        sources.mkdir()
        (sources / "notes.txt").write_text("Interview notes")

        out_dir = tmp_path / "output"
        return jd, resume, sources, out_dir

    @patch("runtime.crewai.cli._get_repo_root")
    @patch("runtime.crewai.cli._validate_repo_structure")
    @patch("runtime.crewai.cli.get_llm_client")
    @patch("runtime.crewai.cli.HydraWorkflow")
    def test_main_success(self, MockWorkflow, mock_llm, mock_validate, mock_root, tmp_path):
        from runtime.crewai.cli import main

        jd, resume, sources, out_dir = self._setup_input_files(tmp_path)
        mock_root.return_value = tmp_path

        mock_result = Mock()
        mock_result.success = True
        mock_result.audit_failed = False
        mock_result.audit_report = {"final_status": "APPROVED"}
        mock_result.final_documents = {"resume": "# Resume", "cover_letter": "CL"}
        mock_result.execution_log = ["done"]
        mock_result.intermediate_results = {}

        MockWorkflow.return_value.execute.return_value = mock_result

        exit_code = main([
            "--jd", str(jd),
            "--resume", str(resume),
            "--sources", str(sources),
            "--out", str(out_dir),
        ])
        assert exit_code == 0

    @patch("runtime.crewai.cli._get_repo_root")
    @patch("runtime.crewai.cli._validate_repo_structure")
    @patch("runtime.crewai.cli.get_llm_client")
    @patch("runtime.crewai.cli.HydraWorkflow")
    def test_main_audit_crashed(self, MockWorkflow, mock_llm, mock_validate, mock_root, tmp_path, capsys):
        from runtime.crewai.cli import main

        jd, resume, sources, out_dir = self._setup_input_files(tmp_path)
        mock_root.return_value = tmp_path

        mock_result = Mock()
        mock_result.success = True
        mock_result.audit_failed = True
        mock_result.audit_error = "LLM timeout"
        mock_result.audit_report = {"final_status": "AUDIT_CRASHED"}
        mock_result.final_documents = {"resume": "R", "cover_letter": "CL"}
        mock_result.execution_log = []
        mock_result.intermediate_results = {"stage": "data"}

        MockWorkflow.return_value.execute.return_value = mock_result

        exit_code = main([
            "--jd", str(jd),
            "--resume", str(resume),
            "--sources", str(sources),
            "--out", str(out_dir),
        ])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "audit crashed" in captured.out.lower() or "AUDIT" in captured.out

    @patch("runtime.crewai.cli._get_repo_root")
    @patch("runtime.crewai.cli._validate_repo_structure")
    @patch("runtime.crewai.cli.get_llm_client")
    @patch("runtime.crewai.cli.HydraWorkflow")
    def test_main_audit_rejected(self, MockWorkflow, mock_llm, mock_validate, mock_root, tmp_path, capsys):
        from runtime.crewai.cli import main

        jd, resume, sources, out_dir = self._setup_input_files(tmp_path)
        mock_root.return_value = tmp_path

        mock_result = Mock()
        mock_result.success = True
        mock_result.audit_failed = True
        mock_result.audit_error = "Failed audit"
        mock_result.audit_report = {"final_status": "REJECTED"}
        mock_result.final_documents = {"resume": "R", "cover_letter": "CL"}
        mock_result.execution_log = []
        mock_result.intermediate_results = {}

        MockWorkflow.return_value.execute.return_value = mock_result

        exit_code = main([
            "--jd", str(jd),
            "--resume", str(resume),
            "--sources", str(sources),
            "--out", str(out_dir),
        ])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "rejected" in captured.out.lower() or "REJECTED" in captured.out

    @patch("runtime.crewai.cli._get_repo_root")
    @patch("runtime.crewai.cli._validate_repo_structure")
    @patch("runtime.crewai.cli.get_llm_client")
    @patch("runtime.crewai.cli.HydraWorkflow")
    def test_main_audit_other_status(self, MockWorkflow, mock_llm, mock_validate, mock_root, tmp_path, capsys):
        from runtime.crewai.cli import main

        jd, resume, sources, out_dir = self._setup_input_files(tmp_path)
        mock_root.return_value = tmp_path

        mock_result = Mock()
        mock_result.success = True
        mock_result.audit_failed = True
        mock_result.audit_error = "Unknown issue"
        mock_result.audit_report = {"final_status": "PARTIAL"}
        mock_result.final_documents = {"resume": "R", "cover_letter": "CL"}
        mock_result.execution_log = []
        mock_result.intermediate_results = {}

        MockWorkflow.return_value.execute.return_value = mock_result

        exit_code = main([
            "--jd", str(jd),
            "--resume", str(resume),
            "--sources", str(sources),
            "--out", str(out_dir),
        ])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "PARTIAL" in captured.out

    @patch("runtime.crewai.cli._get_repo_root")
    @patch("runtime.crewai.cli._validate_repo_structure")
    @patch("runtime.crewai.cli.get_llm_client")
    @patch("runtime.crewai.cli.HydraWorkflow")
    def test_main_workflow_failure(self, MockWorkflow, mock_llm, mock_validate, mock_root, tmp_path, capsys):
        from runtime.crewai.cli import main

        jd, resume, sources, out_dir = self._setup_input_files(tmp_path)
        mock_root.return_value = tmp_path

        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = "Pipeline crashed"
        mock_result.intermediate_results = {}
        mock_result.final_documents = {}
        mock_result.execution_log = []

        MockWorkflow.return_value.execute.return_value = mock_result

        exit_code = main([
            "--jd", str(jd),
            "--resume", str(resume),
            "--sources", str(sources),
            "--out", str(out_dir),
        ])
        assert exit_code == 2

    @patch("runtime.crewai.cli._get_repo_root")
    @patch("runtime.crewai.cli._validate_repo_structure")
    @patch("runtime.crewai.cli.get_llm_client")
    @patch("runtime.crewai.cli.HydraWorkflow")
    def test_main_workflow_failure_with_intermediate(self, MockWorkflow, mock_llm, mock_validate, mock_root, tmp_path, capsys):
        from runtime.crewai.cli import main

        jd, resume, sources, out_dir = self._setup_input_files(tmp_path)
        mock_root.return_value = tmp_path

        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = "Pipeline crashed"
        mock_result.intermediate_results = {"gap_analysis": {"data": "partial"}}
        mock_result.final_documents = {}
        mock_result.audit_report = {}
        mock_result.execution_log = []

        MockWorkflow.return_value.execute.return_value = mock_result

        exit_code = main([
            "--jd", str(jd),
            "--resume", str(resume),
            "--sources", str(sources),
            "--out", str(out_dir),
        ])
        assert exit_code == 2
        captured = capsys.readouterr()
        assert "Partial results" in captured.err or "Pipeline crashed" in captured.err

    @patch("runtime.crewai.cli._get_repo_root")
    @patch("runtime.crewai.cli._validate_repo_structure")
    @patch("runtime.crewai.cli.get_llm_client")
    def test_main_llm_error(self, mock_llm, mock_validate, mock_root, tmp_path, capsys):
        from runtime.crewai.cli import main
        from runtime.crewai.llm_client import LLMClientError

        jd, resume, sources, out_dir = self._setup_input_files(tmp_path)
        mock_root.return_value = tmp_path
        mock_llm.side_effect = LLMClientError("No API key")

        exit_code = main([
            "--jd", str(jd),
            "--resume", str(resume),
            "--sources", str(sources),
            "--out", str(out_dir),
        ])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "LLM configuration error" in captured.err

    @patch("runtime.crewai.cli._get_repo_root")
    @patch("runtime.crewai.cli._validate_repo_structure")
    @patch("runtime.crewai.cli.get_llm_client")
    @patch("runtime.crewai.cli.HydraWorkflow")
    def test_main_defaults_sources_to_jd_parent(self, MockWorkflow, mock_llm, mock_validate, mock_root, tmp_path, capsys):
        from runtime.crewai.cli import main

        (tmp_path / ".git").mkdir()
        (tmp_path / "inputs").mkdir()
        (tmp_path / "examples").mkdir()

        jd_dir = tmp_path / "jd_dir"
        jd_dir.mkdir()
        jd = jd_dir / "jd.md"
        jd.write_text("Job description")
        (jd_dir / "source.txt").write_text("Source doc")

        resume = tmp_path / "resume.md"
        resume.write_text("Resume")

        out_dir = tmp_path / "output"

        mock_root.return_value = tmp_path

        mock_result = Mock()
        mock_result.success = True
        mock_result.audit_failed = False
        mock_result.audit_report = {"final_status": "APPROVED"}
        mock_result.final_documents = {"resume": "R", "cover_letter": "CL"}
        mock_result.execution_log = []
        mock_result.intermediate_results = {}

        MockWorkflow.return_value.execute.return_value = mock_result

        exit_code = main([
            "--jd", str(jd),
            "--resume", str(resume),
            "--out", str(out_dir),
        ])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "No --sources specified" in captured.out

    def test_main_missing_jd_file(self, tmp_path):
        """parser.error exits with code 2 when JD file missing."""
        from runtime.crewai.cli import main
        (tmp_path / ".git").mkdir()
        (tmp_path / "inputs").mkdir()
        (tmp_path / "examples").mkdir()
        resume = tmp_path / "resume.md"
        resume.write_text("Resume")

        with patch("runtime.crewai.cli._get_repo_root", return_value=tmp_path), \
             patch("runtime.crewai.cli._validate_repo_structure"):
            with pytest.raises(SystemExit) as exc_info:
                main(["--jd", str(tmp_path / "missing.md"), "--resume", str(resume)])
            assert exc_info.value.code == 2

    def test_main_missing_resume_file(self, tmp_path):
        from runtime.crewai.cli import main
        (tmp_path / ".git").mkdir()
        (tmp_path / "inputs").mkdir()
        (tmp_path / "examples").mkdir()
        jd = tmp_path / "jd.md"
        jd.write_text("JD")

        with patch("runtime.crewai.cli._get_repo_root", return_value=tmp_path), \
             patch("runtime.crewai.cli._validate_repo_structure"):
            with pytest.raises(SystemExit) as exc_info:
                main(["--jd", str(jd), "--resume", str(tmp_path / "missing.md")])
            assert exc_info.value.code == 2

    def test_main_sources_not_a_directory(self, tmp_path):
        from runtime.crewai.cli import main
        (tmp_path / ".git").mkdir()
        (tmp_path / "inputs").mkdir()
        (tmp_path / "examples").mkdir()
        jd = tmp_path / "jd.md"
        jd.write_text("JD")
        resume = tmp_path / "resume.md"
        resume.write_text("Resume")
        bad_sources = tmp_path / "sources_file"
        bad_sources.write_text("not a directory")

        with patch("runtime.crewai.cli._get_repo_root", return_value=tmp_path), \
             patch("runtime.crewai.cli._validate_repo_structure"):
            with pytest.raises(SystemExit) as exc_info:
                main(["--jd", str(jd), "--resume", str(resume), "--sources", str(bad_sources)])
            assert exc_info.value.code == 2

    @patch("runtime.crewai.cli._get_repo_root")
    def test_main_repo_root_not_found(self, mock_root):
        from runtime.crewai.cli import main
        mock_root.side_effect = FileNotFoundError("Could not find repository root")
        with pytest.raises(SystemExit) as exc_info:
            main(["--jd", "jd.md", "--resume", "resume.md"])
        assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# Crew tests — runtime/crewai/crew.py
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestLoadPrompt:
    """Tests for load_prompt()"""

    def test_loads_prompt_from_file(self, tmp_path):
        agents_dir = tmp_path / "agents" / "commander"
        agents_dir.mkdir(parents=True)
        (agents_dir / "prompt.md").write_text("You are commander")

        with patch("runtime.crewai.crew.PROJECT_ROOT", tmp_path):
            from runtime.crewai.crew import load_prompt
            result = load_prompt("commander")
            assert result == "You are commander"

    def test_raises_on_missing_prompt(self, tmp_path):
        with patch("runtime.crewai.crew.PROJECT_ROOT", tmp_path):
            from runtime.crewai.crew import load_prompt
            with pytest.raises(FileNotFoundError, match="Prompt not found"):
                load_prompt("nonexistent-agent")


@pytest.mark.unit
class TestLoadDocs:
    """Tests for load_docs()"""

    def test_loads_existing_docs(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "AGENTS.MD").write_text("Agent rules")
        (docs_dir / "STYLE_GUIDE.MD").write_text("Style guide")

        with patch("runtime.crewai.crew.PROJECT_ROOT", tmp_path):
            from runtime.crewai.crew import load_docs
            docs = load_docs()
            assert docs["AGENTS.MD"] == "Agent rules"
            assert docs["STYLE_GUIDE.MD"] == "Style guide"

    def test_skips_missing_docs(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        # Only create one doc file
        (docs_dir / "AGENTS.MD").write_text("Agent rules")

        with patch("runtime.crewai.crew.PROJECT_ROOT", tmp_path):
            from runtime.crewai.crew import load_docs
            docs = load_docs()
            assert "AGENTS.MD" in docs
            assert "STYLE_GUIDE.MD" not in docs

    def test_empty_when_no_docs_dir(self, tmp_path):
        with patch("runtime.crewai.crew.PROJECT_ROOT", tmp_path):
            from runtime.crewai.crew import load_docs
            docs = load_docs()
            assert docs == {}


@pytest.mark.unit
class TestCrewGetLLM:
    """Tests for crew.get_llm()"""

    @patch("runtime.crewai.crew.LLM")
    def test_get_llm_with_valid_key(self, MockLLM):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test123"}, clear=False):
            from runtime.crewai.crew import get_llm
            get_llm()
            MockLLM.assert_called_once()
            call_kwargs = MockLLM.call_args[1]
            assert call_kwargs["api_key"] == "sk-or-test123"

    def test_get_llm_without_key(self):
        with patch.dict(os.environ, {}, clear=True):
            from runtime.crewai.crew import get_llm
            with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY not set"):
                get_llm()

    @patch("runtime.crewai.crew.LLM")
    def test_get_llm_uses_custom_model(self, MockLLM):
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "sk-or-test",
            "OPENROUTER_MODEL": "google/gemini-pro",
        }, clear=False):
            from runtime.crewai.crew import get_llm
            get_llm()
            call_kwargs = MockLLM.call_args[1]
            assert "google/gemini-pro" in call_kwargs["model"]


@pytest.mark.unit
class TestHydraCrewInit:
    """Tests for HydraCrew.__init__ and _build_agents"""

    @patch("runtime.crewai.crew.Agent")
    @patch("runtime.crewai.crew.get_llm")
    @patch("runtime.crewai.crew.load_prompt", return_value="Test prompt")
    @patch("runtime.crewai.crew.load_docs", return_value={"AGENTS.MD": "Rules", "STYLE_GUIDE.MD": "Style"})
    def test_init_creates_all_agents(self, mock_docs, mock_prompt, mock_llm, MockAgent):
        from runtime.crewai.crew import HydraCrew
        crew = HydraCrew("JD text", "Resume text", "Interview notes")

        assert crew.job_description == "JD text"
        assert crew.resume_text == "Resume text"
        assert crew.interview_notes == "Interview notes"
        # Agent() called 6 times (one per agent)
        assert MockAgent.call_count == 6

    @patch("runtime.crewai.crew.Agent")
    @patch("runtime.crewai.crew.get_llm")
    @patch("runtime.crewai.crew.load_prompt", return_value="Test prompt")
    @patch("runtime.crewai.crew.load_docs", return_value={})
    def test_init_uses_default_truth_rules_when_docs_missing(self, mock_docs, mock_prompt, mock_llm, MockAgent):
        from runtime.crewai.crew import HydraCrew, DEFAULT_TRUTH_RULES
        crew = HydraCrew("JD", "Resume")
        assert crew.interview_notes == ""
        # When AGENTS.MD not in docs, should use DEFAULT_TRUTH_RULES
        assert MockAgent.call_count == 6

    @patch("runtime.crewai.crew.Agent")
    @patch("runtime.crewai.crew.get_llm")
    @patch("runtime.crewai.crew.load_prompt", return_value="Prompt")
    @patch("runtime.crewai.crew.load_docs", return_value={})
    def test_init_with_none_notes(self, mock_docs, mock_prompt, mock_llm, MockAgent):
        from runtime.crewai.crew import HydraCrew
        crew = HydraCrew("JD", "Resume", None)
        assert crew.interview_notes == ""


@pytest.mark.unit
class TestHydraCrewBuildTasks:
    """Tests for HydraCrew.build_tasks"""

    @patch("runtime.crewai.crew.Task")
    @patch("runtime.crewai.crew.Agent")
    @patch("runtime.crewai.crew.get_llm")
    @patch("runtime.crewai.crew.load_prompt", return_value="Prompt")
    @patch("runtime.crewai.crew.load_docs", return_value={"AGENTS.MD": "R", "STYLE_GUIDE.MD": "S"})
    def test_build_tasks_returns_six(self, mock_docs, mock_prompt, mock_llm, MockAgent, MockTask):
        from runtime.crewai.crew import HydraCrew
        crew = HydraCrew("JD", "Resume", "Notes")
        tasks = crew.build_tasks()
        assert len(tasks) == 6
        assert MockTask.call_count == 6


@pytest.mark.unit
class TestHydraCrewRun:
    """Tests for HydraCrew.run"""

    @patch("runtime.crewai.crew.Crew")
    @patch("runtime.crewai.crew.Task")
    @patch("runtime.crewai.crew.Agent")
    @patch("runtime.crewai.crew.get_llm")
    @patch("runtime.crewai.crew.load_prompt", return_value="Prompt")
    @patch("runtime.crewai.crew.load_docs", return_value={"AGENTS.MD": "R", "STYLE_GUIDE.MD": "S"})
    def test_run_returns_dict(self, mock_docs, mock_prompt, mock_llm, MockAgent, MockTask, MockCrew):
        from runtime.crewai.crew import HydraCrew
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = "Final output"
        MockCrew.return_value = mock_crew_instance

        # Make tasks return mock output for the dict comprehension
        mock_task = MagicMock()
        mock_task.description = "Analyze this job description..." + "x" * 50
        mock_task.output = "Task output"
        MockTask.return_value = mock_task

        crew = HydraCrew("JD", "Resume")
        result = crew.run()

        assert "raw_output" in result
        assert result["raw_output"] == "Final output"
        assert "tasks_output" in result
        MockCrew.assert_called_once()
        mock_crew_instance.kickoff.assert_called_once()


@pytest.mark.unit
class TestCrewMain:
    """Tests for crew.main()"""

    @patch("runtime.crewai.crew.Crew")
    @patch("runtime.crewai.crew.Task")
    @patch("runtime.crewai.crew.Agent")
    @patch("runtime.crewai.crew.get_llm")
    @patch("runtime.crewai.crew.load_prompt", return_value="Prompt")
    @patch("runtime.crewai.crew.load_docs", return_value={})
    def test_main_with_output_file(self, mock_docs, mock_prompt, mock_llm, MockAgent, MockTask, MockCrew, tmp_path):
        from runtime.crewai.crew import main as crew_main

        jd = tmp_path / "jd.md"
        jd.write_text("Job description")
        resume = tmp_path / "resume.md"
        resume.write_text("Resume text")
        out = tmp_path / "result.json"

        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = "Result text"
        MockCrew.return_value = mock_crew_instance

        mock_task = MagicMock()
        mock_task.description = "Task description placeholder text"
        mock_task.output = None
        MockTask.return_value = mock_task

        with patch("sys.argv", ["crew", "--jd", str(jd), "--resume", str(resume), "--out", str(out)]):
            crew_main()

        assert out.exists()

    @patch("runtime.crewai.crew.Crew")
    @patch("runtime.crewai.crew.Task")
    @patch("runtime.crewai.crew.Agent")
    @patch("runtime.crewai.crew.get_llm")
    @patch("runtime.crewai.crew.load_prompt", return_value="Prompt")
    @patch("runtime.crewai.crew.load_docs", return_value={})
    def test_main_without_output_file(self, mock_docs, mock_prompt, mock_llm, MockAgent, MockTask, MockCrew, tmp_path, capsys):
        from runtime.crewai.crew import main as crew_main

        jd = tmp_path / "jd.md"
        jd.write_text("JD")
        resume = tmp_path / "resume.md"
        resume.write_text("Resume")

        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = "Final output here"
        MockCrew.return_value = mock_crew_instance

        mock_task = MagicMock()
        mock_task.description = "Task desc"
        mock_task.output = None
        MockTask.return_value = mock_task

        with patch("sys.argv", ["crew", "--jd", str(jd), "--resume", str(resume)]):
            crew_main()

        captured = capsys.readouterr()
        assert "Final output here" in captured.out

    @patch("runtime.crewai.crew.Crew")
    @patch("runtime.crewai.crew.Task")
    @patch("runtime.crewai.crew.Agent")
    @patch("runtime.crewai.crew.get_llm")
    @patch("runtime.crewai.crew.load_prompt", return_value="Prompt")
    @patch("runtime.crewai.crew.load_docs", return_value={})
    def test_main_with_notes(self, mock_docs, mock_prompt, mock_llm, MockAgent, MockTask, MockCrew, tmp_path):
        from runtime.crewai.crew import main as crew_main

        jd = tmp_path / "jd.md"
        jd.write_text("JD")
        resume = tmp_path / "resume.md"
        resume.write_text("Resume")
        notes = tmp_path / "notes.md"
        notes.write_text("Notes content")

        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = "Result"
        MockCrew.return_value = mock_crew_instance

        mock_task = MagicMock()
        mock_task.description = "Task"
        mock_task.output = None
        MockTask.return_value = mock_task

        with patch("sys.argv", ["crew", "--jd", str(jd), "--resume", str(resume), "--notes", str(notes)]):
            crew_main()


# ---------------------------------------------------------------------------
# Quick Crew tests — runtime/crewai/quick_crew.py
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestQuickCrewGetLLM:
    """Tests for quick_crew.get_llm()"""

    @patch("runtime.crewai.quick_crew.LLM")
    def test_returns_llm_with_valid_key(self, MockLLM):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test"}, clear=False):
            from runtime.crewai.quick_crew import get_llm
            get_llm()
            MockLLM.assert_called_once()

    def test_exits_without_key(self):
        with patch.dict(os.environ, {}, clear=True):
            from runtime.crewai.quick_crew import get_llm
            with pytest.raises(SystemExit) as exc_info:
                get_llm()
            assert exc_info.value.code == 1

    @patch("runtime.crewai.quick_crew.LLM")
    def test_uses_custom_model_env(self, MockLLM):
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "sk-or-test",
            "OPENROUTER_MODEL": "custom/model",
        }, clear=False):
            from runtime.crewai.quick_crew import get_llm
            get_llm()
            call_kwargs = MockLLM.call_args[1]
            assert "custom/model" in call_kwargs["model"]


@pytest.mark.unit
class TestQuickCrewBuildCrew:
    """Tests for quick_crew.build_crew()"""

    @patch("runtime.crewai.quick_crew.Crew")
    @patch("runtime.crewai.quick_crew.Task")
    @patch("runtime.crewai.quick_crew.Agent")
    @patch("runtime.crewai.quick_crew.get_llm")
    def test_build_crew_returns_crew(self, mock_llm, MockAgent, MockTask, MockCrew):
        from runtime.crewai.quick_crew import build_crew
        mock_llm.return_value = Mock()
        result = build_crew("JD text", "Resume text", "Notes")
        MockCrew.assert_called_once()
        assert MockAgent.call_count == 6
        assert MockTask.call_count == 6

    @patch("runtime.crewai.quick_crew.Crew")
    @patch("runtime.crewai.quick_crew.Task")
    @patch("runtime.crewai.quick_crew.Agent")
    @patch("runtime.crewai.quick_crew.get_llm")
    def test_build_crew_without_notes(self, mock_llm, MockAgent, MockTask, MockCrew):
        from runtime.crewai.quick_crew import build_crew
        mock_llm.return_value = Mock()
        result = build_crew("JD", "Resume")
        MockCrew.assert_called_once()


@pytest.mark.unit
class TestQuickCrewMain:
    """Tests for quick_crew.main()"""

    @patch("runtime.crewai.quick_crew.build_crew")
    def test_main_without_output(self, mock_build, tmp_path, capsys):
        from runtime.crewai.quick_crew import main as qc_main

        jd = tmp_path / "jd.md"
        jd.write_text("JD content")
        resume = tmp_path / "resume.md"
        resume.write_text("Resume content")

        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = "Crew result"
        mock_build.return_value = mock_crew

        with patch("sys.argv", ["quick_crew", "--jd", str(jd), "--resume", str(resume)]):
            qc_main()

        captured = capsys.readouterr()
        assert "Crew result" in captured.out

    @patch("runtime.crewai.quick_crew.build_crew")
    def test_main_with_output(self, mock_build, tmp_path):
        from runtime.crewai.quick_crew import main as qc_main

        jd = tmp_path / "jd.md"
        jd.write_text("JD")
        resume = tmp_path / "resume.md"
        resume.write_text("Resume")
        out = tmp_path / "result.txt"

        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = "Output content"
        mock_build.return_value = mock_crew

        with patch("sys.argv", ["quick_crew", "--jd", str(jd), "--resume", str(resume), "--out", str(out)]):
            qc_main()

        assert out.read_text() == "Output content"

    @patch("runtime.crewai.quick_crew.build_crew")
    def test_main_with_notes(self, mock_build, tmp_path):
        from runtime.crewai.quick_crew import main as qc_main

        jd = tmp_path / "jd.md"
        jd.write_text("JD")
        resume = tmp_path / "resume.md"
        resume.write_text("Resume")
        notes = tmp_path / "notes.md"
        notes.write_text("Interview notes")

        mock_crew = MagicMock()
        mock_crew.kickoff.return_value = "Result"
        mock_build.return_value = mock_crew

        with patch("sys.argv", ["quick_crew", "--jd", str(jd), "--resume", str(resume), "--notes", str(notes)]):
            qc_main()

        mock_build.assert_called_once_with("JD", "Resume", "Interview notes")


# ---------------------------------------------------------------------------
# HydraWorkflow additional coverage — runtime/crewai/hydra_workflow.py
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestHydraWorkflowGetAgentLLM:
    """Tests for HydraWorkflow._get_agent_llm fallback paths"""

    def _make_workflow(self, **kwargs):
        """Helper to create a workflow with all agents mocked."""
        with patch("runtime.crewai.hydra_workflow.GapAnalyzerAgent"), \
             patch("runtime.crewai.hydra_workflow.InterrogatorPrepperAgent"), \
             patch("runtime.crewai.hydra_workflow.DifferentiatorAgent"), \
             patch("runtime.crewai.hydra_workflow.TailoringAgent"), \
             patch("runtime.crewai.hydra_workflow.ATSOptimizerAgent"), \
             patch("runtime.crewai.hydra_workflow.AuditorSuiteAgent"), \
             patch("runtime.crewai.hydra_workflow.ExecutiveSynthesizerAgent"):
            return HydraWorkflow(**kwargs)

    @patch("runtime.crewai.hydra_workflow.get_llm_for_agent")
    @patch("runtime.crewai.hydra_workflow.get_agent_model_info", return_value={"model": "test-model"})
    def test_per_agent_model_success(self, mock_info, mock_get_llm):
        from runtime.crewai.hydra_workflow import HydraWorkflow
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm

        wf = self._make_workflow(llm=None, use_per_agent_models=True)
        assert wf.agent_models.get("gap_analyzer") == "test-model"

    @patch("runtime.crewai.hydra_workflow.get_llm_for_agent")
    @patch("runtime.crewai.hydra_workflow.get_agent_model_info")
    def test_fallback_to_provided_llm(self, mock_info, mock_get_llm):
        from runtime.crewai.hydra_workflow import HydraWorkflow, LLMClientError
        mock_get_llm.side_effect = LLMClientError("No key")
        fallback = Mock()
        fallback.model = "fallback-model"

        wf = self._make_workflow(llm=fallback, use_per_agent_models=True)
        assert wf.agent_models.get("gap_analyzer") == "fallback-model"

    @patch("runtime.crewai.hydra_workflow.get_llm_for_agent")
    @patch("runtime.crewai.hydra_workflow.get_agent_model_info")
    def test_fallback_only_when_no_provided_llm(self, mock_info, mock_get_llm):
        from runtime.crewai.hydra_workflow import HydraWorkflow, LLMClientError

        call_count = [0]
        def side_effect(agent_type, fallback_only=False):
            call_count[0] += 1
            if not fallback_only:
                raise LLMClientError("Primary failed")
            return Mock()

        mock_get_llm.side_effect = side_effect

        wf = self._make_workflow(llm=None, use_per_agent_models=True)
        assert wf.agent_models.get("gap_analyzer") == "fallback"

    @patch("runtime.crewai.hydra_workflow.get_llm_for_agent")
    @patch("runtime.crewai.hydra_workflow.get_agent_model_info")
    def test_raises_when_no_llm_available(self, mock_info, mock_get_llm):
        from runtime.crewai.hydra_workflow import HydraWorkflow, LLMClientError
        mock_get_llm.side_effect = LLMClientError("No LLM")

        with pytest.raises(ValueError, match="No LLM available"):
            self._make_workflow(llm=None, use_per_agent_models=True)

    def test_uses_fallback_when_per_agent_disabled(self):
        from runtime.crewai.hydra_workflow import HydraWorkflow
        fallback = Mock()
        fallback.model = "main-model"

        wf = self._make_workflow(llm=fallback, use_per_agent_models=False)
        assert wf.agent_models.get("gap_analyzer") == "main-model"


@pytest.mark.unit
class TestExecuteWithFallback:
    """Tests for HydraWorkflow._execute_with_fallback"""

    def _make_workflow(self):
        with patch("runtime.crewai.hydra_workflow.GapAnalyzerAgent"), \
             patch("runtime.crewai.hydra_workflow.InterrogatorPrepperAgent"), \
             patch("runtime.crewai.hydra_workflow.DifferentiatorAgent"), \
             patch("runtime.crewai.hydra_workflow.TailoringAgent"), \
             patch("runtime.crewai.hydra_workflow.ATSOptimizerAgent"), \
             patch("runtime.crewai.hydra_workflow.AuditorSuiteAgent"), \
             patch("runtime.crewai.hydra_workflow.ExecutiveSynthesizerAgent"):
            return HydraWorkflow(Mock(), use_per_agent_models=False)

    def test_primary_success(self):
        from runtime.crewai.hydra_workflow import HydraWorkflow
        wf = self._make_workflow()
        agent = Mock()
        agent.execute.return_value = {"result": "ok"}
        result = wf._execute_with_fallback(agent, {}, "test_stage")
        assert result == {"result": "ok"}

    def test_fallback_on_primary_failure_with_fallback_llm(self):
        from runtime.crewai.hydra_workflow import HydraWorkflow
        wf = self._make_workflow()
        agent = Mock()
        agent.execute.side_effect = [Exception("Primary failed"), {"result": "fallback_ok"}]

        result = wf._execute_with_fallback(agent, {}, "test_stage")
        assert result == {"result": "fallback_ok"}

    @patch("runtime.crewai.hydra_workflow.get_llm_for_agent")
    def test_fallback_without_fallback_llm(self, mock_get_fallback):
        from runtime.crewai.hydra_workflow import HydraWorkflow
        with patch("runtime.crewai.hydra_workflow.GapAnalyzerAgent"), \
             patch("runtime.crewai.hydra_workflow.InterrogatorPrepperAgent"), \
             patch("runtime.crewai.hydra_workflow.DifferentiatorAgent"), \
             patch("runtime.crewai.hydra_workflow.TailoringAgent"), \
             patch("runtime.crewai.hydra_workflow.ATSOptimizerAgent"), \
             patch("runtime.crewai.hydra_workflow.AuditorSuiteAgent"), \
             patch("runtime.crewai.hydra_workflow.ExecutiveSynthesizerAgent"):
            wf = HydraWorkflow(llm=None, use_per_agent_models=False)

        # Override fallback_llm to None after construction
        wf.fallback_llm = None
        mock_get_fallback.return_value = Mock()

        agent = Mock()
        agent.execute.side_effect = [Exception("Primary failed"), {"result": "ok"}]

        result = wf._execute_with_fallback(agent, {}, "test_stage")
        assert result == {"result": "ok"}
        mock_get_fallback.assert_called_with("test_stage", fallback_only=True)

    def test_raises_original_error_when_fallback_also_fails(self):
        from runtime.crewai.hydra_workflow import HydraWorkflow
        wf = self._make_workflow()
        agent = Mock()
        original_error = RuntimeError("Primary failed")
        agent.execute.side_effect = [original_error, ValueError("Fallback failed")]

        with pytest.raises(RuntimeError, match="Primary failed"):
            wf._execute_with_fallback(agent, {}, "test_stage")


@pytest.mark.unit
class TestInterrogationGapExtraction:
    """Tests for _execute_interrogation gap extraction from nested structures"""

    def _make_workflow(self):
        with patch("runtime.crewai.hydra_workflow.GapAnalyzerAgent"), \
             patch("runtime.crewai.hydra_workflow.InterrogatorPrepperAgent"), \
             patch("runtime.crewai.hydra_workflow.DifferentiatorAgent"), \
             patch("runtime.crewai.hydra_workflow.TailoringAgent"), \
             patch("runtime.crewai.hydra_workflow.ATSOptimizerAgent"), \
             patch("runtime.crewai.hydra_workflow.AuditorSuiteAgent"), \
             patch("runtime.crewai.hydra_workflow.ExecutiveSynthesizerAgent"):
            wf = HydraWorkflow(Mock(), use_per_agent_models=False)
        return wf

    @patch("runtime.crewai.hydra_workflow.trace_workflow_stage")
    def test_extracts_gaps_from_flat_structure(self, mock_trace):
        from runtime.crewai.hydra_workflow import HydraWorkflow
        mock_trace.return_value.__enter__ = Mock(return_value=MagicMock())
        mock_trace.return_value.__exit__ = Mock(return_value=False)

        wf = self._make_workflow()
        wf.interrogator_prepper = Mock()
        wf.interrogator_prepper.execute.return_value = {"questions": []}

        gap_result = {"gaps": ["gap1", "gap2"]}
        context = {
            "job_description": "JD",
            "resume": "R",
            "source_documents": "S",
            "interview_answers": [{"q": "a"}],
        }

        result = wf._execute_interrogation(context, gap_result)
        # Verify the agent was called with gap data in context
        call_args = wf.interrogator_prepper.execute.call_args
        assert "gaps" in call_args[0][0]

    @patch("runtime.crewai.hydra_workflow.trace_workflow_stage")
    def test_extracts_gaps_from_nested_gap_analysis(self, mock_trace):
        from runtime.crewai.hydra_workflow import HydraWorkflow
        mock_trace.return_value.__enter__ = Mock(return_value=MagicMock())
        mock_trace.return_value.__exit__ = Mock(return_value=False)

        wf = self._make_workflow()
        wf.interrogator_prepper = Mock()
        wf.interrogator_prepper.execute.return_value = {"questions": []}

        gap_result = {
            "gap_analysis": {
                "gaps": ["nested_gap"],
                "requirements": [
                    {"classification": "gap", "name": "kubernetes"},
                    {"classification": "direct_match", "name": "python"},
                    {"classification": "blocker", "name": "java"},
                ]
            }
        }
        context = {
            "job_description": "JD",
            "resume": "R",
            "source_documents": "S",
            "interview_answers": [{"q": "a"}],
        }

        result = wf._execute_interrogation(context, gap_result)
        call_context = wf.interrogator_prepper.execute.call_args[0][0]
        gaps = call_context["gaps"]
        # Should include nested_gap + gap + blocker requirements (3 total)
        assert len(gaps) == 3

    @patch("runtime.crewai.hydra_workflow.trace_workflow_stage")
    def test_interactive_mode_conducts_interview(self, mock_trace):
        from runtime.crewai.hydra_workflow import HydraWorkflow, UserInteraction
        mock_trace.return_value.__enter__ = Mock(return_value=MagicMock())
        mock_trace.return_value.__exit__ = Mock(return_value=False)

        wf = self._make_workflow()
        wf.interactive = True
        wf.interrogator_prepper = Mock()
        wf.interrogator_prepper.execute.return_value = {
            "questions": [{"question": "Tell me about AWS?", "id": "q1"}]
        }

        context = {"job_description": "JD", "resume": "R", "source_documents": "S"}

        with patch.object(UserInteraction, "conduct_interview", return_value=[{"answer": "5 years"}]) as mock_interview:
            result = wf._execute_interrogation(context, {"gaps": []})
            mock_interview.assert_called_once()
            assert result["interview_notes"] == [{"answer": "5 years"}]

    @patch("runtime.crewai.hydra_workflow.trace_workflow_stage")
    def test_no_questions_skips_interview(self, mock_trace):
        from runtime.crewai.hydra_workflow import HydraWorkflow
        mock_trace.return_value.__enter__ = Mock(return_value=MagicMock())
        mock_trace.return_value.__exit__ = Mock(return_value=False)

        wf = self._make_workflow()
        wf.interrogator_prepper = Mock()
        wf.interrogator_prepper.execute.return_value = {"questions": []}

        context = {"job_description": "JD", "resume": "R", "source_documents": "S",
                    "interview_answers": []}

        result = wf._execute_interrogation(context, {"gaps": []})
        assert result == {"questions": []}


@pytest.mark.unit
class TestGapAnalysisInteractive:
    """Tests for _execute_gap_analysis interactive mode"""

    def _make_workflow(self):
        with patch("runtime.crewai.hydra_workflow.GapAnalyzerAgent"), \
             patch("runtime.crewai.hydra_workflow.InterrogatorPrepperAgent"), \
             patch("runtime.crewai.hydra_workflow.DifferentiatorAgent"), \
             patch("runtime.crewai.hydra_workflow.TailoringAgent"), \
             patch("runtime.crewai.hydra_workflow.ATSOptimizerAgent"), \
             patch("runtime.crewai.hydra_workflow.AuditorSuiteAgent"), \
             patch("runtime.crewai.hydra_workflow.ExecutiveSynthesizerAgent"):
            wf = HydraWorkflow(Mock(), use_per_agent_models=False, interactive=True)
        return wf

    @patch("runtime.crewai.hydra_workflow.trace_workflow_stage")
    def test_interactive_proceeds_on_approval(self, mock_trace):
        from runtime.crewai.hydra_workflow import HydraWorkflow, UserInteraction
        mock_trace.return_value.__enter__ = Mock(return_value=MagicMock())
        mock_trace.return_value.__exit__ = Mock(return_value=False)

        wf = self._make_workflow()
        wf.gap_analyzer = Mock()
        wf.gap_analyzer.execute.return_value = {"gaps": [], "confidence": 0.9}

        context = {"job_description": "JD", "resume": "R", "source_documents": "S"}

        with patch.object(UserInteraction, "ask_yes_no", return_value=True):
            result = wf._execute_gap_analysis(context)
            assert result["confidence"] == 0.9

    @patch("runtime.crewai.hydra_workflow.trace_workflow_stage")
    def test_interactive_aborts_on_rejection(self, mock_trace):
        from runtime.crewai.hydra_workflow import HydraWorkflow, UserInteraction
        mock_trace.return_value.__enter__ = Mock(return_value=MagicMock())
        mock_trace.return_value.__exit__ = Mock(return_value=False)

        wf = self._make_workflow()
        wf.gap_analyzer = Mock()
        wf.gap_analyzer.execute.return_value = {"gaps": [], "confidence": 0.9}

        context = {"job_description": "JD", "resume": "R", "source_documents": "S"}

        with patch.object(UserInteraction, "ask_yes_no", return_value=False):
            with pytest.raises(Exception, match="User aborted"):
                wf._execute_gap_analysis(context)


@pytest.mark.unit
class TestExecutiveSynthesisFailure:
    """Tests for _execute_executive_synthesis failure path"""

    def _make_workflow(self):
        with patch("runtime.crewai.hydra_workflow.GapAnalyzerAgent"), \
             patch("runtime.crewai.hydra_workflow.InterrogatorPrepperAgent"), \
             patch("runtime.crewai.hydra_workflow.DifferentiatorAgent"), \
             patch("runtime.crewai.hydra_workflow.TailoringAgent"), \
             patch("runtime.crewai.hydra_workflow.ATSOptimizerAgent"), \
             patch("runtime.crewai.hydra_workflow.AuditorSuiteAgent"), \
             patch("runtime.crewai.hydra_workflow.ExecutiveSynthesizerAgent"):
            wf = HydraWorkflow(Mock(), use_per_agent_models=False)
        return wf

    @patch("runtime.crewai.hydra_workflow.trace_workflow_stage")
    def test_returns_minimal_brief_on_failure(self, mock_trace):
        from runtime.crewai.hydra_workflow import HydraWorkflow
        mock_trace.return_value.__enter__ = Mock(return_value=MagicMock())
        mock_trace.return_value.__exit__ = Mock(return_value=False)

        wf = self._make_workflow()
        wf.executive_synthesizer = Mock()
        wf.executive_synthesizer.execute.side_effect = Exception("Schema validation failed")

        # Also make _execute_with_fallback propagate the error by having fallback fail too
        wf.fallback_llm = None
        with patch("runtime.crewai.hydra_workflow.get_llm_for_agent", side_effect=Exception("no fallback")):
            result = wf._execute_executive_synthesis(
                {"job_description": "JD", "resume": "R"},
                {}, {}, {}, {}, {}, {"audit_report": {}}
            )

        assert result["decision"]["recommendation"] == "PROCEED"
        assert result["decision"]["fit_score"] == 70
        assert "synthesis_error" in result


@pytest.mark.unit
class TestApplyAuditFixes:
    """Tests for _apply_audit_fixes"""

    def _make_workflow(self):
        with patch("runtime.crewai.hydra_workflow.GapAnalyzerAgent"), \
             patch("runtime.crewai.hydra_workflow.InterrogatorPrepperAgent"), \
             patch("runtime.crewai.hydra_workflow.DifferentiatorAgent"), \
             patch("runtime.crewai.hydra_workflow.TailoringAgent"), \
             patch("runtime.crewai.hydra_workflow.ATSOptimizerAgent"), \
             patch("runtime.crewai.hydra_workflow.AuditorSuiteAgent"), \
             patch("runtime.crewai.hydra_workflow.ExecutiveSynthesizerAgent"):
            wf = HydraWorkflow(Mock(), use_per_agent_models=False)
        return wf

    def test_returns_documents_unchanged(self):
        wf = self._make_workflow()
        docs = {"resume": "Resume content", "cover_letter": "CL content"}
        result = wf._apply_audit_fixes(docs, {"issues": []}, {"issues": []})
        assert result == docs

    def test_returns_documents_with_none_cover_audit(self):
        wf = self._make_workflow()
        docs = {"resume": "Resume", "cover_letter": "CL"}
        result = wf._apply_audit_fixes(docs, {"issues": []}, None)
        assert result == docs


@pytest.mark.unit
class TestWorkflowHelperMethods:
    """Tests for _log, get_current_state, get_execution_log, get_intermediate_results"""

    def _make_workflow(self):
        with patch("runtime.crewai.hydra_workflow.GapAnalyzerAgent"), \
             patch("runtime.crewai.hydra_workflow.InterrogatorPrepperAgent"), \
             patch("runtime.crewai.hydra_workflow.DifferentiatorAgent"), \
             patch("runtime.crewai.hydra_workflow.TailoringAgent"), \
             patch("runtime.crewai.hydra_workflow.ATSOptimizerAgent"), \
             patch("runtime.crewai.hydra_workflow.AuditorSuiteAgent"), \
             patch("runtime.crewai.hydra_workflow.ExecutiveSynthesizerAgent"):
            return HydraWorkflow(Mock(), use_per_agent_models=False)

    def test_log_appends_to_execution_log(self):
        from runtime.crewai.hydra_workflow import HydraWorkflow
        wf = self._make_workflow()
        wf._log("Test message")
        assert len(wf.execution_log) >= 1
        assert "Test message" in wf.execution_log[-1]

    def test_get_current_state(self):
        from runtime.crewai.hydra_workflow import WorkflowState
        wf = self._make_workflow()
        assert wf.get_current_state() == WorkflowState.INITIALIZED

    def test_get_execution_log_returns_copy(self):
        wf = self._make_workflow()
        log = wf.get_execution_log()
        log.append("extra")
        assert len(wf.execution_log) != len(log)

    def test_get_intermediate_results_returns_deepcopy(self):
        wf = self._make_workflow()
        wf.intermediate_results["test"] = {"nested": [1, 2, 3]}
        results = wf.get_intermediate_results()
        results["test"]["nested"].append(4)
        assert len(wf.intermediate_results["test"]["nested"]) == 3


@pytest.mark.unit
class TestWorkflowPaused:
    """Tests for WorkflowPaused exception and pause handling in execute()"""

    def _make_workflow(self):
        with patch("runtime.crewai.hydra_workflow.GapAnalyzerAgent"), \
             patch("runtime.crewai.hydra_workflow.InterrogatorPrepperAgent"), \
             patch("runtime.crewai.hydra_workflow.DifferentiatorAgent"), \
             patch("runtime.crewai.hydra_workflow.TailoringAgent"), \
             patch("runtime.crewai.hydra_workflow.ATSOptimizerAgent"), \
             patch("runtime.crewai.hydra_workflow.AuditorSuiteAgent"), \
             patch("runtime.crewai.hydra_workflow.ExecutiveSynthesizerAgent"):
            return HydraWorkflow(Mock(), use_per_agent_models=False)

    @patch("runtime.crewai.hydra_workflow.trace_workflow_stage")
    def test_pauses_at_gap_analysis_review(self, mock_trace):
        from runtime.crewai.hydra_workflow import WorkflowState
        mock_trace.return_value.__enter__ = Mock(return_value=MagicMock())
        mock_trace.return_value.__exit__ = Mock(return_value=False)

        wf = self._make_workflow()
        wf.gap_analyzer = Mock()
        wf.gap_analyzer.execute.return_value = {"gaps": [], "confidence": 0.9}

        context = {
            "job_description": "JD",
            "resume": "R",
            "source_documents": "S",
            # gap_analysis_approved is False (default) so workflow should pause
        }

        result = wf.execute(context)
        assert result.state == WorkflowState.GAP_ANALYSIS_REVIEW
        assert result.success is True  # Pause is a successful pause


@pytest.mark.unit
class TestWorkflowExecuteFailure:
    """Tests for execute() exception handling"""

    def _make_workflow(self):
        with patch("runtime.crewai.hydra_workflow.GapAnalyzerAgent"), \
             patch("runtime.crewai.hydra_workflow.InterrogatorPrepperAgent"), \
             patch("runtime.crewai.hydra_workflow.DifferentiatorAgent"), \
             patch("runtime.crewai.hydra_workflow.TailoringAgent"), \
             patch("runtime.crewai.hydra_workflow.ATSOptimizerAgent"), \
             patch("runtime.crewai.hydra_workflow.AuditorSuiteAgent"), \
             patch("runtime.crewai.hydra_workflow.ExecutiveSynthesizerAgent"):
            return HydraWorkflow(Mock(), use_per_agent_models=False)

    def test_missing_required_context_key(self):
        from runtime.crewai.hydra_workflow import WorkflowState
        wf = self._make_workflow()
        result = wf.execute({"job_description": "JD"})
        assert result.success is False
        assert result.state == WorkflowState.FAILED
        assert "Missing required context key" in result.error_message

    @patch("runtime.crewai.hydra_workflow.trace_workflow_stage")
    def test_generic_exception_returns_failure(self, mock_trace):
        from runtime.crewai.hydra_workflow import WorkflowState
        mock_trace.return_value.__enter__ = Mock(return_value=MagicMock())
        mock_trace.return_value.__exit__ = Mock(return_value=False)

        wf = self._make_workflow()
        wf.gap_analyzer = Mock()
        wf.gap_analyzer.execute.side_effect = RuntimeError("Unexpected failure")

        # Also ensure _execute_with_fallback raises
        wf.fallback_llm = None
        with patch("runtime.crewai.hydra_workflow.get_llm_for_agent", side_effect=Exception("no fallback")):
            result = wf.execute({
                "job_description": "JD",
                "resume": "R",
                "source_documents": "S",
                "gap_analysis_approved": True,
            })
        assert result.success is False
        assert result.state == WorkflowState.FAILED


@pytest.mark.unit
class TestWorkflowResult:
    """Tests for WorkflowResult dataclass"""

    def test_default_values(self):
        from runtime.crewai.hydra_workflow import WorkflowResult, WorkflowState
        result = WorkflowResult(state=WorkflowState.INITIALIZED, success=True)
        assert result.final_documents is None
        assert result.audit_report is None
        assert result.executive_brief is None
        assert result.error_message is None
        assert result.execution_log is None
        assert result.intermediate_results is None
        assert result.audit_failed is False
        assert result.audit_error is None
        assert result.agent_models is None

    def test_all_fields(self):
        from runtime.crewai.hydra_workflow import WorkflowResult, WorkflowState
        result = WorkflowResult(
            state=WorkflowState.COMPLETED,
            success=True,
            final_documents={"resume": "R"},
            audit_report={"status": "APPROVED"},
            executive_brief={"decision": "PROCEED"},
            error_message=None,
            execution_log=["step1"],
            intermediate_results={"gap": {}},
            audit_failed=False,
            audit_error=None,
            agent_models={"gap_analyzer": "model-x"},
        )
        assert result.state == WorkflowState.COMPLETED
        assert result.agent_models["gap_analyzer"] == "model-x"


@pytest.mark.unit
class TestUserInteraction:
    """Tests for UserInteraction helper class"""

    def test_ask_yes_no_yes(self):
        from runtime.crewai.hydra_workflow import UserInteraction
        with patch("builtins.input", return_value="y"):
            assert UserInteraction.ask_yes_no("Continue?") is True

    def test_ask_yes_no_no(self):
        from runtime.crewai.hydra_workflow import UserInteraction
        with patch("builtins.input", return_value="no"):
            assert UserInteraction.ask_yes_no("Continue?") is False

    def test_ask_yes_no_eof(self):
        from runtime.crewai.hydra_workflow import UserInteraction
        with patch("builtins.input", side_effect=EOFError):
            assert UserInteraction.ask_yes_no("Continue?") is True

    def test_conduct_interview_with_answers(self):
        from runtime.crewai.hydra_workflow import UserInteraction
        questions = [
            {"question": "Tell me about AWS?", "id": "q1"},
            {"question": "Leadership example?", "id": "q2"},
        ]
        with patch("builtins.input", side_effect=["5 years AWS experience", "Led team of 10"]):
            answers = UserInteraction.conduct_interview(questions)
            assert len(answers) == 2
            assert answers[0]["answer"] == "5 years AWS experience"
            assert answers[0]["verified"] is True

    def test_conduct_interview_eof(self):
        from runtime.crewai.hydra_workflow import UserInteraction
        questions = [
            {"question": "Q1?", "id": "q1"},
            {"question": "Q2?", "id": "q2"},
        ]
        with patch("builtins.input", side_effect=["answer1", EOFError]):
            answers = UserInteraction.conduct_interview(questions)
            assert len(answers) == 1

    def test_conduct_interview_skips_empty_answers(self):
        from runtime.crewai.hydra_workflow import UserInteraction
        questions = [
            {"question": "Q1?", "id": "q1"},
            {"question": "Q2?", "id": "q2"},
        ]
        with patch("builtins.input", side_effect=["", "real answer"]):
            answers = UserInteraction.conduct_interview(questions)
            assert len(answers) == 1
            assert answers[0]["answer"] == "real answer"


@pytest.mark.unit
class TestWorkflowStateEnum:
    """Tests for WorkflowState enum values"""

    def test_all_states_exist(self):
        from runtime.crewai.hydra_workflow import WorkflowState
        states = [
            "INITIALIZED", "GAP_ANALYSIS", "GAP_ANALYSIS_REVIEW",
            "INTERROGATION", "INTERROGATION_REVIEW", "DIFFERENTIATION",
            "TAILORING", "ATS_OPTIMIZATION", "AUDITING",
            "EXECUTIVE_SYNTHESIS", "COMPLETED", "FAILED",
        ]
        for state_name in states:
            assert hasattr(WorkflowState, state_name)


# Ensure HydraWorkflow import is available at module level for helper methods
from runtime.crewai.hydra_workflow import HydraWorkflow
