# Composable Crew - Work Streams

This directory coordinates parallel development across multiple AI coding assistants.

## Overview

The Composable Crew project is being built by multiple agents working in parallel streams. Each stream has clear responsibilities, interfaces, and deliverables.

## Active Streams

| Stream | Agent | Role | Status | Priority |
|--------|-------|------|--------|----------|
| **Stream A** | Kiro | Orchestration & Integration | In Progress | Critical |
| **Stream B** | Claude | Commander Agent | Not Started | High |
| **Stream C** | Codex | Gap Analyzer | Not Started | High |
| **Stream D** | Augment | Interrogator-Prepper | Not Started | Medium |
| **Stream E** | Assistant | Differentiator & Tailoring | Not Started | Medium |
| **Stream F** | Assistant | ATS Optimizer & Auditor | Not Started | Low |

## How It Works

### 1. Assignments
See `assignments.json` for the master list of who's doing what.

### 2. Stream Directories
Each stream has its own directory:
- `assigned.md` - What you're building
- `status.json` - Current progress
- `questions.md` - Questions for Stream A
- `answers.md` - Answers from Stream A
- `completed/` - Finished work

### 3. Coordination
- Stream A (Kiro) coordinates everything
- Other streams work independently
- Communication via files (questions/answers)
- Integration happens in Stream A

### 4. Interfaces
All agents communicate via structured YAML. See `stream-a-kiro/agent-interfaces.md` for complete specifications.

### 5. Status Protocol
**CRITICAL:** All agents MUST update their `status.json` file when:
- Starting work (change to `in_progress`)
- Completing tasks (update `completed_tasks`)
- Hitting blockers (change to `blocked`)
- Finishing work (change to `completed`)

See `.kiro/steering/work-stream-protocol.md` for complete protocol.

## Getting Started

### If you're Stream A (Kiro)
1. ✅ Set up coordination system (DONE)
2. ✅ Define interfaces (DONE)
3. ✅ Create assignments (DONE)
4. ⏳ Implement integration framework
5. ⏳ Wait for other streams to complete
6. ⏳ Integrate and test

### If you're Stream B-F
1. Read your `assigned.md` file
2. Review `stream-a-kiro/agent-interfaces.md`
3. Read `.kiro/specs/composable-crew/requirements.md`
4. Start building!
5. Update your `status.json` as you progress
6. Put completed work in your `completed/` directory

## Dependencies

```
Stream A (Orchestration)
    │
    ├─► Stream B (Commander) ──┐
    │                          │
    ├─► Stream C (Gap Analyzer)├─► Stream D (Interrogator)
    │                          │
    │                          ├─► Stream E (Differentiator & Tailoring)
    │                          │
    │                          └─► Stream F (ATS & Auditor)
    │
    └─► Integration & Testing
```

**Critical Path:**
1. Stream B (Commander) - blocks everything
2. Stream C (Gap Analyzer) - blocks D, E, F
3. Stream D (Interrogator) - blocks E
4. Stream E (Tailoring) - blocks F
5. Stream F (Auditor) - final validation

## Communication

### Questions
If you have questions, create `stream-X/questions.md`:

```markdown
# Questions for Stream A

## Question 1: Interface clarification
How should I handle missing fields in the input?

## Question 2: Error handling
Should I retry on LLM timeout or escalate immediately?
```

Stream A will answer in `stream-X/answers.md`.

### Status Updates
Update your `status.json` regularly:
- When you start
- When you hit blockers
- When you complete tasks
- When you're done

### Completion
When done:
1. Update `status.json` to "completed"
2. Put all code in `completed/` directory
3. Create `completed/DONE.md` summarizing what you built
4. Notify Stream A

## Integration Process

1. Stream completes work
2. Stream A reviews code
3. Stream A integrates into main codebase
4. Stream A runs tests
5. If issues found, Stream A creates `stream-X/integration-issues.md`
6. Stream fixes issues
7. Repeat until clean integration

## Testing

Each stream should:
- Write unit tests for their components
- Test against the interface specification
- Validate YAML output format
- Test error handling

Stream A will:
- Run integration tests
- Test full workflow end-to-end
- Validate agent interactions

## Current Status

**Stream A:** Foundation complete, waiting for other streams to start

**Next Steps:**
1. Stream B (Commander) should start immediately - it's blocking everything
2. Stream C (Gap Analyzer) should start immediately - it's on the critical path
3. Other streams can start once their dependencies are clear

## Coordinator Monitoring

Check all stream statuses:
```bash
for stream in .kiro/work-streams/stream-*/status.json; do
    name=$(basename $(dirname $stream))
    status=$(cat $stream | jq -r '.status')
    progress=$(cat $stream | jq -r '.progress')
    echo "$name: $status ($progress)"
done
```

## Questions?

Contact Stream A (Kiro) by creating a `questions.md` file in your stream directory.
