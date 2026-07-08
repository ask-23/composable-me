"""
Unit tests for the CLI wrapper.

These tests focus on argument handling and file I/O; workflow execution is
stubbed to avoid calling the live LLM. Integration tests cover the real flow.
"""

import json
from types import SimpleNamespace

import pytest

from runtime.crewai.hydra_workflow import RunStatus


def test_cli_requires_arguments():
    """CLI should exit with error when required args are missing."""
    from runtime.crewai import cli

    with pytest.raises(SystemExit) as excinfo:
        cli.main([])

    assert excinfo.value.code != 0


def _stub_result(**overrides):
    """A WorkflowResult-shaped stub with sane defaults."""
    base = dict(
        success=True,
        status=RunStatus.COMPLETED,
        final_documents={"resume": "resume output", "cover_letter": "cover letter output"},
        audit_report={"final_status": "APPROVED"},
        executive_brief={"decision": {"recommendation": "PROCEED", "fit_score": 72}},
        execution_log=["step1", "step2"],
        intermediate_results={},
        agent_models={"gap_analyzer": "test-model"},
        audit_failed=False,
        audit_error=None,
        error_message=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_cli_runs_workflow_and_writes_run_scoped_outputs(tmp_path, monkeypatch, capsys):
    """CLI runs the workflow, writes a run-scoped directory + manifest, reports success."""
    from runtime.crewai import cli

    jd_file = tmp_path / "jd.md"
    resume_file = tmp_path / "resume.md"
    sources_dir = tmp_path / "sources"
    out_dir = tmp_path / "out"

    jd_file.write_text("JD content")
    resume_file.write_text("Resume content")
    sources_dir.mkdir()
    (sources_dir / "source.txt").write_text("Source content")

    captured_context = {}

    class StubWorkflow:
        def __init__(self, llm, max_audit_retries=2, interactive=False, auto_approve=False):
            self.llm = llm
            self.max_audit_retries = max_audit_retries

        def execute(self, context):
            captured_context.update(context)
            return _stub_result()

    monkeypatch.setattr(cli, "get_llm_client", lambda *args, **kwargs: "stub-llm")
    monkeypatch.setattr(cli, "HydraWorkflow", StubWorkflow)

    exit_code = cli.main(
        [
            "--jd",
            str(jd_file),
            "--resume",
            str(resume_file),
            "--sources",
            str(sources_dir),
            "--out",
            str(out_dir),
        ]
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert "Success" in stdout

    # Outputs land in a single run-scoped subdirectory, not directly in out_dir.
    run_dirs = [p for p in out_dir.iterdir() if p.is_dir()]
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]

    assert (run_dir / "resume.md").read_text() == "resume output"
    assert (run_dir / "cover_letter.md").read_text() == "cover letter output"
    assert "final_status: APPROVED" in (run_dir / "audit_report.yaml").read_text()
    assert "step1" in (run_dir / "execution_log.txt").read_text()

    # The run manifest records status, decision, and artifacts — but no PII.
    manifest = json.loads((run_dir / "run.json").read_text())
    assert manifest["status"] == "completed"
    assert manifest["decision"]["recommendation"] == "PROCEED"
    assert "resume.md" in manifest["artifacts"]
    assert manifest["inputs"]["resume_chars"] == len("Resume content")
    assert "Resume content" not in (run_dir / "run.json").read_text()

    # Context forwarded into workflow.
    assert captured_context["job_description"] == "JD content"
    assert captured_context["resume"] == "Resume content"
    assert "Source content" in captured_context["source_documents"]


def test_cli_audit_rejected_returns_partial_exit_code(tmp_path, monkeypatch, capsys):
    """A rejected audit still writes outputs but returns a non-zero (partial) code."""
    from runtime.crewai import cli

    jd_file = tmp_path / "jd.md"
    resume_file = tmp_path / "resume.md"
    sources_dir = tmp_path / "sources"
    out_dir = tmp_path / "out"
    jd_file.write_text("JD")
    resume_file.write_text("Resume")
    sources_dir.mkdir()
    (sources_dir / "s.txt").write_text("Source")

    class StubWorkflow:
        def __init__(self, llm, max_audit_retries=2, interactive=False, auto_approve=False):
            pass

        def execute(self, context):
            return _stub_result(
                status=RunStatus.COMPLETED_WITH_AUDIT_CONCERNS,
                audit_report={"final_status": "REJECTED"},
                audit_failed=True,
                audit_error="Document did not pass audit",
            )

    monkeypatch.setattr(cli, "get_llm_client", lambda *args, **kwargs: "stub-llm")
    monkeypatch.setattr(cli, "HydraWorkflow", StubWorkflow)

    exit_code = cli.main(
        [
            "--jd",
            str(jd_file),
            "--resume",
            str(resume_file),
            "--sources",
            str(sources_dir),
            "--out",
            str(out_dir),
        ]
    )

    assert exit_code == 1
    assert "rejected" in capsys.readouterr().out.lower()
