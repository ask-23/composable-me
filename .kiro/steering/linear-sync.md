# Linear Sync Configuration

## Overview

This project uses a script to sync Kiro specs (`.kiro/specs/*/requirements.md`) to Linear stories.

## How It Works

1. Parse all `requirements.md` files in `.kiro/specs/*/`
2. Extract requirements with pattern: `### Requirement N` + `**User Story:**`
3. Generate title: `{Feature Name} – Req {N}: {Summary}`
4. Check Linear for existing stories with same title prefix
5. Create missing stories, skip existing ones

## Configuration

### `.kiro/linear-project.json`

```json
{
  "projectName": "My Project",
  "projectId": "uuid-from-linear",
  "teamId": "uuid-from-linear",
  "featureMapping": {
    "my-feature": "My Feature Display Name"
  }
}
```

**Fields:**
- `projectName`: Human-readable project name (for logging)
- `projectId`: Linear project UUID (from project URL)
- `teamId`: Linear team UUID (from team settings)
- `featureMapping`: Maps spec directory names to display names

## Usage

```bash
# Set your Linear API key
export LINEAR_API_KEY=lin_api_xxx

# Preview what would be created
node scripts/sync-kiro-to-linear.js --dry-run

# Create missing stories
node scripts/sync-kiro-to-linear.js

# Sync specific feature only
node scripts/sync-kiro-to-linear.js --feature my-feature
```

## Title Pattern

Stories are created with titles matching:
```
{Feature Display Name} – Req {N}: {Summary from User Story}
```

Example:
```
User Authentication – Req 1: Users to log in with email and password
```

## Deduplication

The sync script prevents duplicates by matching title prefix:
```
{Feature Name} – Req {N}:
```

If any Linear issue starts with this prefix, the requirement is skipped.

This means:
- ✅ Running sync multiple times is safe
- ✅ Changing requirement summary text doesn't create duplicates
- ✅ Renumbering requirements may create new stories

## Requirements Format

In `.kiro/specs/{feature}/requirements.md`:

```markdown
# Feature Name Requirements

### Requirement 1

**User Story:** As a user, I want X, so that Y.

#### Acceptance Criteria
1. Criterion one
2. Criterion two

### Requirement 2

**User Story:** As an admin, I want A, so that B.

#### Acceptance Criteria
1. Criterion one
```

## Anti-Patterns

❌ **Don't** auto-trigger sync on file save (use manual trigger)
❌ **Don't** modify existing Linear issues (create-only)
❌ **Don't** delete Linear issues via sync
❌ **Don't** sync without `--dry-run` first on new features

## Finding Linear IDs

**Project ID:** Open project in Linear → URL contains `/project/{uuid}`
**Team ID:** Team Settings → scroll to ID section

