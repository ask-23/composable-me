# Stream C: Gap Analyzer

**Agent:** Codex  
**Status:** Not Started  
**Priority:** High (Commander depends on you)

## Your Mission

Build the Gap Analyzer agent that maps job requirements to candidate experience and classifies each as direct match, adjacent experience, gap, or blocker.

## Requirements

See `.kiro/specs/composable-crew/requirements.md`:
- **Requirement 2:** Job fit analysis (criteria 2-4)
- **Requirement 9:** Truth law enforcement

## What You're Building

### 1. Gap Analyzer Agent Prompt
Location: `agents/gap-analyzer/prompt.md`

Refine the existing prompt to ensure it:
- Extracts all requirements from JD (explicit and implicit)
- Maps each requirement to resume experience
- Classifies as: direct_match, adjacent_experience, gap, or blocker
- Provides evidence and source locations
- Never fabricates experience

### 2. Gap Analyzer Implementation
Location: `runtime/crewai/agents/gap_analyzer.py`

Implement:
- Requirement extraction from job descriptions
- Experience mapping logic
- Classification algorithm
- Fit scoring
- Evidence tracking (source document references)

### 3. Classification Logic

**Direct Match:** Candidate has done exactly this (same tech, same role, same domain)
**Adjacent Experience:** Transferable skills, similar but not identical
**Gap:** No relevant experience, but learnable
**Blocker:** Hard requirement with no path to claim (e.g., "must have PhD" when candidate doesn't)

### 4. Fit Scoring
Calculate per-requirement confidence scores and overall fit percentage.

## Interface Contract

**Input:**
```yaml
job_description: string
resume: string
research_data: object (optional)
```

**Output:**
```yaml
agent: "gap_analyzer"
timestamp: "ISO-8601"
confidence: float
requirements:
  - requirement: string
    classification: "direct_match" | "adjacent_experience" | "gap" | "blocker"
    evidence: string
    source_location: string
    confidence: float
fit_score: float
gaps: list[string]
blockers: list[string]
```

See full interface spec: `.kiro/work-streams/stream-a-kiro/agent-interfaces.md`

## Dependencies

**You depend on:**
- Stream A (Integration framework) - provides utilities

**Who depends on you:**
- Stream B (Commander) - uses your output for fit analysis
- Stream D (Interrogator-Prepper) - uses your gaps to generate questions

## Testing

Create tests for:
1. Requirement extraction from various JD formats
2. Classification accuracy (direct vs adjacent vs gap)
3. Blocker detection
4. Evidence tracking
5. Truth law compliance (no fabrication)

## Deliverables

1. `agents/gap-analyzer/prompt.md` - Refined prompt
2. `runtime/crewai/agents/gap_analyzer.py` - Implementation
3. `tests/test_gap_analyzer.py` - Unit tests
4. `stream-c-codex/completed/DONE.md` - Summary

## Status Updates

Update `stream-c-codex/status.json` as you progress.

## Questions?

Put questions in `stream-c-codex/questions.md`.

## Getting Started

1. Read requirements document
2. Review interface specification
3. Look at existing `agents/gap-analyzer/prompt.md`
4. Start building!
