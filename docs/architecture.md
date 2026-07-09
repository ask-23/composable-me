# Architecture

Composable Me is a deterministic pipeline that orchestrates seven LLM agents to produce
truthful, audit-backed application materials. This document describes the spine, the
control boundaries, the data contracts, and how to extend the system.

## System purpose

Turn a job description + résumé + supporting source documents into a tailored résumé, a
cover letter, and an audit report — where every claim is verifiable against the sources.
The design thesis: **software owns the workflow; models operate inside it.**

## Execution flow

A run enters through one of two front doors, both driving the same engine:

- **CLI** — `run.sh` → `python -m runtime.crewai.cli` → `HydraWorkflow.execute()`
- **Web** — Astro frontend → Litestar API → `web/backend/services/workflow_runner.py`
  → `HydraWorkflow.execute()`

`HydraWorkflow.execute()` (`runtime/crewai/hydra_workflow.py`) runs a fixed sequence:

1. **Gap Analysis** — classify each JD requirement against the résumé. Human approval
   gate (auto in interactive CLI, explicit in web).
2. **Interrogation** — generate questions to fill real gaps; pause for answers (HITL).
3. **Differentiation** — identify authentic value propositions.
4. **Tailoring** — write the résumé and cover letter.
5. **ATS Optimization** — keyword/format pass.
6. **Audit** — verify the documents; produce a pass/fail verdict (non-fatal gate).
7. **Executive Synthesis** — strategic brief + fit score.

Each stage calls an agent through `_execute_with_fallback`, which retries once on a
secondary model if the primary errors.

## Control boundaries: deterministic vs. model-driven

The workflow is deliberately _not_ an autonomous agent loop. Control flow is hard-coded
Python; agents are bounded function calls.

**Deterministic (Python):** stage ordering; resume/skip logic; coercion of each agent's
raw output into a typed contract; the audit pass/fail gate; the `fit_score →
recommendation` mapping; artifact naming, run-scoped writes, and process exit codes.

**Model-driven (LLM):** requirement classification; question generation;
differentiators; résumé/cover-letter prose; ATS keywording; the audit verdict; and the
fit score with its rationale.

The one place the two most visibly meet is the executive decision: the model reports a
`fit_score`, and `contracts.recommendation_for_fit_score` deterministically maps it to
`STRONG_PROCEED / PROCEED / PROCEED_WITH_CAUTION / PASS`. The model never decides the
verdict word.

## Data flow and contracts

Agents return free-form JSON whose exact shape varies by model. Rather than probe nested
dictionaries at every call site, the workflow coerces each agent's output into a typed
contract at the boundary (`runtime/crewai/contracts.py`):

| Contract            | Produced from         | Consumed by                           |
| ------------------- | --------------------- | ------------------------------------- |
| `GapAnalysis`       | Gap Analyzer          | Interrogation                         |
| `TailoredDocuments` | Tailoring             | ATS, Audit, Executive Synthesis       |
| `ATSResult`         | ATS Optimizer         | Audit                                 |
| `AuditVerdict`      | Auditor               | the audit gate                        |
| `ExecutiveDecision` | Executive Synthesizer | the deterministic recommendation gate |

Each contract's `from_raw()` is **lenient on input** (accepts the several shapes models
emit) and **strict on output** (downstream code sees a stable, typed object). This is
the single tested place where shape variance is absorbed.

## Run state

CLI runs are single-process and in-memory: `HydraWorkflow` holds `current_state`,
`execution_log`, and `intermediate_results` (the inter-stage message bus).
Resumability for the web flow works by passing prior `intermediate_results` and
`WorkflowPaused` back into a new `execute()` call with the awaited human input.

## Artifact lifecycle

`runtime/crewai/artifacts.py` centralizes artifact filenames and writes each run into
`output/<run_id>/`. Every run emits a `run.json` manifest (status, per-agent models,
executive decision, artifact list, input sizes) — PII-free by construction: it records
input _sizes_, never input _content_. Run scoping means consecutive runs never overwrite
one another.

## Failure modes

Failure is classified explicitly via `RunStatus`:

| Status                          | Meaning                                | Exit code |
| ------------------------------- | -------------------------------------- | --------- |
| `COMPLETED`                     | documents produced, audit passed       | 0         |
| `COMPLETED_WITH_AUDIT_CONCERNS` | produced, audit rejected (non-fatal)   | 1         |
| `AUDIT_ERROR`                   | produced, audit stage errored          | 1         |
| `PAUSED`                        | awaiting human input                   | 1         |
| `FAILED`                        | a pre-audit stage failed; no documents | 2         |

The audit is a **verification gate, not a correction loop**: it judges the documents and
records the verdict. There is no automatic re-write, so it runs once per document rather
than re-auditing unchanged text. Audit failure is non-fatal — the documents and all
prior work are preserved and returned, clearly flagged.

## Extending the system

To add an agent:

1. Write `agents/<name>/prompt.md` (role, task, constraints, JSON output schema).
2. Add a wrapper in `runtime/crewai/agents/` subclassing `BaseHydraAgent`.
3. Register its model in `runtime/crewai/model_config.py` (`AGENT_MODELS`).
4. Wire it into `HydraWorkflow` at the right stage.
5. If downstream stages consume its output, give it a typed contract in
   `runtime/crewai/contracts.py` instead of reading raw dicts.

Truth rules (`docs/AGENTS.MD`) and the style guide (`docs/STYLE_GUIDE.MD`) are injected
into agent prompts automatically — do not duplicate them in individual prompts.
