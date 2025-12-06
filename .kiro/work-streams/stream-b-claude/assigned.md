# Stream B: Commander Agent

**Agent:** Claude  
**Status:** Not Started  
**Priority:** High (blocking other streams)

## Your Mission

Build the Commander agent - the orchestrator that coordinates the entire workflow, enforces truth laws, and manages the greenlight process.

## Requirements

See `.kiro/specs/composable-crew/requirements.md`:
- **Requirement 2:** Fit analysis and recommendations
- **Requirement 3:** Red flag identification
- **Requirement 4:** Greenlight process
- **Requirement 15:** Workflow order enforcement
- **Requirement 17:** Error handling

## What You're Building

### 1. Commander Agent Prompt
Location: `agents/commander/prompt.md`

Refine the existing prompt to ensure it:
- Enforces workflow order
- Handles greenlight logic
- Identifies red flags and auto-reject criteria
- Makes PROCEED/PASS/DISCUSS recommendations
- Coordinates other agents

### 2. Commander Implementation
Location: `runtime/crewai/agents/commander.py`

Implement:
- Workflow orchestration logic
- Agent invocation in correct sequence
- Greenlight handling (wait for user approval)
- Error handling and retry logic
- Audit trail logging

### 3. Fit Analysis Logic
Calculate overall fit percentage based on Gap Analyzer output:
- Direct matches: 100% weight
- Adjacent experience: 70% weight
- Gaps: 0% weight
- Blockers: Auto-reject

### 4. Red Flag Detection
Check for:
- Contract-to-hire
- Below senior level
- No compensation listed
- Relocation required
- Company red flags from Research Agent

## Interface Contract

**Input:**
```yaml
job_description: string
resume: string
research_data: object (optional)
```

**Output:**
```yaml
agent: "commander"
timestamp: "ISO-8601"
confidence: float (0.0-1.0)
action: "proceed" | "pass" | "discuss"
fit_analysis:
  overall_fit_percentage: float
  recommendation: string
  reasoning: string
  red_flags: list[string]
  auto_reject_triggered: boolean
  auto_reject_reasons: list[string]
next_step: string
```

See full interface spec: `.kiro/work-streams/stream-a-kiro/agent-interfaces.md`

## Dependencies

**You depend on:**
- Stream C (Gap Analyzer) - you'll call this agent
- Stream A (Integration framework) - provides agent invocation utilities

**Who depends on you:**
- Everyone - you orchestrate the entire workflow

## Testing

Create tests for:
1. Auto-reject scenarios (contract-to-hire, etc.)
2. Fit percentage calculation
3. Greenlight handling
4. Error handling and retry
5. Workflow order enforcement

## Deliverables

1. `agents/commander/prompt.md` - Refined prompt
2. `runtime/crewai/agents/commander.py` - Implementation
3. `tests/test_commander.py` - Unit tests
4. `stream-b-claude/completed/DONE.md` - Summary of what you built

## Status Updates

Update `stream-b-claude/status.json` as you progress:
- When you start
- When you hit blockers
- When you complete tasks
- When you're done

## Questions?

Put questions in `stream-b-claude/questions.md` and I'll answer in `stream-b-claude/answers.md`.

## Getting Started

1. Read the requirements document
2. Review the interface specification
3. Look at existing `agents/commander/prompt.md`
4. Start building!
