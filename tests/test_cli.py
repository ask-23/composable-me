"""
Unit tests for the CLI wrapper.

These tests focus on argument handling and file I/O; workflow execution is
stubbed to avoid calling the live LLM. Integration tests cover the real flow.
"""

from types import SimpleNamespace

import pytest


def test_cli_requires_arguments():
    """CLI should exit with error when required args are missing."""
    # Import inline to allow failure before the CLI is implemented
    from runtime.crewai import cli  # noqa: WPS433

    with pytest.raises(SystemExit) as excinfo:
        cli.main([])

    assert excinfo.value.code != 0


def test_cli_runs_workflow_and_writes_outputs(tmp_path, monkeypatch, capsys):
    """CLI should run workflow, write outputs, and report success."""
    from runtime.crewai import cli  # noqa: WPS433

    jd_file = tmp_path / "jd.md"
    resume_file = tmp_path / "resume.md"
    sources_dir = tmp_path / "sources"
    out_dir = tmp_path / "out"

    jd_file.write_text("JD content")
    resume_file.write_text("Resume content")
    sources_dir.mkdir()
    (sources_dir / "source.txt").write_text("Source content")

    # Stub LLM + workflow to avoid live calls
    captured_context = {}

    class StubWorkflow:
        def __init__(self, llm, max_audit_retries=2):
            self.llm = llm
            self.max_audit_retries = max_audit_retries

        def execute(self, context):
            captured_context.update(context)
            return SimpleNamespace(
                success=True,
                final_documents={
                    "resume": "resume output",
                    "cover_letter": "cover letter output",
                },
                audit_report={"final_status": "APPROVED", "retry_count": 0},
                execution_log=["step1", "step2"],
                error_message=None,
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

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert "Success" in stdout

    # Files are written
    assert (out_dir / "resume.md").read_text() == "resume output"
    assert (out_dir / "cover_letter.md").read_text() == "cover letter output"
    assert "final_status: APPROVED" in (out_dir / "audit_report.yaml").read_text()
    assert "step1" in (out_dir / "execution_log.txt").read_text()

    # Context forwarded into workflow
    assert captured_context["job_description"] == "JD content"
    assert captured_context["resume"] == "Resume content"
    assert "Source content" in captured_context["source_documents"]
