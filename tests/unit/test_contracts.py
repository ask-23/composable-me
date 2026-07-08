"""Unit tests for the typed stage contracts.

These lock the lenient-in / strict-out coercion that replaced the workflow's
defensive nested-dict probing.
"""

import pytest

from runtime.crewai.contracts import (
    ATSResult,
    AuditVerdict,
    ExecutiveDecision,
    GapAnalysis,
    TailoredDocuments,
    coerce_text,
    recommendation_for_fit_score,
)


class TestCoerceText:
    def test_plain_string(self):
        assert coerce_text("hello") == "hello"

    def test_dict_with_content(self):
        assert coerce_text({"content": "body"}) == "body"

    def test_dict_alternate_keys(self):
        assert coerce_text({"markdown": "md"}) == "md"

    def test_none_and_unknown(self):
        assert coerce_text(None) == ""
        assert coerce_text({"nope": 1}) == ""


class TestTailoredDocuments:
    def test_nested_output_content(self):
        raw = {"tailored_output": {"resume": {"content": "R"}, "cover_letter": {"content": "C"}}}
        docs = TailoredDocuments.from_raw(raw)
        assert docs.resume == "R"
        assert docs.cover_letter == "C"

    def test_flat_strings(self):
        raw = {"tailored_resume": "R", "tailored_cover_letter": "C"}
        docs = TailoredDocuments.from_raw(raw)
        assert (docs.resume, docs.cover_letter) == ("R", "C")

    def test_nested_output_plain_string(self):
        docs = TailoredDocuments.from_raw({"tailored_output": {"resume": "R"}})
        assert docs.resume == "R"
        assert docs.cover_letter == ""

    def test_garbage_is_empty(self):
        assert TailoredDocuments.from_raw("nope").resume == ""


class TestATSResult:
    def test_under_ats_report(self):
        raw = {"ats_report": {"optimized_resume": "R", "ats_score": "88"}}
        ats = ATSResult.from_raw(raw)
        assert ats.optimized_resume == "R"
        assert ats.ats_score == 88.0

    def test_top_level_fallback(self):
        ats = ATSResult.from_raw({"optimized_resume": "R"})
        assert ats.optimized_resume == "R"
        assert ats.ats_score is None


class TestAuditVerdict:
    def test_nested_report_approval(self):
        raw = {"audit_report": {"approval": {"approved": True, "reason": "ok"}}}
        v = AuditVerdict.from_raw(raw)
        assert v.approved is True
        assert v.reason == "ok"

    def test_flat_approval(self):
        assert AuditVerdict.from_raw({"approval": {"approved": False}}).approved is False

    def test_missing_defaults_to_not_approved(self):
        assert AuditVerdict.from_raw({}).approved is False
        assert AuditVerdict.from_raw(None).approved is False


class TestGapAnalysis:
    def test_flat_gaps(self):
        gaps = GapAnalysis.from_raw({"gaps": [{"skill": "k8s"}]}).gaps
        assert gaps == [{"skill": "k8s"}]

    def test_nested_and_classified_requirements(self):
        raw = {
            "gap_analysis": {
                "gaps": [{"skill": "a"}],
                "requirements": [
                    {"skill": "b", "classification": "gap"},
                    {"skill": "c", "classification": "blocker"},
                    {"skill": "d", "classification": "direct_match"},
                ],
            }
        }
        gaps = GapAnalysis.from_raw(raw).gaps
        skills = {g["skill"] for g in gaps}
        assert skills == {"a", "b", "c"}  # direct_match excluded


class TestRecommendation:
    @pytest.mark.parametrize(
        "score,expected",
        [
            (95, "STRONG_PROCEED"),
            (80, "STRONG_PROCEED"),
            (79, "PROCEED"),
            (65, "PROCEED"),
            (64, "PROCEED_WITH_CAUTION"),
            (50, "PROCEED_WITH_CAUTION"),
            (49, "PASS"),
            (0, "PASS"),
        ],
    )
    def test_thresholds(self, score, expected):
        assert recommendation_for_fit_score(score) == expected

    def test_executive_decision_derives_recommendation(self):
        # Model reports a verdict of PASS, but the score maps to PROCEED — Python wins.
        raw = {"decision": {"recommendation": "PASS", "fit_score": "72%", "rationale": "solid"}}
        decision = ExecutiveDecision.from_raw(raw)
        assert decision.fit_score == 72.0
        assert decision.recommendation == "PROCEED"
        assert decision.rationale == "solid"
