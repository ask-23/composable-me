# Refactor Audit — Composable Me (Hydra)

**Date:** 2026-07-07
**Branch:** `refactor/application-optimization`
**Scope:** Production-minded refactor of the multi-agent application. Goal: leaner, clearer,
more deterministic where determinism matters, more auditable — without a framework rewrite and
without changing the truth-first product philosophy.

This document records the pre-refactor state, the decisions taken, and a running log of changes.

---

## 1. Current architecture

Composable Me is a multi-agent pipeline that turns a job description + résumé + source
documents into a tailored résumé, cover letter, and an audit report. Two front doors drive the
same engine:

- **CLI:** `run.sh` → `python -m runtime.crewai.cli` → `HydraWorkflow.execute()`.
- **Web:** `web/frontend` (Astro 5 + Svelte 5) → `web/backend` (Litestar + Postgres) →
  `web/backend/services/workflow_runner.py` → `HydraWorkflow.execute()`.

Engine (`runtime/crewai/`): a hand-rolled sequential orchestrator (`HydraWorkflow`) that invokes
seven agent wrappers, each of which wraps a single CrewAI `Agent`/`Task`/`Crew` and parses the
model's JSON output. Prompts live as markdown in `agents/<name>/prompt.md`.

## 2. Execution flow (live CLI path)

```
run.sh
  └─ python -m runtime.crewai.cli
       ├─ resolve --jd / --resume / --sources, read files
       ├─ get_llm_client(model)                 # single fallback LLM
       ├─ HydraWorkflow(llm, ...)               # eagerly builds 7 agents + per-agent LLMs
       └─ workflow.execute(context)
            ├─ 1. Gap Analysis        (model)  + human approval gate (web) / auto (cli)
            ├─ 2. Interrogation       (model)  + interview-answers gate
            ├─ 3. Differentiation     (model)
            ├─ 4. Tailoring           (model)  → tailored_output.{resume,cover_letter}.content
            ├─ 5. ATS Optimization    (model)
            ├─ 6. Audit (retry loop)  (model gate) → APPROVED / REJECTED / AUDIT_CRASHED
            └─ 7. Executive Synthesis (model)  → decision + fit_score
       └─ _write_output_files(...)              # resume.md, cover_letter.md, audit_report.yaml, execution_log.txt
```

## 3. Agent map (production roster — `HydraWorkflow`)

| Agent                 | Prompt                         | Role                                       | Decision type                    | Downstream                                    |
| --------------------- | ------------------------------ | ------------------------------------------ | -------------------------------- | --------------------------------------------- |
| Gap Analyzer          | `agents/gap-analyzer/`         | Classify each JD requirement vs experience | model                            | Interrogator, Differentiator, Tailoring, Exec |
| Interrogator-Prepper  | `agents/interrogator-prepper/` | Generate interview questions to fill gaps  | model + HITL                     | Differentiator, Tailoring                     |
| Differentiator        | `agents/differentiator/`       | Identify unique value propositions         | model                            | Tailoring, Exec                               |
| Tailoring             | `agents/tailoring-agent/`      | Generate tailored résumé + cover letter    | model                            | ATS, Audit, Exec                              |
| ATS Optimizer         | `agents/ats-optimizer/`        | Keyword/format optimization                | model                            | Audit                                         |
| Auditor Suite         | `agents/auditor-suite/`        | Truth/tone/ATS/compliance quality gate     | model gate                       | (gate)                                        |
| Executive Synthesizer | _(inline, no prompt.md)_       | Strategic brief + proceed/pass decision    | model→**now deterministic gate** | (final)                                       |

Not in production (removed in this refactor): **Commander** — existed only in the legacy
`crew.py` and its test; never wired into `HydraWorkflow`. Its deterministic scoring methods were
dead.

## 4. Deterministic vs model-driven boundary

**Deterministic (Python owns):** stage ordering; resume/skip logic; gap re-classification;
audit pass/fail gate reading `approval.approved`; retry counting; artifact naming + writes; CLI
exit codes. **Model-driven:** every stage's substance (classification, question generation,
document text, ATS keywords, audit verdict, fit rationale).

The boundary was blurred in three ways this refactor sharpens:

1. The executive **recommendation** was left to the model even though a threshold table
   (`DECISION_THRESHOLDS`) existed unused — now Python derives `recommendation` from `fit_score`.
2. The audit "retry loop" looked deterministic but its only mutation (`_apply_audit_fixes`) was a
   no-op — removed.
3. Stage-to-stage data was passed as raw dicts and re-probed defensively — replaced with typed
   contracts (`runtime/crewai/contracts.py`).

## 5. Main sources of complexity / fragility (pre-refactor)

- **Three orchestration lineages:** `hydra_workflow.py` (live), `crew.py` (legacy, test-only),
  `quick_crew.py` (dead). Duplicated LLM setup, agent defs, banners; divergent rosters.
- **No typed contracts:** defensive nested-dict / `isinstance` probing at
  `hydra_workflow.py:396-408, 494-503, 530-548, 580-592`. Hid a real bug: executive synthesis
  read `tailoring_result["tailored_resume"]` (never set) → always received empty documents.
- **Fake self-healing audit loop:** `_apply_audit_fixes` returned documents unchanged; the loop
  re-audited identical text, burning model calls.
