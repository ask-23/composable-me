# Sync Kiro Specs to Linear

## Trigger
**Type:** Manual

This hook is triggered manually when you want to sync specs to Linear.

## Description
Parses all `.kiro/specs/*/requirements.md` files and creates corresponding Linear stories for any requirements that don't already have matching stories.

## When to Run
- After creating or updating requirements in `.kiro/specs/`
- Before starting implementation of a new feature
- When you want to ensure Linear reflects current specs

## How to Run

```bash
# Set your Linear API key
export LINEAR_API_KEY=lin_api_xxx

# Preview what would be created (safe, no changes)
npm run sync:linear:dry

# Create missing stories in Linear
npm run sync:linear
```

## Prerequisites
1. `.kiro/linear-project.json` configured with your Linear project/team IDs
2. `LINEAR_API_KEY` environment variable set
3. Requirements in `.kiro/specs/{feature}/requirements.md`

## What It Does
1. Reads configuration from `.kiro/linear-project.json`
2. Scans all `.kiro/specs/*/requirements.md` files
3. Parses requirements (pattern: `### Requirement N` + `**User Story:**`)
4. Checks Linear for existing stories with matching title prefix
5. Creates missing stories (skips existing ones)
6. Reports summary of created/skipped/errors

## Title Format
Stories are created with titles:
```
{Feature Name} – Req {N}: {Summary}
```

## Safety Features
- **Dry run mode:** Preview before creating
- **Deduplication:** Never creates duplicate stories
- **Create only:** Never modifies or deletes existing stories
- **Graceful errors:** Missing config shows helpful message, doesn't crash

