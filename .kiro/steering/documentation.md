# Documentation Management

## Core Principles

**1. Every markdown file must have a clear, ongoing purpose. Temporary notes should be consolidated or deleted.**

**2. Avoid documentation proliferation. One comprehensive document is better than ten fragmented ones.**

**3. Don't create documentation for the sake of documentation. Create it when it solves a real problem.**

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

- **Multiple guides for the same topic**
  - Don't create: "Guide", "Quick Reference", "Summary", "Checklist", "Flow Diagram" for one feature
  - Create ONE comprehensive document instead
  - Use sections and headers for organization

- **Redundant documentation**
  - If information exists in one place, link to it - don't duplicate it
  - Update existing docs rather than creating new ones

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
7. **One document per topic** - Don't create multiple variations (guide, quick-ref, summary, checklist, diagram)
8. **Maximum 2-3 files per feature** - Protocol doc + helper scripts is enough
9. **Link, don't duplicate** - Reference existing docs rather than copying content
10. **Ask before creating ANY new markdown file** - User must approve first

## Documentation Budget

**Maximum files per feature/system:**
- 1 protocol/specification document (the "how it works")
- 1-2 helper scripts (if needed)
- Updates to existing docs (README, AGENTS.md, etc.)

**That's it. No more.**

If you think you need more files, you're probably:
- Over-documenting
- Duplicating information
- Creating variations of the same content
- Writing documentation instead of code

**Ask yourself:**
- Does this information already exist somewhere? → Update that file
- Can this be a section in an existing doc? → Add a section
- Is this temporary? → Don't commit it
- Will anyone actually read this? → Probably not

## Summary

**Goal:** Maintain a clean, focused set of documentation that serves ongoing needs.

**Rule of thumb:** If you wouldn't want to read it 6 months from now, don't commit it.

**Hard limit:** Maximum 3 new files per feature. Period.

