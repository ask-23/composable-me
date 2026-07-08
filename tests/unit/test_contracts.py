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
    coerce_bool,
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

    def test_zero_to_one_scale_is_rescaled(self):
        # A 0-1 fraction must not be read as a ~0 percentage -> PASS.
        assert ExecutiveDecision.from_raw({"decision": {"fit_score": "0.85"}}).fit_score == 85.0
        assert ExecutiveDecision.from_raw({"decision": {"fit_score": 0.5}}).recommendation == (
            "PROCEED_WITH_CAUTION"
        )

    def test_score_clamped(self):
        assert ExecutiveDecision.from_raw({"decision": {"fit_score": 150}}).fit_score == 100.0


# --- Regression tests for adversarial-review findings ---------------------------


class TestCoerceBool:
    @pytest.mark.parametrize("value", [True, 1, "true", "yes", "approved", "PASS"])
    def test_truthy(self, value):
        assert coerce_bool(value) is True

    @pytest.mark.parametrize("value", [False, 0, "false", "no", "rejected", ""])
    def test_falsy(self, value):
        assert coerce_bool(value) is False

    def test_unknown_uses_default(self):
        assert coerce_bool("maybe") is False
        assert coerce_bool("maybe", default=True) is True


class TestAuditVerdictRobustness:
    def test_bool_approval_not_discarded(self):
        # approval given as a bare bool must be honored, not dropped.
        assert AuditVerdict.from_raw({"audit_report": {"approval": True}}).approved is True

    def test_string_rejection_not_inverted(self):
        # bool("false") is True in Python; a string rejection must stay rejected.
        assert AuditVerdict.from_raw({"approved": "false"}).approved is False
        assert AuditVerdict.from_raw({"approved": "no"}).approved is False

    def test_status_style_verdict(self):
        assert (
            AuditVerdict.from_raw({"audit_report": {"final_status": "APPROVED"}}).approved is True
        )
        assert AuditVerdict.from_raw({"final_status": "REJECTED"}).approved is False


class TestATSResultDoesNotPromoteOriginalResume:
    def test_bare_resume_key_is_ignored(self):
        # When ATS omits its report, a top-level `resume` (the ORIGINAL input) must
        # NOT become the optimized output.
        raw = {"optimization": {"done": True}, "resume": "ORIGINAL INPUT RESUME"}
        assert ATSResult.from_raw(raw).optimized_resume == ""

    def test_percent_score_parsed(self):
        assert ATSResult.from_raw({"ats_report": {"ats_score": "92%"}}).ats_score == 92.0


class TestTailoredDocumentsFallthrough:
    def test_empty_nested_falls_back_to_flat(self):
        raw = {"tailored_output": {"notes": "x"}, "tailored_resume": "R"}
        assert TailoredDocuments.from_raw(raw).resume == "R"

    def test_list_of_sections_joined(self):
        raw = {"tailored_output": {"resume": ["# Alex", "Engineer"]}}
        assert TailoredDocuments.from_raw(raw).resume == "# Alex\nEngineer"