- **Smeared success semantics:** `execute()` returned `success=True` for REJECTED/AUDIT_CRASHED;
  CLI re-derived status via `getattr`.
- **Three config surfaces:** orphaned `config.py`, `llm_client.py` (single fallback),
  `model_config.py` (per-agent) — different provider precedence; stale env docs; comment drift.
- **Prompt sprawl:** truth rules duplicated in code; forbidden-phrase list in 3 disagreeing
  places; ATS ruleset duplicated across two agents; prompts showed YAML while the parser expects
  JSON; candidate-specific persona leaked into "generic" prompts;
  `docs/AGENTS.MD` / `docs/STYLE_GUIDE.MD` referenced by the loader but absent → silent stub fallback.
- **Fragile JSON repair:** `base_agent._parse_json` did `str.replace("'", '"')`, corrupting
  apostrophes inside values.
- **Eager construction:** `HydraWorkflow.__init__` builds all agent LLMs, so it can't be
  constructed without an API key (breaks a graceful-handling test).
- **Test coupling:** root `tests/conftest.py` imports the web backend, which connects to Postgres
  at import time — coupling every test to a live DB.
- **Dead code:** whole `models.py`; unreachable code in `interrogator_prepper.py`; uncalled
  `_validate_context` methods; unused deps `langchain`/`langchain-openai`; orphaned Go
  (`runtime/go/`, `cli/`).

## 6. Validation commands discovered

- Python: `pip install -r requirements.txt`; `pytest` (config in `pytest.ini`, coverage on
  `runtime/crewai`). No lint/typecheck/CI existed pre-refactor.
- Frontend: `npm install`; `npm run build` (astro); `npm run check` (astro check);
  `npm run test:e2e` (Playwright).
- **Baseline (no key):** runtime suite 153 passed / 2 skipped / 1 failed (the failure is the
  eager-construction test; passes once any key is set → 154/2/0). Backend tests require Postgres.

## 7. Proposed refactor plan

See `/Users/alex/.claude/plans/…` (approved plan) — workstreams A–K: hygiene+CI, collapse to one
spine, typed contracts + bug fix, honest audit + status semantics, unified provider resolution,
prompts-as-source, run-scoped artifacts + manifest, test consolidation, documentation.

## 8. Decisions log (running)

- **Keep CrewAI.** A framework swap is out of scope; documented as a future consideration only.
- **Delete the Commander agent and the `crew.py`/`quick_crew.py` lineage.** Dead / contradictory
  with the production roster; git history preserves them.
- **Normalize at the deterministic boundary** (Python-side contract coercion) rather than relying
  on provider-specific structured-output modes.
- **Preserve the non-fatal-audit philosophy** but remove the pretend retry.

### Implemented (this PR)

- **Hygiene/CI:** fixed `.gitignore` (it blanket-ignored `docs/`, blocking
  documentation); dropped unused `langchain`/`langchain-openai`; added `ruff` +
  `pyproject.toml` + first CI (`.github/workflows/ci.yml`); committed the frontend
  lockfile for reproducible installs.
- **DB-at-import fix:** `web/backend/services/job_queue.py` no longer connects to
  Postgres at import (migrations already run on app startup). This decoupled the entire
  test suite from a live database.
- **Spine collapse:** deleted the two dead/legacy CrewAI lineages (`quick_crew.py`,
  `crew.py`) and the unused **Commander** agent; removed orphaned Go trees.
  `HydraWorkflow` is the single spine.
- **Typed contracts** (`contracts.py`) replaced the nested-dict probing; **fixed the
  executive-synthesis bug** (it read `tailored_resume`, never set, so it always got
  empty documents) and a **second latent bug** where the exec agent's inline prompt was
  assigned to an unused attribute and never reached the model.
- **Honest audit:** removed the no-op `_apply_audit_fixes` retry loop; audit runs once,
  is non-fatal, and retries only on transient errors.
- **Explicit status:** `RunStatus` drives CLI exit codes; deterministic
  `fit_score → recommendation` gate.
- **Provider config:** single `resolve_api_key`/`PROVIDER_ENV_KEYS`; removed orphaned
  `config.py`; fixed stale env list and comment drift.
- **Prompts as source:** created canonical `docs/AGENTS.MD` + `docs/STYLE_GUIDE.MD`
  (the injection path previously fell back to stubs); case-tolerant loader; de-duplicated
  the banned-phrase list; extracted the exec prompt into the prompt tree.
- **Observability:** run-scoped `output/<run_id>/` + a PII-free `run.json` manifest.
- **Tests:** consolidated duplicate suites into `tests/unit/`; added contract,
  artifacts, model-config, and CLI coverage. Runtime suite: **166 passed / 2 skipped**,
  **82%** line coverage on `runtime/crewai`, `ruff` clean.

### Deferred (documented, not done)

- Genericizing candidate-archetype examples and converting YAML-shaped output examples
  to JSON inside a few prompts (see `docs/content-and-prompts.md`). The JSON contract is
  already enforced at the task layer.
- Wiring the web backend's Postgres integration tests into CI (they need a live DB).
- Dropping CrewAI in favor of direct LLM calls (the framework is used as a thin shim by
  the live spine) — a larger, out-of-scope change.
