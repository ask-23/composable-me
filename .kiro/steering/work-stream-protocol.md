# Work Stream Protocol

## Quick Start

```bash
# 1. Start work
python3 .kiro/work-streams/update_status.py YOUR-STREAM in_progress --task "Reading requirements"

# 2. Update progress
python3 .kiro/work-streams/update_status.py YOUR-STREAM in_progress \
    --add-completed "Task done" --task "Current task" --progress "45%"

# 3. Complete
python3 .kiro/work-streams/update_status.py YOUR-STREAM completed
```

## Overview

When multiple AI agents work in parallel on different parts of a project, they must follow a standardized protocol for status tracking and communication. This enables automation, coordination, and visibility.

## Status Tracking Requirements

### CRITICAL: Always Update status.json

**Every agent MUST update their `status.json` file at these key moments:**

1. **When starting work** - Change status from `not_started` to `in_progress`
2. **When completing tasks** - Update `completed_tasks` array
3. **When hitting blockers** - Add to `blockers` array
4. **When finishing** - Change status to `completed`

### Status File Location

Each work stream has a status file at:
```
.kiro/work-streams/stream-{name}/status.json
```

### Status File Schema

```json
{
  "stream": "stream-b-codex",
  "agent": "Codex",
  "status": "not_started" | "in_progress" | "blocked" | "completed",
  "started_at": "ISO-8601 timestamp or null",
  "completed_at": "ISO-8601 timestamp or null",
  "last_updated": "ISO-8601 timestamp",
  "progress": "percentage string (e.g., '45%')",
  "current_task": "description of what you're working on now",
  "completed_tasks": [
    "Task 1 description",
    "Task 2 description"
  ],
  "next_tasks": [
    "Task 3 description",
    "Task 4 description"
  ],
  "blockers": [
    {
      "description": "What's blocking you",
      "severity": "critical" | "high" | "medium" | "low",
      "created_at": "ISO-8601 timestamp"
    }
  ],
  "notes": "Any additional context"
}
```

## When to Update Status

### 1. Starting Work

**Before you write any code**, update status to indicate you've started:

```json
{
  "status": "in_progress",
  "started_at": "2024-12-06T01:00:00Z",
  "last_updated": "2024-12-06T01:00:00Z",
  "progress": "5%",
  "current_task": "Reading requirements and interface specs",
  "notes": "Starting work on Stream B"
}
```

### 2. Completing Individual Tasks

**After each significant task**, update the completed tasks:

```json
{
  "status": "in_progress",
  "last_updated": "2024-12-06T02:30:00Z",
  "progress": "40%",
  "current_task": "Writing unit tests",
  "completed_tasks": [
    "Read requirements document",
    "Reviewed interface specifications",
    "Created agent class",
    "Wrote agent prompt"
  ],
  "next_tasks": [
    "Write unit tests",
    "Test YAML validation",
    "Create DONE.md summary"
  ]
}
```

### 3. Hitting Blockers

**If you encounter a blocker**, update immediately:

```json
{
  "status": "blocked",
  "last_updated": "2024-12-06T03:00:00Z",
  "progress": "60%",
  "current_task": "Waiting for clarification on interface",
  "blockers": [
    {
      "description": "Unclear how to handle missing company name in JD",
      "severity": "high",
      "created_at": "2024-12-06T03:00:00Z"
    }
  ],
  "notes": "Created questions.md with blocker details"
}
```

### 4. Completing Work

**When all work is done**, update to completed:

```json
{
  "status": "completed",
  "started_at": "2024-12-06T01:00:00Z",
  "completed_at": "2024-12-06T05:00:00Z",
  "last_updated": "2024-12-06T05:00:00Z",
  "progress": "100%",
  "current_task": "Work complete, ready for integration",
  "completed_tasks": [
    "Read requirements document",
    "Reviewed interface specifications",
    "Created agent class",
    "Wrote agent prompt",
    "Wrote unit tests",
    "All tests passing",
    "Created DONE.md summary",
    "Moved code to completed/ directory"
  ],
  "next_tasks": [],
  "blockers": [],
  "notes": "All deliverables complete. See completed/DONE.md for summary."
}
```

## Automation Hooks

### Status Change Triggers

The system monitors `status.json` files for changes and can trigger automated actions:

**When status changes to `in_progress`:**
- Notify coordinator (Stream A)
- Update project dashboard
- Start time tracking

**When status changes to `blocked`:**
- Alert coordinator immediately
- Create notification for blocker resolution
- Pause dependent streams if critical

**When status changes to `completed`:**
- Trigger integration workflow
- Notify coordinator for review
- Update dependency graph
- Notify dependent streams they can start

### Hook Configuration

Hooks are defined in `.kiro/hooks/` and can be triggered by:
- File changes (status.json updates)
- Status transitions
- Blocker creation
- Task completion

## Communication Protocol

