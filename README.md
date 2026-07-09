[![CI](https://github.com/ask-23/composable-me/actions/workflows/ci.yml/badge.svg)](https://github.com/ask-23/composable-me/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Node 20](https://img.shields.io/badge/node-20-green?logo=node.js&logoColor=white)](https://nodejs.org/)
[![Astro 5](https://img.shields.io/badge/astro-5-ff5d01?logo=astro&logoColor=white)](https://astro.build/)
[![Svelte 5](https://img.shields.io/badge/svelte-5-ff3e00?logo=svelte&logoColor=white)](https://svelte.dev/)
[![CrewAI](https://img.shields.io/badge/crewai-0.86%2B-purple)](https://www.crewai.com/)
[![Litestar](https://img.shields.io/badge/litestar-2.0%2B-yellow)](https://litestar.dev/)
[![License: MIT](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)

# Composable Me

**Generate job applications that tell the truth.**

Composable Me is a multi-agent AI application that turns your real experience into a
tailored résumé and cover letter — without fabricating skills, inflating metrics, or
bending timelines. Every claim is checked against your source documents, and every run
leaves an inspectable audit trail.

It is also a working example of a design point: **deterministic software owns the
workflow; model reasoning operates inside it.** Agents interpret, write, and judge;
Python owns routing, validation, the pass/fail gate, artifact naming, and the final
decision. That boundary is the interesting part, and this repo keeps it explicit.

![Composable Me Web Interface](docs/assets/composable-me-screenshot.webp)

## Quick Start

```bash
git clone https://github.com/ask-23/composable-me.git
cd composable-me
cp .env.example .env          # add at least one LLM API key
./run.sh --jd your_jd.md --resume your_resume.md --out output/
```

Your materials land in a run-scoped directory: `output/<run_id>/`.

## Why this exists

Most AI résumé tools optimize for _plausibility_. Composable Me optimizes for **truth
under scrutiny**.

| Other tools                        | Composable Me                       |
| ---------------------------------- | ----------------------------------- |
| Invent impressive-sounding metrics | Use only metrics you provide        |
| Stretch timelines to fill gaps     | Preserve your actual chronology     |
| Add trending keywords liberally    | Add keywords only where truthful    |
| Hope you don't get caught          | Emit an audit report you can defend |

If the system can't justify a claim, it won't ship it. The Auditor can reject output —
that's a feature, not a bug. Truth rules are defined once in
[`docs/AGENTS.MD`](docs/AGENTS.MD) and injected into every agent.

## How it works

A fixed, deterministic pipeline invokes seven agents in order and passes typed data
between them:

```
Inputs (JD + résumé + source docs)
      │
      ▼
Gap Analysis ─▶ Interrogation ─▶ Differentiation ─▶ Tailoring
                                                        │
                                                        ▼
                                          ATS Optimization ─▶ Audit (gate)
                                                        │
                                                        ▼
                                          Executive Synthesis
      │
      ▼
Artifacts: output/<run_id>/ {resume.md, cover_letter.md, audit_report.yaml,
                             execution_log.txt, run.json}
```

### Agent map

| Agent                     | Job                                                    | Decision type                                  |
| ------------------------- | ------------------------------------------------------ | ---------------------------------------------- |
| **Gap Analyzer**          | Classify each JD requirement vs. your experience       | model                                          |
| **Interrogator-Prepper**  | Ask questions to fill real gaps (human-in-the-loop)    | model + HITL                                   |
| **Differentiator**        | Identify authentic value propositions                  | model                                          |
| **Tailoring**             | Write the tailored résumé + cover letter               | model                                          |
| **ATS Optimizer**         | Keyword/format optimization for ATS                    | model                                          |
| **Auditor Suite**         | Verify truth, tone, ATS, compliance — the quality gate | model gate                                     |
| **Executive Synthesizer** | Strategic brief + fit score                            | model (score) → deterministic (recommendation) |

### Deterministic vs. model-driven

| Owned by software (deterministic)              | Owned by the model                   |
| ---------------------------------------------- | ------------------------------------ |
| Stage ordering and resume/skip logic           | Requirement classification           |
| Contract coercion at every stage boundary      | Question generation, differentiators |
| Audit pass/fail gate                           | Résumé / cover-letter prose          |
| `fit_score → recommendation` mapping           | The fit score itself, with rationale |
| Artifact naming, run-scoped writes, exit codes | ATS keywording, audit verdicts       |

The model proposes; the surrounding software disposes. See
[`docs/architecture.md`](docs/architecture.md) for the full control-flow map.

## Output artifacts

Each run writes to `output/<run_id>/`:

| File                | Contents                                                                                            |
| ------------------- | --------------------------------------------------------------------------------------------------- |
| `resume.md`         | Tailored résumé                                                                                     |
| `cover_letter.md`   | Tailored cover letter                                                                               |
| `audit_report.yaml` | Claim-by-claim verification and the final verdict                                                   |
| `execution_log.txt` | Timestamped agent trace                                                                             |
| `run.json`          | Run manifest: status, per-agent models, decision, artifact list — input _sizes_ only, never content |

Because runs are scoped by id, consecutive runs never clobber each other, and
`run.json` lets you understand a run without reading the whole log.

See [`examples/validated-output/`](examples/validated-output/) for a sanitized sample
run — source inputs, the generated résumé and cover letter, rejected unsupported
claims, and the execution log.

## Installation

Requires **Python 3.11+** (3.13 recommended) and one LLM API key. Node 18+ only for the
optional web UI.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m runtime.crewai.cli --help
```

`./run.sh` wraps venv creation, dependency install, and execution.

## Configuration

Set at least one provider key in `.env` (copy from `.env.example`). The CLI's fallback
LLM uses the first available in order **Together → Chutes → OpenRouter**. Agents are
additionally assigned per-task models (see
[`runtime/crewai/model_config.py`](runtime/crewai/model_config.py)); provide the
matching keys to use each agent's preferred model, or it degrades to a fallback.

| Provider     | Env var              | Used by                                          |
| ------------ | -------------------- | ------------------------------------------------ |
| Together AI  | `TOGETHER_API_KEY`   | ATS Optimizer, Interrogator, fallback            |
| Chutes (TEE) | `CHUTES_API_KEY`     | Gap Analyzer                                     |
| OpenRouter   | `OPENROUTER_API_KEY` | Anthropic-model fallback                         |
| Anthropic    | `ANTHROPIC_API_KEY`  | Differentiator, Tailoring, Executive Synthesizer |
| OpenAI       | `OPENAI_API_KEY`     | Auditor Suite                                    |

### Web interface (optional)

Astro + Svelte frontend over a Litestar API. See the frontend under `web/`. Requires
Postgres for job persistence:

```bash
export HYDRA_DATABASE_URL=postgresql://hydra:hydra@localhost:5432/hydra
./web/run.sh both      # backend :8000, frontend :4321
```

## Development

| Task                     | Command                                                           |
| ------------------------ | ----------------------------------------------------------------- |
| Install (with dev tools) | `pip install -r requirements-dev.txt`                             |
| Lint                     | `ruff check .`                                                    |
| Test (application core)  | `pytest tests/unit tests/integration --ignore=tests/unit/backend` |
| Frontend typecheck       | `cd web/frontend && npm ci && npm run check`                      |

CI runs lint + the core test suite and the frontend typecheck on every push
(`.github/workflows/ci.yml`). The backend integration tests require a live Postgres and
run separately.

## Extending it

- **A new agent**: add `agents/<name>/prompt.md`, a wrapper in
  `runtime/crewai/agents/`, a `model_config.py` entry, and wire it into
  `HydraWorkflow`. Give it a typed contract in `runtime/crewai/contracts.py` if
  downstream stages consume its output.
- **Prompt / voice changes**: see [`docs/content-and-prompts.md`](docs/content-and-prompts.md).
  Truth rules and the banned-phrase list live in `docs/AGENTS.MD` and
  `docs/STYLE_GUIDE.MD` and are injected automatically.

## Tech stack

| Layer           | Technology               |
| --------------- | ------------------------ |
| Agent framework | CrewAI + LiteLLM         |
| Runtime         | Python 3.11+             |
| Contracts       | Pydantic v2              |
| Web frontend    | Astro 5 + Svelte 5       |
| Web backend     | Litestar + PostgreSQL    |
| Observability   | OpenTelemetry            |
| Tests / lint    | pytest, ruff, Playwright |

## Design philosophy

This project is intentionally constrained. Those constraints _are_ the product.

1. **Truth is a hard boundary** — every claim traces to source material.
2. **Chronology is immutable** — dates and sequences are never altered.
3. **Failing is acceptable** — a rejected audit beats a silent fabrication.
4. **Software owns the frame** — agents reason inside deterministic rails.

## License

MIT — use responsibly. This system exists to amplify real experience, not invent it.
