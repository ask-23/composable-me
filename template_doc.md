# Kiro Project Template

Foundation template for Kiro-enabled projects with Linear sync, AI agent steering, and development guardrails.

## Quick Start

```bash
# 1. Create new repo from this template (GitHub UI or CLI)
gh repo create my-project --template ask-23/kiro-project-template

# 2. Clone and install
git clone <your-new-repo>
cd my-project
npm install

# 3. Configure Linear (optional - do when ready)
cp .kiro/linear-project.json.example .kiro/linear-project.json
# Edit with your Linear project/team IDs

# 4. Customize project-specific steering docs
# Edit these files to describe YOUR project:
#   .kiro/steering/product.md
#   .kiro/steering/tech.md
#   .kiro/steering/structure.md
#   .kiro/steering/scope-control.md
```

## What's Included

### Universal Steering Docs (Ready to Use)
| File | Purpose |
|------|---------|
| `data-privacy.md` | PII protection rules, never log user data |
| `documentation.md` | Anti-clutter rules, no chat logs or scratch files |
| `deployment.md` | Test-first deployment patterns |
| `environments.md` | Dev/staging/production separation |
| `linear-sync.md` | How specs sync to Linear stories |

### Project-Specific Steering (Customize These)
| File | Purpose |
|------|---------|
| `product.md` | What is this product? Who uses it? |
| `tech.md` | What tech stack? What commands? |
| `structure.md` | How is code organized? |
| `scope-control.md` | What's in/out of MVP scope? |

### Tools
| Tool | Purpose |
|------|---------|
| `scripts/sync-kiro-to-linear.js` | Sync `.kiro/specs/` to Linear stories |
| `.husky/pre-commit` | Lint/format checks (graceful, non-blocking) |
| `.github/PULL_REQUEST_TEMPLATE.md` | Standard PR checklist |

## Syncing Specs to Linear

```bash
# Preview what would be created
LINEAR_API_KEY=lin_xxx node scripts/sync-kiro-to-linear.js --dry-run

# Create missing stories
LINEAR_API_KEY=lin_xxx node scripts/sync-kiro-to-linear.js

# Sync specific feature only
LINEAR_API_KEY=lin_xxx node scripts/sync-kiro-to-linear.js --feature my-feature
```

## Creating Feature Specs

```bash
mkdir .kiro/specs/my-feature
```

Create `.kiro/specs/my-feature/requirements.md`:
```markdown
# My Feature Requirements

### Requirement 1

**User Story:** As a user, I want feature X, so that I can do Y.

#### Acceptance Criteria
1. Criterion one
2. Criterion two
```

Then sync to Linear to create stories.

## Philosophy

- **Zero friction on startup** - Everything works on fresh clone
- **Graceful degradation** - Missing config = helpful message, not crash
- **Universal + specific** - Generic rules in AGENTS.md, project details in steering
- **Manual control** - No auto-syncing or autonomous actions

## License

MIT

