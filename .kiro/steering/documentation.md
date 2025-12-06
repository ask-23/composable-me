# Documentation Management

## Core Principle

**Every markdown file must have a clear, ongoing purpose. Temporary notes should be consolidated or deleted.**

## Allowed Documentation Categories

### 1. Essential Project Documentation (Root Level)
- `README.md` - Project overview, setup, and usage
- `AGENTS.md` - AI agent rules and guidelines

**Rule:** Root-level MD files must document permanent features or essential project information.

### 2. Steering Rules (`.kiro/steering/`)
- Stable guidance for AI agents and development practices
- Rarely change once established

**Rule:** Don't create steering files for temporary guidance.

### 3. Spec Documents (`.kiro/specs/{feature-name}/`)
- `requirements.md` - Feature requirements
- `design.md` - Feature design (optional)
- `tasks.md` - Implementation tasks (optional)

**Rule:** Spec documents are temporary during development. Archive or delete after feature completion.

### 4. Planning Documents (`docs/plans/`)
- Implementation plans for major features
- Architecture decision records (ADRs)
- Migration guides

**Rule:** Archive after implementation is complete.

## Prohibited Documentation

### ❌ Never Commit These

- **Chat logs** (`*-chat-*.md`)
  - Working notes, not documentation
  - Delete after extracting useful information

- **Scratch notes** (`scratch.txt`, `*.tmp`)
  - Use for temporary thinking, then delete

- **Task summaries** (`TASK-*-SUMMARY.md`, `IMPLEMENTATION-SUMMARY.md`)
  - Consolidate into README or delete after completion

- **Validation reports** (unless documenting permanent testing strategy)
  - Test results are temporary

## Documentation Lifecycle

### During Development
1. Create spec documents in `.kiro/specs/{feature-name}/`
2. Take notes in temporary files (don't commit)
3. Update relevant permanent docs (README)

### After Feature Completion
1. Archive or delete spec documents
2. Update README with new feature documentation
3. Delete temporary notes, summaries, and chat logs
4. Consolidate useful information into permanent docs

## Decision Framework

Before creating a new MD file, ask:

1. **Is this temporary?** → Don't commit it
2. **Does this duplicate existing docs?** → Update existing docs instead
3. **Will this be useful in 6 months?** → If no, don't commit it
4. **Is this for a specific feature?** → Put it in `.kiro/specs/{feature-name}/`

## Agent Instructions

When working on this project:

1. **Never create summary MD files** after completing tasks
2. **Never commit chat logs** or scratch notes
3. **Update existing docs** instead of creating new ones
4. **Delete temporary files** before completing work
5. **Ask user** before creating new root-level MD files
6. **Consolidate** information into README when possible

## Summary

**Goal:** Maintain a clean, focused set of documentation that serves ongoing needs.

**Rule of thumb:** If you wouldn't want to read it 6 months from now, don't commit it.

