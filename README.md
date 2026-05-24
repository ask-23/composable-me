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

Composable Me is a multi-agent system that creates tailored résumés and cover letters from your real experience—without fabricating skills, inflating metrics, or distorting timelines.

This repository is intentionally public: it demonstrates how I design, constrain, and execute complex AI systems end-to-end.

## Why This Matters

Composable Me is not a résumé generator wrapper. It is a small AI operating system for a high-trust workflow: taking messy source material, mapping it to a target role, generating tailored artifacts, and refusing unsupported claims.

It demonstrates the work I care about most:

- multi-agent workflow design
- human-in-the-loop governance
- claim verification and audit trails
- role-specific reasoning under constraints
- production-minded AI UX
- defensible automation instead of plausible fabrication

![Composable Me Web Interface](docs/assets/composable-me-screenshot.webp)

## Quick Start

```bash
git clone https://github.com/ask-23/composable-me.git
cd composable-me
cp .env.example .env   # Add your LLM API key
./run.sh --jd your_job_description.md --resume your_resume.md --out output/
```

That's it. Your tailored application materials will be in `output/`.

## Why This Exists

Most AI résumé tools optimize for _plausibility_. Composable Me optimizes for **truth under scrutiny**.

| Other Tools                        | Composable Me                          |
| ---------------------------------- | -------------------------------------- |
| Invent impressive-sounding metrics | Only use metrics you provide           |
| Stretch timelines to fill gaps     | Preserve your actual chronology        |
| Add trending keywords liberally    | Add keywords only where truthful       |
| Hope you don't get caught          | Generate an audit trail you can defend |

If the system can't justify a claim, it won't produce it. That's a feature.

## System Overview

```
┌─────────────┐
│ Your Inputs │  Job description + résumé + source documents
└──────┬──────┘
       ▼
┌──────────────────────────────────────────────────────┐
│                    HYDRA AGENTS                       │
├──────────────┬───────────────┬───────────────────────┤
│ Gap Analyzer │ Differentiator│ Tailoring Agent       │
│ Interrogator │ ATS Optimizer │ Auditor               │
└──────────────┴───────────────┴───────────────────────┘
       ▼
┌─────────────┐
│   Outputs   │  Résumé + cover letter + audit report
└─────────────┘
```

**Gap Analysis** — Maps job requirements to your experience, identifying matches and gaps

**Interview Prep** — Generates targeted questions to surface real details you may have forgotten

**Differentiation** — Identifies authentic value propositions that set you apart

**Tailoring** — Creates customized documents for the specific role

**ATS Optimization** — Improves keyword coverage _without_ changing meaning

**Audit & Verify** — Validates every claim against your source documents

## Output Files

| File                | What It Contains            |
| ------------------- | --------------------------- |
| `resume.md`         | Tailored résumé             |
| `cover_letter.md`   | Tailored cover letter       |
| `audit_report.yaml` | Claim-by-claim verification |
| `execution_log.txt` | Full agent trace            |

See [examples/validated-output/](examples/validated-output/) for a sanitized sample run with source inputs, generated application materials, rejected unsupported claims, and an execution log.

## Proof Points

- **Truth-constrained generation:** every résumé claim must trace back to supplied source material.
- **Agent separation:** gap analysis, differentiation, tailoring, ATS optimization, and audit are handled as separate responsibilities.
- **Audit output:** generated materials include a claim-by-claim verification report.
- **Human control:** the system stops where judgment is required instead of silently inventing.
- **Operational packaging:** CLI, web interface, examples, tests, and repeatable setup are included.

## Installation

### Requirements

- Python 3.11+ (3.13 recommended)
- One LLM API key (see below)
- Node.js 18+ (only for web interface)

### Option 1: Use the Script (Recommended)

```bash
./run.sh --help
```

The script handles virtual environments, dependencies, and execution.

### Option 2: Manual Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m runtime.crewai.cli --help
```

## Configuration

### LLM Providers

Set one of these in your `.env` file:

| Provider    | Link                  | Key Format                     |
| ----------- | --------------------- | ------------------------------ |
| Together AI | https://together.ai   | `TOGETHER_API_KEY=tgp_v1_...`  |
| Chutes      | https://chutes.ai     | `CHUTES_API_KEY=cpk_...`       |
| OpenRouter  | https://openrouter.ai | `OPENROUTER_API_KEY=sk-or-...` |

The CLI uses the first available key.

### Web Interface (Optional)

```bash
# Start PostgreSQL
docker run -d --name hydra-db \
  -e POSTGRES_USER=hydra \
  -e POSTGRES_PASSWORD=hydra \
  -e POSTGRES_DB=hydra \
  -p 5432:5432 postgres:16

# Set database URL
export HYDRA_DATABASE_URL=postgresql://hydra:hydra@localhost:5432/hydra

# Run migrations
PYTHONPATH="$(pwd)" python -m web.backend.db.migrate

# Start backend (terminal 1)
cd web/backend && ./run.sh

# Start frontend (terminal 2)
cd web/frontend && npm install && npm run dev
```

- Frontend: http://localhost:4321
- Backend: http://localhost:8000

## Project Structure

```
composable-me/
├── runtime/crewai/   # Core orchestration engine
├── agents/           # Agent prompt templates
├── web/              # Optional web UI (Astro + Litestar)
├── tests/            # pytest + Playwright tests
├── examples/         # Template inputs and validated sample output
└── run.sh            # CLI entry point
```

## Troubleshooting

<details>
<summary><strong>No API key found</strong></summary>

Set at least one provider key in `.env`. See [Configuration](#configuration).

</details>

<details>
<summary><strong>Document failed audit</strong></summary>

This means the system refused to approve unverifiable claims. This is expected behavior—review the `audit_report.yaml` to see what couldn't be verified, then provide additional source documents.

</details>

<details>
<summary><strong>Permission denied: run.sh</strong></summary>

```bash
chmod +x run.sh
```

</details>

<details>
<summary><strong>Database connection failed</strong></summary>

Ensure PostgreSQL is running and `HYDRA_DATABASE_URL` is set:

```bash
export HYDRA_DATABASE_URL=postgresql://hydra:hydra@localhost:5432/hydra
```

</details>

## Tech Stack

| Layer           | Technology         |
| --------------- | ------------------ |
| Agent Framework | CrewAI 0.86+       |
| LLM Abstraction | LiteLLM            |
| Runtime         | Python 3.11+       |
| Web Frontend    | Astro 5 + Svelte 5 |
| Web Backend     | Litestar           |
| Database        | PostgreSQL 16      |
| Observability   | OpenTelemetry      |
| Testing         | pytest, Playwright |

## Design Philosophy

This project is intentionally constrained. Those constraints _are_ the product.

1. **Truth is a hard boundary** — Every claim traces to source material
2. **Chronology is immutable** — Dates and sequences are never altered
3. **Failing is acceptable** — Silent degradation is a defect
4. **Human-in-the-loop** — Automation stops where judgment begins
5. **Legibility over cleverness** — The system is designed to be understood, audited, and reasoned about by humans, not just models.
6. **Opinionated defaults** — The system encodes strong opinions so users don’t have to invent policy under pressure.

## License

MIT — Use responsibly. This system exists to amplify real experience, not invent it.
