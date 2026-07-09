"""Run artifacts: canonical filenames, a run-scoped writer, and a run manifest.

A multi-agent run should leave an inspectable trail. This module centralizes the
artifact filenames (previously string literals inside the CLI) and writes each run
into its own ``output/<run_id>/`` directory so consecutive runs no longer clobber
each other. Every run also emits a ``run.json`` manifest summarizing what happened —
status, per-stage models, the executive decision, and the produced files — so a run
can be understood without re-reading the whole log.

The manifest deliberately records input *sizes*, not input *content*: no résumé or
job-description text is written to it.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional

import yaml

RESUME_FILE = "resume.md"
COVER_LETTER_FILE = "cover_letter.md"
AUDIT_REPORT_FILE = "audit_report.yaml"
EXECUTION_LOG_FILE = "execution_log.txt"
MANIFEST_FILE = "run.json"
INTERMEDIATE_DIR = "intermediate"


@dataclass
class RunInputs:
    """Lightweight, PII-free summary of a run's inputs (sizes and names only)."""

    job_description_chars: int = 0
    resume_chars: int = 0
    sources_chars: int = 0
    jd_path: Optional[str] = None
    resume_path: Optional[str] = None
    sources_path: Optional[str] = None


def generate_run_id(now: Optional[datetime] = None) -> str:
    """Return a sortable, unique run id: ``YYYYmmdd-HHMMSS-<8 hex>``."""
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


def _sanitize_warning(message: Any) -> str:
    """Strip any raw agent output from an error message before it enters the manifest.

    Validation errors embed a slice of the model's raw output (e.g. after
    "Output was:"), which for the tailoring agent is the résumé itself. The manifest
    is PII-free by contract, so keep only the first line up to that marker.
    """
    text = str(message)
    for marker in ("Output was:", "\n\nOutput was", "Output was\n"):
        idx = text.find(marker)
        if idx != -1:
            text = text[:idx]
            break
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    return first_line[:200]


def build_manifest(run_id: str, result: Any, inputs: Optional[RunInputs] = None) -> dict:
    """Assemble the JSON-serializable run manifest from a WorkflowResult."""
    audit_report = getattr(result, "audit_report", None) or {}
    brief = getattr(result, "executive_brief", None) or {}
    decision = brief.get("decision", {}) if isinstance(brief, dict) else {}
    status = getattr(result, "status", None)
    log_lines = getattr(result, "execution_log", None) or []

    warnings = []
    audit_error = getattr(result, "audit_error", None)
    error_message = getattr(result, "error_message", None)
    if audit_error:
        warnings.append(_sanitize_warning(audit_error))
    if error_message:
        warnings.append(_sanitize_warning(error_message))

    # "passed" is derived from an explicit APPROVED verdict, and is null when no audit
    # ran (e.g. a pre-audit failure). Do NOT infer "passed" from audit_failed's default
    # False, or a failed run with no audit would falsely claim the audit passed.
    final_status = audit_report.get("final_status")
    audit_passed = (final_status == "APPROVED") if final_status else None

    manifest = {
        "run_id": run_id,
        "status": status.value if hasattr(status, "value") else status,
        "success": getattr(result, "success", None),
        "audit": {
            "final_status": final_status,
            "passed": audit_passed,
        },
        "decision": {
            "recommendation": decision.get("recommendation"),
            "fit_score": decision.get("fit_score"),
        },
        "models": getattr(result, "agent_models", None) or {},
        "log_lines": len(list(log_lines)) if isinstance(log_lines, Iterable) else 0,
        "warnings": warnings,
    }
    if inputs is not None:
        manifest["inputs"] = {
            "job_description_chars": inputs.job_description_chars,
            "resume_chars": inputs.resume_chars,
            "sources_chars": inputs.sources_chars,
            "jd_path": inputs.jd_path,
            "resume_path": inputs.resume_path,
            "sources_path": inputs.sources_path,
        }
    return manifest


def write_run_artifacts(
    base_dir: Path,
    result: Any,
    run_id: Optional[str] = None,
    inputs: Optional[RunInputs] = None,
    include_intermediate: bool = False,
) -> Path:
    """Write all artifacts for a run into ``base_dir/<run_id>/`` and return that dir.

    Always writes the manifest; writes documents/audit/log when present. Returns the
    run directory so callers can report exactly where the output landed.
    """
    run_id = run_id or generate_run_id()
    run_dir = Path(base_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    final_docs = getattr(result, "final_documents", None) or {}
    artifacts: list[str] = []

    if final_docs.get("resume") is not None:
        (run_dir / RESUME_FILE).write_text(final_docs.get("resume", ""))
        artifacts.append(RESUME_FILE)
    if final_docs.get("cover_letter") is not None:
        (run_dir / COVER_LETTER_FILE).write_text(final_docs.get("cover_letter", ""))
        artifacts.append(COVER_LETTER_FILE)

    audit_report = getattr(result, "audit_report", None)
    if audit_report is not None:
        (run_dir / AUDIT_REPORT_FILE).write_text(yaml.safe_dump(audit_report, sort_keys=False))
        artifacts.append(AUDIT_REPORT_FILE)

    log_lines = getattr(result, "execution_log", None) or []
    if isinstance(log_lines, Iterable):
        (run_dir / EXECUTION_LOG_FILE).write_text("\n".join(log_lines))
        artifacts.append(EXECUTION_LOG_FILE)

    if include_intermediate and getattr(result, "intermediate_results", None):
        intermediate_dir = run_dir / INTERMEDIATE_DIR
        intermediate_dir.mkdir(parents=True, exist_ok=True)
        for stage_name, stage_result in result.intermediate_results.items():
            (intermediate_dir / f"{stage_name}.yaml").write_text(
                yaml.safe_dump(stage_result, sort_keys=False, default_flow_style=False)
            )

    manifest = build_manifest(run_id, result, inputs)
    manifest["artifacts"] = artifacts
    (run_dir / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2, default=str))

    return run_dir
