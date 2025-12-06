# Stream E: Differentiator & Tailoring Agents

**Agent:** Assistant  
**Status:** Not Started  
**Priority:** Medium (depends on Interrogator-Prepper)

## Your Mission

Build two agents:
1. **Differentiator** - Identifies unique value propositions
2. **Tailoring Agent** - Generates tailored resume and cover letter

## Requirements

See `.kiro/specs/composable-crew/requirements.md`:
- **Requirement 6:** Unique differentiators
- **Requirement 7:** Tailored documents
- **Requirement 8:** Human-sounding content (anti-AI detection)
- **Requirement 9:** Truth law enforcement

## What You're Building

### 1. Differentiator Agent

**Location:** `agents/differentiator/prompt.md` and `runtime/crewai/agents/differentiator.py`

**Responsibilities:**
- Analyze candidate background for unique value propositions
- Identify rare skill combinations
- Find quantified outcomes
- Discover narrative threads
- Ensure relevance to job description

**Interface:**
```yaml
# Input
job_description: string
resume: string
interview_notes: object
gap_analysis: object

# Output
agent: "differentiator"
timestamp: "ISO-8601"
confidence: float
differentiators:
  - differentiator: string
    evidence: list[string]
    framing_suggestion: string
    relevance_to_jd: string
    uniqueness_score: float
positioning_angles: list[string]
```

### 2. Tailoring Agent

**Location:** `agents/tailoring-agent/prompt.md` and `runtime/crewai/agents/tailoring_agent.py`

**Responsibilities:**
- Generate tailored resume in Markdown
- Generate cover letter (250-400 words)
- Emphasize relevant experience
- Incorporate differentiators naturally
- Use only verified source material
- Apply anti-AI detection patterns (see STYLE_GUIDE.MD)

**Anti-AI Detection Rules:**
- Avoid: "proven track record", "passionate about", "leverage", "synergize"
- Vary sentence lengths (short, medium, long, conversational)
- Use active voice and specific numbers
- Include human elements (contractions, occasional asides)
- Use sentence fragments where natural

**Interface:**
```yaml
# Input
job_description: string
resume: string
interview_notes: object
differentiators: object
gap_analysis: object

# Output
agent: "tailoring_agent"
timestamp: "ISO-8601"
confidence: float
tailored_resume:
  format: "markdown"
  content: string
cover_letter:
  format: "markdown"
  content: string
  word_count: int
sources_used: list[string]
```

## Dependencies

**You depend on:**
- Stream D (Interrogator-Prepper) - provides interview notes
- Stream C (Gap Analyzer) - provides gap analysis
- Stream A (Integration framework)

**Who depends on you:**
- Stream F (ATS Optimizer) - optimizes your documents
- Stream F (Auditor Suite) - audits your documents

## Testing

Create tests for:
1. Differentiator: Unique value identification
2. Differentiator: Relevance scoring
3. Tailoring: Resume generation with truth compliance
4. Tailoring: Cover letter generation (word count, tone)
5. Tailoring: Anti-AI pattern compliance
6. Both: Source material traceability

## Deliverables

1. `agents/differentiator/prompt.md` - Refined prompt
2. `runtime/crewai/agents/differentiator.py` - Implementation
3. `agents/tailoring-agent/prompt.md` - Refined prompt
4. `runtime/crewai/agents/tailoring_agent.py` - Implementation
5. `tests/test_differentiator.py` - Unit tests
6. `tests/test_tailoring_agent.py` - Unit tests
7. `stream-e-assistant/completed/DONE.md` - Summary

## Status Updates

Update `stream-e-assistant/status.json` as you progress.

## Questions?

Put questions in `stream-e-assistant/questions.md`.

## Getting Started

1. Read requirements document
2. Review interface specification
3. Read STYLE_GUIDE.MD for anti-AI patterns
4. Look at existing agent prompts
5. Start building!
