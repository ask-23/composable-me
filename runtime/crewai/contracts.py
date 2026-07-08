"""Typed contracts for the stage boundaries of the Hydra workflow.

Agents return free-form JSON whose exact shape varies from model to model. Rather
than probe nested dictionaries defensively at every call site, the workflow coerces
each agent's raw output into one of these typed contracts at the boundary. Coercion
is *lenient on input* (it accepts the several shapes models actually emit) and
*strict on output* (downstream code sees a stable, typed object).

Keeping this logic in one tested place removes the `isinstance` / nested-`.get()`
spelunking that previously lived inside `hydra_workflow.py`.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

_TRUTHY = {"true", "yes", "y", "approved", "approve", "pass", "passed", "ok", "1"}
_FALSY = {"false", "no", "n", "rejected", "reject", "fail", "failed", "0", ""}


def coerce_text(value: Any) -> str:
    """Coerce a document-ish value to plain text.

    Agents variously return a string, a dict like ``{"content": "..."}`` /
    ``{"text": "..."}`` / ``{"markdown": "..."}``, or a list of sections/lines
    (joined with newlines). Anything else becomes "".
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(coerce_text(v) for v in value if coerce_text(v))
    if isinstance(value, dict):
        for key in ("content", "text", "markdown", "body"):
            inner = value.get(key)
            if isinstance(inner, str) and inner.strip():
                return inner
        return ""
    return str(value)


