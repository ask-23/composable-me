# Codebase Structure

```
composable-crew/
├── runtime/                    # Core Python runtime
│   ├── crewai/                # CrewAI-based implementation
│   │   ├── agents/            # Individual agent implementations
│   │   │   ├── ats_optimizer.py
│   │   │   ├── auditor.py
│   │   │   ├── commander.py
│   │   │   ├── differentiator.py
│   │   │   ├── executive_synthesizer.py
│   │   │   ├── gap_analyzer.py
│   │   │   ├── interrogator_prepper.py
│   │   │   └── tailoring_agent.py
│   │   ├── base_agent.py      # BaseHydraAgent base class
│   │   ├── cli.py             # Command-line interface
│   │   ├── config.py          # Configuration management
│   │   ├── crew.py            # CrewAI crew setup
│   │   ├── hydra_workflow.py  # Main workflow orchestration
│   │   ├── llm_client.py      # LLM provider abstraction
│   │   ├── model_config.py    # Model configuration
│   │   ├── models.py          # Data models (dataclasses)
│   │   └── quick_crew.py      # Simplified runner
│   └── go/                    # Go orchestrator (alternative)
│       └── main.go
│
├── agents/                    # Agent prompt templates
│   ├── commander/
│   ├── interrogator-prepper/
│   ├── gap-analyzer/
│   ├── differentiator/
│   ├── tailoring-agent/
│   ├── ats-optimizer/
│   └── auditor-suite/
│
├── web/                       # Web interface
│   ├── frontend/              # Astro + Svelte frontend
│   │   ├── src/
│   │   │   ├── pages/        # Astro pages
│   │   │   └── components/   # Svelte components
│   │   ├── tests/            # Playwright E2E tests
│   │   └── package.json
│   └── backend/              # Litestar Python backend
│       ├── app.py            # Main application
│       ├── models.py         # API models
│       ├── routes/           # API routes
│       └── services/         # Business logic
│
├── tests/                     # Python tests
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   ├── conftest.py           # pytest fixtures
│   └── test_*.py             # Test files
│
├── docs/                      # Documentation
│   ├── AGENTS.MD             # Truth rules
│   ├── AGENT_ROLES.MD        # Agent specifications
│   ├── ARCHITECTURE.MD       # System design
│   └── STYLE_GUIDE.MD        # Anti-AI language patterns
│
├── examples/                  # Sample input files
├── sources/                   # User resume/background files
├── output/                    # Generated output
│
├── .claude/                   # Claude Code configuration
├── .husky/                    # Git hooks
├── .serena/                   # Serena configuration
│
├── run.sh                     # Main entry script
├── requirements.txt           # Python dependencies
├── pytest.ini                # pytest configuration
└── package.json              # Node.js dependencies (Husky)
```

## Key Entry Points

| Entry Point | Location | Purpose |
|-------------|----------|---------|
| CLI | `./run.sh` or `python -m runtime.crewai.cli` | Main workflow |
| Quick Run | `runtime/crewai/quick_crew.py` | Simplified workflow |
| Web Backend | `web/backend/app.py` | API server |
| Web Frontend | `web/frontend/` | User interface |

## Important Files

| File | Purpose |
|------|---------|
| `runtime/crewai/hydra_workflow.py` | Main `HydraWorkflow` class |
| `runtime/crewai/base_agent.py` | `BaseHydraAgent` base class |
| `runtime/crewai/models.py` | All data models |
| `runtime/crewai/llm_client.py` | LLM provider abstraction |
| `docs/AGENTS.MD` | Truth rules (immutable) |
| `docs/STYLE_GUIDE.MD` | Anti-AI patterns |
