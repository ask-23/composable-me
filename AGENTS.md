# AGENTS Guide for Kiro Projects

This file provides universal rules for AI agents working on Kiro-enabled projects.
Generic rules live here (rarely change). Project-specific rules live in `.kiro/steering/`.

## How This Works

1. Agent reads this file (AGENTS.md) for universal rules
2. Agent reads `.kiro/steering/*.md` for project-specific guidance
3. Steering docs extend/override generic rules where needed

## Universal Rules (Always Apply)

### Data Privacy
**See `.kiro/steering/data-privacy.md` for full details.**

- Never log PII (names, emails, IPs) to console or error messages
- Use placeholder data in examples: `user@example.com`, `Test User`
- Test with synthetic data only, never production data
- Redact PII from logs: `User ***@example.com submitted form`

### Deployment Safety
**See `.kiro/steering/deployment.md` for full details.**

- Always deploy to test/staging first
- Validate before production deployment
- Never skip the staging step for production apps
- Roll back immediately if issues detected

### Environment Separation
**See `.kiro/steering/environments.md` for full details.**

- Development: Local testing, break things freely
- Staging: Pre-production validation, synthetic data only
- Production: Real users only, never test here

### Documentation Hygiene
**See `.kiro/steering/documentation.md` for full details.**

- Never commit chat logs, scratch notes, or stale summaries
- Specs go in `.kiro/specs/{feature}/`, not root
- Consolidate into README when possible
- Delete temporary files before completing work

### Linear Sync
**See `.kiro/steering/linear-sync.md` for full details.**

- Sync specs to Linear via `scripts/sync-kiro-to-linear.js`
- Manual trigger only (no auto-sync on file save)
- One story per requirement, deduplication by title prefix

## Project-Specific (Customize These)

The following steering docs MUST be customized for each project:

| File | What to Add |
|------|-------------|
| `.kiro/steering/product.md` | Product overview, user flows, value proposition |
| `.kiro/steering/tech.md` | Tech stack, commands, dependencies |
| `.kiro/steering/structure.md` | Code organization, file layout |
| `.kiro/steering/scope-control.md` | MVP scope, what's in/out, guardrails |

## Work Stream Protocol (Parallel Development)
**See `.kiro/steering/work-stream-protocol.md` for full details.**

When working on parallel development streams:
- **ALWAYS update status.json** when starting, completing tasks, or finishing
- Update status to `in_progress` BEFORE writing any code
- Update `completed_tasks` array as you finish each task
- Update status to `completed` when all work is done
- Add blockers to status.json if you get stuck
- **Put completed work in stream-X/completed/ directory** for handoff
- **Create completed/DONE.md** summarizing what you built
- This enables automation hooks and coordination

**Critical:** If you don't update status.json, the coordinator won't know you've completed work!

## Anti-Patterns (Never Do)

- ❌ Create files without being asked
- ❌ Commit chat logs or scratch notes
- ❌ Deploy to production without staging validation
- ❌ Log or display PII in any form
- ❌ Run tests against production data
- ❌ Auto-sync to Linear without user action
- ❌ Create documentation summarizing completed work (unless asked)
- ❌ Forget to update status.json when starting or completing work

## When In Doubt

1. Ask the user before creating new files
2. Ask before deploying to any environment
3. Ask before syncing to Linear
4. Prefer editing existing files over creating new ones
5. Check `.kiro/steering/` for project-specific guidance

