"""Unit tests for run artifacts and the run manifest."""

import json
from types import SimpleNamespace

from runtime.crewai import artifacts
from runtime.crewai.artifacts import RunInputs, build_manifest, generate_run_id, write_run_artifacts
from runtime.crewai.hydra_workflow import RunStatus


def _result(**overrides):
    base = dict(
        success=True,
        status=RunStatus.COMPLETED,
        final_documents={"resume": "R", "cover_letter": "C"},
        audit_report={"final_status": "APPROVED"},
        executive_brief={"decision": {"recommendation": "PROCEED", "fit_score": 71}},
        execution_log=["a", "b", "c"],
        intermediate_results={"gap_analysis": {"x": 1}},
        agent_models={"gap_analyzer": "m1"},
        audit_failed=False,
        audit_error=None,
        error_message=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_generate_run_id_is_sortable_and_unique():
    a = generate_run_id()
    b = generate_run_id()
    assert a != b
    # YYYYmmdd-HHMMSS-<8 hex>
    stamp, _, suffix = a.rpartition("-")
    assert len(suffix) == 8
    assert len(stamp) == len("20260101-120000")


def test_build_manifest_summarizes_outcome_without_pii():
    inputs = RunInputs(job_description_chars=10, resume_chars=20, sources_chars=30, jd_path="jd.md")
    result = _result(final_documents={"resume": "SECRET_RESUME_BODY", "cover_letter": "SECRET_CL"})
    manifest = build_manifest("rid", result, inputs)

    assert manifest["run_id"] == "rid"
    assert manifest["status"] == "completed"
    assert manifest["audit"]["final_status"] == "APPROVED"
    assert manifest["audit"]["passed"] is True
    assert manifest["decision"] == {"recommendation": "PROCEED", "fit_score": 71}
    assert manifest["models"] == {"gap_analyzer": "m1"}
    assert manifest["log_lines"] == 3
    assert manifest["inputs"]["resume_chars"] == 20
    # Manifest carries sizes, never document content.
    serialized = json.dumps(manifest)
    assert "SECRET_RESUME_BODY" not in serialized
    assert "SECRET_CL" not in serialized


def test_write_run_artifacts_creates_run_scoped_dir(tmp_path):
    run_dir = write_run_artifacts(tmp_path, _result(), run_id="rid-1", include_intermediate=True)

    assert run_dir == tmp_path / "rid-1"
    assert (run_dir / artifacts.RESUME_FILE).read_text() == "R"
    assert (run_dir / artifacts.COVER_LETTER_FILE).read_text() == "C"
    assert (run_dir / artifacts.AUDIT_REPORT_FILE).exists()
    assert (run_dir / artifacts.EXECUTION_LOG_FILE).read_text() == "a\nb\nc"
    assert (run_dir / artifacts.INTERMEDIATE_DIR / "gap_analysis.yaml").exists()

    manifest = json.loads((run_dir / artifacts.MANIFEST_FILE).read_text())
    assert manifest["artifacts"] == [
        artifacts.RESUME_FILE,
        artifacts.COVER_LETTER_FILE,
        artifacts.AUDIT_REPORT_FILE,
        artifacts.EXECUTION_LOG_FILE,
    ]


def test_write_run_artifacts_two_runs_do_not_clobber(tmp_path):
    write_run_artifacts(tmp_path, _result(final_documents={"resume": "first"}), run_id="r1")
    write_run_artifacts(tmp_path, _result(final_documents={"resume": "second"}), run_id="r2")

    assert (tmp_path / "r1" / artifacts.RESUME_FILE).read_text() == "first"
    assert (tmp_path / "r2" / artifacts.RESUME_FILE).read_text() == "second"


def test_manifest_warnings_strip_raw_output_pii():
    # A validation error embeds raw agent output (résumé text) after "Output was:".
    leaky = (
        "Invalid JSON output: line 1\n\nOutput was:\n"
        "{'name': 'Jane Candidate', 'phone': '555-0100', ...}"
    )
    result = _result(status=RunStatus.FAILED, error_message=leaky, audit_error=None)
    manifest = build_manifest("rid", result)
    serialized = str(manifest["warnings"])
    assert "Jane Candidate" not in serialized
    assert "555-0100" not in serialized
    assert "Invalid JSON output" in serialized  # the summary line survives
