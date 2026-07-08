# Issues

Detailed issue specs intended to be handed directly to a developer agent (or filed into Linear). Each file is a single, scoped, ready-to-execute change with explicit acceptance criteria, testing requirements, and regression checks.

| # | Title | Status | Depends on |
|---|-------|--------|------------|
| [001](001-validated-output-example.md) | Add `examples/validated-output/` sanitized sample run | open | — |
| [002](002-run-sh-example-flag.md) | Add `./run.sh --example` CLI mode | open | 001 |

## Conventions

- One feature per file. No omnibus tickets.
- Filename: `NNN-kebab-case-summary.md`, numbers monotonically increasing.
- Each issue must include: Why, Goal, Acceptance Criteria, Testing Plan, Regression Checks, Out of Scope.
- Once an issue is shipped, leave the file in place as a historical record and mark `Status` here.
