# Stream F: ATS Optimizer & Auditor Suite

**Agent:** Assistant  
**Status:** Not Started  
**Priority:** Low (depends on Tailoring Agent)

## Your Mission

Build two agents:
1. **ATS Optimizer** - Ensures documents pass Applicant Tracking Systems
2. **Auditor Suite** - Verifies truth, tone, ATS compliance, and rule adherence

## Requirements

See `.kiro/specs/composable-crew/requirements.md`:
- **Requirement 10:** ATS optimization
- **Requirement 11:** Comprehensive auditing
- **Requirement 12:** Automatic issue fixing

## What You're Building

### 1. ATS Optimizer Agent

**Location:** `agents/ats-optimizer/prompt.md` and `runtime/crewai/agents/ats_optimizer.py`

**Responsibilities:**
- Extract keywords from job description
- Verify keyword presence in resume
- Suggest truthful keyword insertions
- Check ATS-compatible formatting
- Calculate ATS score

**Interface:**
```yaml
# Input
job_description: string
tailored_resume: string
cover_letter: string

# Output
agent: "ats_optimizer"
timestamp: "ISO-8601"
confidence: float
keyword_analysis:
  required_keywords: list[string]
  present_keywords: list[string]
  missing_keywords: list[string]
  claimable_missing: list[string]
  unclaimable_missing: list[string]
suggestions: list[string]
ats_score: float
formatting_issues: list[string]
```

### 2. Auditor Suite Agent

**Location:** `agents/auditor-suite/prompt.md` and `runtime/crewai/agents/auditor_suite.py`

**Responsibilities:**
- **Truth Audit:** Verify all claims trace to source documents
- **Tone Audit:** Check for AI detection patterns
- **ATS Audit:** Verify keyword coverage
- **Compliance Audit:** Ensure AGENTS.MD rules followed

**Audit Categories:**
- **Blocking:** Must be fixed before approval
- **Warning:** Should be fixed but not blocking
- **Recommendation:** Nice to have improvements

**Interface:**
```yaml
# Input
job_description: string
resume: string
tailored_resume: string
cover_letter: string
interview_notes: object
all_agent_outputs: object

# Output
agent: "auditor_suite"
timestamp: "ISO-8601"
confidence: float
audits:
  truth_audit:
    passed: boolean
    issues: list[object]
    blocking_issues: list[object]
  tone_audit:
    passed: boolean
    ai_patterns_detected: list[string]
    issues: list[object]
  ats_audit:
    passed: boolean
    keyword_coverage: float
    issues: list[object]
  compliance_audit:
    passed: boolean
    rule_violations: list[object]
overall_passed: boolean
requires_revision: boolean
revision_instructions: list[string]
```

### 3. Retry Logic

When audit fails:
1. Categorize issues (blocking vs warning)
2. Generate specific revision instructions
3. Route back to responsible agent
4. Re-audit after revision
5. Max 2 retry loops, then escalate to user

## Dependencies

**You depend on:**
- Stream E (Tailoring Agent) - provides documents to audit
- Stream A (Integration framework)

**Who depends on you:**
- Stream B (Commander) - uses audit results for final approval

## Testing

Create tests for:
1. ATS: Keyword extraction and matching
2. ATS: Formatting validation
3. Auditor: Truth verification (catch fabrications)
4. Auditor: AI pattern detection
5. Auditor: Retry logic
6. Both: Issue categorization (blocking vs warning)

## Deliverables

1. `agents/ats-optimizer/prompt.md` - Refined prompt
2. `runtime/crewai/agents/ats_optimizer.py` - Implementation
3. `agents/auditor-suite/prompt.md` - Refined prompt
4. `runtime/crewai/agents/auditor_suite.py` - Implementation
5. `tests/test_ats_optimizer.py` - Unit tests
6. `tests/test_auditor_suite.py` - Unit tests
7. `stream-f-assistant/completed/DONE.md` - Summary

## Status Updates

Update `stream-f-assistant/status.json` as you progress.

## Questions?

Put questions in `stream-f-assistant/questions.md`.

## Getting Started

1. Read requirements document
2. Review interface specification
3. Read AGENTS.MD for truth laws
4. Look at existing agent prompts
5. Start building!