### Questions

If you have questions:

1. Create `stream-X/questions.md`
2. Update status to `blocked` if question is blocking
3. Add blocker to `status.json`
4. Coordinator will answer in `stream-X/answers.md`
5. Update status back to `in_progress` when unblocked

### Completion Handoff

When you complete your work:

1. Update `status.json` to `completed`
2. Move all code to `stream-X/completed/` directory
3. Create `stream-X/completed/DONE.md` with summary
4. **Hook automatically triggers** - Kiro reviews your work immediately
5. You'll get feedback via `integration-issues.md` (if fixes needed) or integration confirmation (if approved)

## Best Practices

### Update Frequently

Update status at least:
- When starting work
- Every 1-2 hours during active work
- When completing major tasks
- When hitting blockers
- When finishing

### Be Specific

In `current_task`, be specific:
- ❌ "Working on agent"
- ✅ "Implementing YAML validation for Commander output"

### Track Progress Accurately

Update `progress` percentage based on:
- Tasks completed vs. total tasks
- Estimated time spent vs. total time
- Be realistic, not optimistic

### Document Blockers Clearly

When adding blockers:
- Describe the specific issue
- Explain why it's blocking you
- Indicate severity accurately
- Reference related files/docs

## Example Workflow

### Day 1: Starting Work

```json
{
  "status": "in_progress",
  "started_at": "2024-12-06T09:00:00Z",
  "last_updated": "2024-12-06T09:00:00Z",
  "progress": "5%",
  "current_task": "Reading requirements and design documents",
  "completed_tasks": [],
  "next_tasks": [
    "Read requirements.md",
    "Review agent-interfaces.md",
    "Create agent class skeleton",
    "Write agent prompt",
    "Implement execute() method",
    "Write unit tests"
  ]
}
```

### Day 1: Mid-Day Update

```json
{
  "status": "in_progress",
  "last_updated": "2024-12-06T14:30:00Z",
  "progress": "35%",
  "current_task": "Implementing execute() method",
  "completed_tasks": [
    "Read requirements.md",
    "Reviewed agent-interfaces.md",
    "Created agent class skeleton",
    "Wrote agent prompt"
  ],
  "next_tasks": [
    "Implement execute() method",
    "Write unit tests",
    "Test YAML validation"
  ]
}
```

### Day 2: Completion

```json
{
  "status": "completed",
  "started_at": "2024-12-06T09:00:00Z",
  "completed_at": "2024-12-07T16:00:00Z",
  "last_updated": "2024-12-07T16:00:00Z",
  "progress": "100%",
  "current_task": "Work complete",
  "completed_tasks": [
    "Read requirements.md",
    "Reviewed agent-interfaces.md",
    "Created agent class skeleton",
    "Wrote agent prompt",
    "Implemented execute() method",
    "Wrote unit tests",
    "All tests passing (15/15)",
    "Created DONE.md summary",
    "Moved code to completed/"
  ],
  "next_tasks": [],
  "blockers": [],
  "notes": "Commander agent complete. All tests passing. Ready for integration."
}
```

## Enforcement

### Required Updates

Agents MUST update status.json:
- ✅ When starting (status: in_progress)
- ✅ When completing (status: completed)
- ✅ When blocked (status: blocked)
- ✅ At least once per work session

### Consequences of Not Updating

If status is not updated:
- Coordinator cannot track progress
- Automation hooks won't trigger
- Dependent streams won't know when to start
- Integration delays occur
- Project visibility is lost

## Lessons Learned

### Common Mistakes to Avoid

1. **Not updating status.json at all**
   - Problem: Coordinator can't track progress, automation doesn't trigger
   - Solution: Update BEFORE starting, DURING work, and WHEN completing

2. **Putting code directly in main codebase**
   - Problem: No clean handoff, hard to review, can't rollback easily
   - Solution: Put all code in `stream-X/completed/` directory first

3. **Not creating DONE.md summary**
   - Problem: Coordinator doesn't know what you built or how to integrate
   - Solution: Always create `completed/DONE.md` with summary

4. **Test data missing base fields**
   - Problem: Tests fail because validation expects `agent`, `timestamp`, `confidence`
   - Solution: All YAML output must include base fields from BaseHydraAgent

5. **Using assertEqual for floats**
   - Problem: Floating point precision causes test failures
   - Solution: Use `assertAlmostEqual(value, expected, places=N)` for floats

## Summary

**Golden Rule:** Keep `status.json` current. It's the single source of truth for your work stream's progress.

**Update frequency:** At minimum when starting, when blocked, and when completing. Ideally every 1-2 hours during active work.

**Be specific:** Clear task descriptions and accurate progress percentages help everyone.

**Enable automation:** Proper status updates trigger hooks that coordinate the entire project.

**Handoff properly:** Code goes in `completed/` directory with `DONE.md` summary.
