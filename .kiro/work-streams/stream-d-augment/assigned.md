# Stream D: Interrogator-Prepper

**Agent:** Augment  
**Status:** Not Started  
**Priority:** Medium (depends on Gap Analyzer)

## Your Mission

Build the Interrogator-Prepper agent that generates targeted interview questions to fill gaps in the candidate's experience and extracts truthful details.

## Requirements

See `.kiro/specs/composable-crew/requirements.md`:
- **Requirement 5:** Targeted interview questions

## What You're Building

### 1. Interrogator-Prepper Agent Prompt
Location: `agents/interrogator-prepper/prompt.md`

Refine the existing prompt to ensure it:
- Generates 8-12 targeted questions based on gaps
- Groups questions by theme (technical, leadership, outcomes, tools)
- Uses STAR+ format (Situation, Task, Actions, Results, Proof)
- Focuses on extracting truthful, specific details
- Handles "I don't know" gracefully

### 2. Interrogator-Prepper Implementation
Location: `runtime/crewai/agents/interrogator_prepper.py`

Implement:
- Question generation based on gap analysis
- Thematic grouping
- STAR+ formatting
- Interview note processing
- Verification of answers against truth laws

### 3. Question Generation Strategy

For each gap:
- Why is this gap important for the role?
- What transferable experience might the candidate have?
- How can we frame adjacent experience honestly?
- What proof/evidence should we ask for?

### 4. Interview Note Processing

When user provides answers:
- Store as verified source material
- Flag for downstream agents (Differentiator, Tailoring)
- Note which gaps were filled vs. remain unfilled

## Interface Contract

**Input:**
```yaml
job_description: string
resume: string
gaps: list[string]
gap_analysis: object
```

**Output:**
```yaml
agent: "interrogator_prepper"
timestamp: "ISO-8601"
confidence: float
questions:
  - id: string
    theme: "technical" | "leadership" | "outcomes" | "tools"
    question: string
    format: "STAR+"
    target_gap: string
    why_asking: string
interview_notes:
  - question_id: string
    answer: string
    verified: boolean
    source_material: boolean
```

See full interface spec: `.kiro/work-streams/stream-a-kiro/agent-interfaces.md`

## Dependencies

**You depend on:**
- Stream C (Gap Analyzer) - provides gaps to target
- Stream A (Integration framework)

**Who depends on you:**
- Stream E (Differentiator) - uses interview notes
- Stream E (Tailoring Agent) - uses interview notes as source material

## Testing

Create tests for:
1. Question generation for various gap types
2. STAR+ format compliance
3. Thematic grouping
4. Interview note validation
5. Handling unanswered questions

## Deliverables

1. `agents/interrogator-prepper/prompt.md` - Refined prompt
2. `runtime/crewai/agents/interrogator_prepper.py` - Implementation
3. `tests/test_interrogator_prepper.py` - Unit tests
4. `stream-d-augment/completed/DONE.md` - Summary

## Status Updates

Update `stream-d-augment/status.json` as you progress.

## Questions?

Put questions in `stream-d-augment/questions.md`.

## Getting Started

1. Read requirements document
2. Review interface specification
3. Look at existing `agents/interrogator-prepper/prompt.md`
4. Start building!
