# Project Overview: Composable Me Hydra

## Purpose
Composable Me Hydra is a truth-constrained, multi-agent system for generating high-quality job applications. It uses specialized AI agents to analyze job descriptions, map candidate experience, and generate tailored resumes and cover letters while ensuring all claims are verifiable.

## Key Principles
1. **Never lie** — All claims must be traced to source documents
2. **Sound human** — Anti-AI-detection patterns built in
3. **Tailor precisely** — Match JD subtext, not just keywords
4. **Find your edge** — Surface differentiators, not generic strengths

## Tech Stack

### Core Runtime (Python)
- **CrewAI** (>=0.86.0) — Multi-agent orchestration framework
- **LiteLLM** (>=1.80.0) — LLM provider abstraction
- **LangChain** (>=0.3.0) — LLM tooling
- **Python 3.13** — Runtime

### LLM Providers (by agent tier)
- **Anthropic** — Claude Sonnet 4 (differentiator, tailoring, executive_synthesizer)
- **Chutes.ai** — DeepSeek V3 (gap_analyzer), DeepSeek R1-TEE (auditor - TEE for privacy)
- **Together AI** — Llama 4 Maverick (ats_optimizer, interrogator_prepper, fallbacks)

### Web Interface
- **Frontend**: Astro 5 + Svelte 5 + TypeScript
- **Backend**: Litestar (Python async web framework)
- **Testing**: Playwright (E2E), pytest (unit)

### Development Tools
- pytest with coverage
- Husky pre-commit hooks
- Virtual environment (.venv)

## Agent Architecture

```
COMMANDER (Orchestrator)
    ├─→ RESEARCH-AGENT ─────→ Company intel
    ├─→ GAP-ANALYZER ────────→ Fit assessment
    ├─→ INTERROGATOR-PREPPER → Deep truth extraction
    ├─→ DIFFERENTIATOR ──────→ Unique positioning
    ├─→ TAILORING-AGENT ─────→ Document generation
    ├─→ ATS-OPTIMIZER ───────→ Keyword optimization
    └─→ AUDITOR-SUITE ───────→ Final verification
```

## Key Agents
| Agent | File | Purpose |
|-------|------|---------|
| Commander | `runtime/crewai/agents/commander.py` | Workflow orchestration |
| Gap Analyzer | `runtime/crewai/agents/gap_analyzer.py` | JD vs experience matching |
| Interrogator-Prepper | `runtime/crewai/agents/interrogator_prepper.py` | Extract missing details |
| Differentiator | `runtime/crewai/agents/differentiator.py` | Find unique positioning |
| Tailoring Agent | `runtime/crewai/agents/tailoring_agent.py` | Generate documents |
| ATS Optimizer | `runtime/crewai/agents/ats_optimizer.py` | Keyword optimization |
| Auditor | `runtime/crewai/agents/auditor.py` | Truth/tone verification |
| Executive Synthesizer | `runtime/crewai/agents/executive_synthesizer.py` | Final synthesis |