def coerce_bool(value: Any, default: bool = False) -> bool:
    """Coerce an approval-ish value to a bool, treating strings by meaning.

    ``bool("false")`` is ``True`` in Python, so a model that returns a *string*
    "false"/"no"/"rejected" must be parsed by content, not truthiness. Unknown
    shapes fall back to ``default`` (rejection, for the audit gate).
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        token = value.strip().lower()
        if token in _TRUTHY:
            return True
        if token in _FALSY:
            return False
    return default


def _first_dict(raw: Any, *keys: str) -> dict:
    """Return the first value among ``keys`` that is a dict, else the raw dict."""
    if not isinstance(raw, dict):
        return {}
    for key in keys:
        value = raw.get(key)
        if isinstance(value, dict):
            return value
    return raw


class TailoredDocuments(BaseModel):
    """Canonical tailored résumé + cover letter, extracted from the Tailoring agent."""

    resume: str = ""
    cover_letter: str = ""

    @classmethod
    def from_raw(cls, raw: Any) -> "TailoredDocuments":
        if not isinstance(raw, dict):
            return cls()
        resume = cover = ""
        # Preferred nested shape: {"tailored_output": {"resume": {"content": ...}}}
        output = raw.get("tailored_output")
        if isinstance(output, dict):
            resume = coerce_text(output.get("resume"))
            cover = coerce_text(output.get("cover_letter"))
        # Flat fallbacks (also used when the nested shape is present but empty, e.g.
        # documents nested one level deeper than expected).
        if not resume:
            resume = coerce_text(raw.get("tailored_resume", raw.get("resume")))
        if not cover:
            cover = coerce_text(raw.get("tailored_cover_letter", raw.get("cover_letter")))
        return cls(resume=resume, cover_letter=cover)


class ATSResult(BaseModel):
    """Canonical ATS-optimization output."""

    optimized_resume: str = ""
    optimized_cover_letter: str = ""
    ats_score: float | None = None

    @classmethod
    def from_raw(cls, raw: Any) -> "ATSResult":
        report = _first_dict(raw, "ats_report")
        raw_score = report.get("ats_score", report.get("score"))
        score = _parse_score(raw_score) if raw_score is not None else None
        # Only trust explicit optimized_* keys. Deliberately NOT falling back to a
        # bare "resume" key: when the ATS agent omits its output, that key may be the
        # ORIGINAL input résumé, which must never be promoted as the final document.
        return cls(
            optimized_resume=coerce_text(report.get("optimized_resume")),
            optimized_cover_letter=coerce_text(report.get("optimized_cover_letter")),
            ats_score=score,
        )


class AuditVerdict(BaseModel):
    """Canonical audit verdict for a single document."""

    approved: bool = False
    reason: str = ""

    @classmethod
    def from_raw(cls, raw: Any) -> "AuditVerdict":
        if not isinstance(raw, dict):
            return cls()
        # Accept nested (audit_report.*) or flat shapes.
        report = raw.get("audit_report") if isinstance(raw.get("audit_report"), dict) else raw
        approval = report.get("approval")

        # `approval` may be a dict, a bool, or a string; `approved` may be at either
        # level; some models express the verdict via `final_status`/`overall_status`.
        if isinstance(approval, dict):
            approved = coerce_bool(approval.get("approved"))
            reason = coerce_text(approval.get("reason", report.get("reason", "")))
        elif approval is not None:
            approved = coerce_bool(approval)
            reason = coerce_text(report.get("reason", ""))
        elif "approved" in report:
            approved = coerce_bool(report.get("approved"))
            reason = coerce_text(report.get("reason", ""))
        else:
            status = report.get("final_status", report.get("overall_status"))
            approved = coerce_bool(status) if status is not None else False
            reason = coerce_text(report.get("reason", status or ""))
        return cls(approved=approved, reason=reason)


class GapAnalysis(BaseModel):
    """Canonical view of the Gap Analyzer output, exposing the list of gaps."""

    gaps: list[dict] = Field(default_factory=list)

    @classmethod
    def from_raw(cls, raw: Any) -> "GapAnalysis":
        if not isinstance(raw, dict):
            return cls()
        if isinstance(raw.get("gaps"), list):
            return cls(gaps=[g for g in raw["gaps"] if isinstance(g, dict)])

        analysis = raw.get("gap_analysis")
        if isinstance(analysis, dict):
            gaps: list[dict] = []
            if isinstance(analysis.get("gaps"), list):
                gaps.extend(g for g in analysis["gaps"] if isinstance(g, dict))
            # Requirements classified as gap/blocker also count as gaps.
            for req in analysis.get("requirements", []) or []:
                if isinstance(req, dict) and req.get("classification") in ("gap", "blocker"):
                    gaps.append(req)
            return cls(gaps=gaps)
        return cls()


# Recommendation is derived deterministically from fit_score; the model supplies the
# score and rationale, Python owns the gate. Thresholds mirror the Executive
# Synthesizer's DECISION_THRESHOLDS and are the single source of truth for the CLI.
RECOMMENDATIONS = ("STRONG_PROCEED", "PROCEED", "PROCEED_WITH_CAUTION", "PASS")


class ExecutiveDecision(BaseModel):
    """Canonical executive decision: model-supplied score/rationale, Python-owned verdict."""

    recommendation: str = "PASS"
    fit_score: float = 0.0
    rationale: str = ""

    @classmethod
    def from_raw(cls, raw: Any) -> "ExecutiveDecision":
        decision = _first_dict(raw, "decision")
        fit_score = decision.get("fit_score", decision.get("score"))
        if fit_score is None and isinstance(raw, dict):
            fit_score = raw.get("fit_score", raw.get("score"))
        fit_score = _parse_score(fit_score)
        rationale = coerce_text(
            decision.get("rationale") or (raw.get("rationale") if isinstance(raw, dict) else "")
        )
        return cls(
            recommendation=recommendation_for_fit_score(fit_score),
            fit_score=fit_score,
            rationale=rationale,
        )


def _parse_score(value: Any) -> float:
    """Parse a fit score to a 0-100 float.

    Accepts a number or a '85%'/'85' string. Models sometimes report fit on a 0-1
    scale; a value in (0, 1] is treated as a fraction and scaled to 0-100 so the
    deterministic gate doesn't read an 85% fit as 0.85 -> PASS. Result is clamped.
    """
    score: float
    if isinstance(value, (int, float)):
        score = float(value)
    elif isinstance(value, str):
        try:
            score = float(value.strip().rstrip("%"))
        except ValueError:
            return 0.0
    else:
        return 0.0

    if 0.0 < score <= 1.0:
        score *= 100.0
    return max(0.0, min(100.0, score))


def recommendation_for_fit_score(fit_score: float) -> str:
    """Deterministically map a fit score (0-100) to a recommendation.

    This is the authoritative gate: the model no longer decides the verdict, only
    reports the score it is graded against.
    """
    if fit_score >= 80:
        return "STRONG_PROCEED"
    if fit_score >= 65:
        return "PROCEED"
    if fit_score >= 50:
        return "PROCEED_WITH_CAUTION"
    return "PASS"
