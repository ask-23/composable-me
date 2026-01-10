# Kiro Hooks

Hooks automate workflows by triggering actions when specific events occur.

## Active Hooks

### stream-completion-review.json

**Trigger:** When `DONE.md` is created in any stream's `completed/` directory

**Action:** Automatically invokes Kiro to review the completed work

**What Kiro does:**
1. Reads the DONE.md summary
2. Checks all deliverables exist
3. Runs the agent's tests
4. Validates code quality
5. Checks YAML output format
6. Either integrates the code OR creates integration-issues.md with fixes needed

**Why this matters:**
- No manual coordination needed
- Immediate feedback to agents
- Consistent review process
- Automatic integration when work is good

### work-stream-status-monitor.json

**Trigger:** When any `status.json` file changes

**Action:** Monitors status changes and triggers notifications

**What it does:**
- Notifies when agents start work
- Alerts when agents get blocked
- Triggers integration workflow on completion
- Checks dependency graph
- Notifies dependent streams

## How Hooks Work

1. **File watcher** monitors specified patterns
2. **Event detected** (file created/modified)
3. **Hook triggered** with context variables
4. **Action executed** (send message to agent, run command, etc.)
5. **Notification sent** about outcome

## Hook Configuration

Hooks are JSON files with this structure:

```json
{
  "name": "Hook Name",
  "trigger": {
    "type": "file_created" | "file_modified" | "file_deleted",
    "pattern": "glob pattern"
  },
  "action": {
    "type": "agent_message" | "command" | "notification",
    "details": "..."
  }
}
```

## Testing Hooks

To test if a hook would trigger:

```bash
# Create a test DONE.md file
mkdir -p .kiro/work-streams/stream-test/completed
echo "# Test" > .kiro/work-streams/stream-test/completed/DONE.md

# Hook should trigger and send message to Kiro
```

## Disabling Hooks

Set `"enabled": false` in the hook JSON file.
