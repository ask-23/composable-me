# Work Streams - Quick Start Guide

## For Stream A (Kiro) - COMPLETE ✅

You're done with the foundation! Next steps:
1. Wait for Stream B (Commander) to start
2. Implement integration framework skeleton
3. Integrate agents as they complete

## For Stream B (Claude) - START HERE 🚀

**You're on the critical path!** Everyone is waiting for you.

### Quick Start
1. Read `stream-b-claude/assigned.md`
2. Read `.kiro/specs/composable-crew/requirements.md` (Requirements 2, 3, 4, 15, 17)
3. Read `stream-a-kiro/agent-interfaces.md` (Commander section)
4. Look at existing `agents/commander/prompt.md`
5. Start building!

### What You're Building
- Commander agent that orchestrates the workflow
- Greenlight handling
- Fit analysis logic
- Red flag detection
- Error handling

### Interface
```yaml
# Input
job_description: string
resume: string
research_data: object (optional)

# Output
agent: "commander"
action: "proceed" | "pass" | "discuss"
fit_analysis: { ... }
```

### When Done
1. Update `stream-b-claude/status.json` to "completed"
2. Put code in `stream-b-claude/completed/`
3. Create `stream-b-claude/completed/DONE.md`

## For Stream C (Codex) - START HERE 🚀

**You're also on the critical path!**

### Quick Start
1. Read `stream-c-codex/assigned.md`
2. Read `.kiro/specs/composable-crew/requirements.md` (Requirement 2)
3. Read `stream-a-kiro/agent-interfaces.md` (Gap Analyzer section)
4. Look at existing `agents/gap-analyzer/prompt.md`
5. Start building!

### What You're Building
- Gap Analyzer agent
- Requirement extraction
- Classification logic (direct/adjacent/gap/blocker)
- Fit scoring

### Interface
```yaml
# Input
job_description: string
resume: string

# Output
agent: "gap_analyzer"
requirements: [ ... ]
fit_score: float
gaps: [ ... ]
blockers: [ ... ]
```

## For Stream D (Augment) - WAIT

**Dependency:** Stream C must complete first

You'll build the Interrogator-Prepper agent. See `stream-d-augment/assigned.md` when ready.

## For Stream E (Assistant) - WAIT

**Dependency:** Stream D must complete first

You'll build Differentiator and Tailoring agents. See `stream-e-assistant/assigned.md` when ready.

## For Stream F (Assistant) - WAIT

**Dependency:** Stream E must complete first

You'll build ATS Optimizer and Auditor Suite. See `stream-f-assistant/assigned.md` when ready.

## Status Tracking

Check progress anytime:
```bash
cat .kiro/work-streams/stream-*/status.json
```

## Questions?

Create `stream-X/questions.md` and Stream A will answer in `stream-X/answers.md`.

## Critical Path

```
Stream B (Commander) ──┐
                       ├─► Stream A integrates
Stream C (Gap Analyzer)┘

Then:
Stream D (Interrogator) → Stream E (Tailoring) → Stream F (Auditor)
```

**Priority:** Streams B and C should start immediately!
