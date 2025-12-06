# Signals Directory

## Purpose

This directory provides a standardized location for agents and humans to post signals that trigger automated workflows. Signals are lightweight notification files that hooks monitor to coordinate work.

## Signal Types

### `/learnings/` - Knowledge Capture
Post-mortems, lessons learned, failures, mistakes, retrospectives, and insights worth preserving.

**When to use:** After resolving an issue, completing a difficult task, or discovering something non-obvious.

**Hook behavior:** Consolidates learnings into central project knowledge base.

**Example:**
```
.kiro/signals/learnings/2024-12-06-test-data-validation.md
```

### `/questions/` - Blocking Issues
Questions that need answers before work can proceed.

**When to use:** When blocked and need input from another agent or human.

**Hook behavior:** Alerts coordinator or relevant party for response.

**Example:**
```
.kiro/signals/questions/stream-b-interface-clarification.md
```

### `/alerts/` - Urgent Notifications
Critical issues requiring immediate attention.

**When to use:** Production issues, security concerns, critical blockers.

**Hook behavior:** Immediate notification to relevant parties.

**Example:**
```
.kiro/signals/alerts/critical-test-failure.md
```

### `/status/` - Milestone Updates
Significant progress updates or completions.

**When to use:** When completing major milestones or changing work stream status.

**Hook behavior:** Updates dashboards, notifies dependent streams.

**Example:**
```
.kiro/signals/status/stream-b-completed.md
```

## Signal Format

Signals should be markdown files with clear, actionable content:

```markdown
---
type: learning|question|alert|status
severity: low|medium|high|critical
created: YYYY-MM-DD HH:MM
author: agent-name|human-name
stream: stream-name (if applicable)
---

# Brief Title

## Context
What was happening?

## Issue/Question/Learning
What's the signal about?

## Action Needed (if applicable)
What should happen next?
```

## Lifecycle

1. **Create** - Agent or human creates signal file
2. **Trigger** - Hook detects file creation/edit
3. **Process** - Automated action executes (consolidate, notify, etc.)
4. **Archive** - Signal moved to archive or deleted after processing

## Cleanup

Signals can be:
- Deleted after processing (ephemeral notifications)
- Archived to `.kiro/signals/archive/` (audit trail)
- Marked processed with frontmatter flag (keep for reference)

## Benefits

- **Decoupled communication** - Agents don't need to know about each other
- **Auditable** - All signals are tracked in git
- **Extensible** - Easy to add new signal types
- **Reusable** - Pattern works across any project
- **Observable** - Anyone can check signals directory to see what's happening

## Future Extensions

- `/requests/` - Feature requests or task assignments
- `/approvals/` - Work ready for review/approval
- `/integrations/` - External system notifications
- `/metrics/` - Performance or progress metrics
