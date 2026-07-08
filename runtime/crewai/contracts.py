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


def coerce_text(value: Any) -> str:
    """Coerce a document-ish value to plain text.

    Agents variously return a string, or a dict like ``{"content": "..."}`` /
    ``{"text": "..."}`` / ``{"markdown": "..."}``. Anything else becomes "".
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("content", "text", "markdown", "body"):
            inner = value.get(key)
            if isinstance(inner, str) and inner.strip():
                return inner
        return ""
    return str(value)


def _first_dict(raw: Any, *keys: str) -> dict:
    """Return the first value among ``keys`` that is a dict, else ``{}``."""
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
        # Preferred nested shape: {"tailored_output": {"resume": {"content": ...}}}
        output = raw.get("tailored_output")
        if isinstance(output, dict):
            return cls(
                resume=coerce_text(output.get("resume")),
                cover_letter=coerce_text(output.get("cover_letter")),
            )
        # Flat fallbacks used by some models / older fixtures.
        resume = raw.get("tailored_resume", raw.get("resume"))
        cover = raw.get("tailored_cover_letter", raw.get("cover_letter"))
        return cls(resume=coerce_text(resume), cover_letter=coerce_text(cover))


class ATSResult(BaseModel):
    """Canonical ATS-optimization output."""

    optimized_resume: str = ""
    optimized_cover_letter: str = ""
    ats_score: float | None = None

    @classmethod
    def from_raw(cls, raw: Any) -> "ATSResult":
        report = _first_dict(raw, "ats_report")
        score = report.get("ats_score", report.get("score"))
        try:
            score = float(score) if score is not None else None
        except (TypeError, ValueError):
            score = None
        return cls(
            optimized_resume=coerce_text(report.get("optimized_resume", report.get("resume"))),
            optimized_cover_letter=coerce_text(
                report.get("optimized_cover_letter", report.get("cover_letter"))
            ),
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
        # Accept nested (audit_report.approval) or flat (approval) shapes.
        report = raw.get("audit_report") if isinstance(raw.get("audit_report"), dict) else raw
        approval = report.get("approval") if isinstance(report.get("approval"), dict) else {}
        approved = approval.get("approved", report.get("approved", False))
        reason = approval.get("reason", report.get("reason", ""))
        return cls(approved=bool(approved), reason=coerce_text(reason))


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
    """Parse a fit score that may arrive as a number or a '85%'/'85' string."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip().rstrip("%"))
        except ValueError:
            return 0.0
    return 0.0


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
