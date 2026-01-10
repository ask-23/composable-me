# Project Structure

## Directory Organization

```
composable-me/
├── agents/                    # Agent prompt definitions
│   ├── commander/            # Orchestrator agent
│   ├── gap-analyzer/         # Requirement mapping
│   ├── interrogator-prepper/ # Interview question generation
│   ├── differentiator/       # Unique positioning
│   ├── tailoring-agent/      # Document generation
│   ├── ats-optimizer/        # Keyword optimization
│   └── auditor-suite/        # Final verification
│
├── docs/                      # Core documentation (immutable)
│   ├── AGENTS.MD             # Truth laws (non-negotiable)
│   ├── AGENT_ROLES.MD        # Agent specifications
│   ├── ARCHITECTURE.MD       # System design
│   └── STYLE_GUIDE.MD        # Language rules
│
├── runtime/                   # Implementation options
│   ├── crewai/               # Python/CrewAI implementation
│   │   ├── __init__.py
│   │   ├── crew.py           # Full implementation
│   │   └── quick_crew.py     # Simplified runner
│   └── go/                   # Go implementation (alternative)
│       └── main.go
│
├── examples/                  # Sample inputs
│   ├── sample_jd.md          # Example job description
│   └── sample_resume.md      # Example resume
│
├── sources/                   # User source documents (add here)
├── output/                    # Generated applications
├── requirements.txt           # Python dependencies
└── run.sh                     # Quick start script
```

## Key File Conventions

### Agent Prompts (`agents/*/prompt.md`)
- Each agent has a dedicated directory
- `prompt.md` contains the agent's system prompt
- Prompts include version in frontmatter
- Prompts reference AGENTS.MD and STYLE_GUIDE.MD for rules

### Core Documentation (`docs/`)
These files define immutable rules and specifications:
- **AGENTS.MD** - Truth laws that cannot be overridden
- **AGENT_ROLES.MD** - Detailed agent specifications and communication protocol
- **ARCHITECTURE.MD** - System design, data flow, framework recommendations
- **STYLE_GUIDE.MD** - Anti-AI language patterns and human voice standards

### Runtime Implementations (`runtime/`)
- **crewai/** - Primary Python implementation using CrewAI framework
  - `crew.py` - Full implementation with prompt loading from files
  - `quick_crew.py` - Simplified single-file version with embedded prompts
- **go/** - Alternative Go implementation (requires LLM client wiring)

## Agent Structure

Each agent follows this pattern:
1. Single responsibility (no overlap)
2. Structured YAML input/output (not prose)
3. "Cannot" constraints defined
4. AGENTS.MD compliance required
5. Version tracking in prompt frontmatter

## Workflow Execution Order

Standard sequence:
```
1. COMMANDER receives JD
2. RESEARCH-AGENT gathers company intel (optional)
3. GAP-ANALYZER identifies matches/gaps
4. COMMANDER requests user greenlight
5. INTERROGATOR-PREPPER fills gaps via interview
6. DIFFERENTIATOR identifies unique angles
7. TAILORING-AGENT generates documents
8. ATS-OPTIMIZER ensures keyword coverage
9. AUDITOR-SUITE verifies everything
10. COMMANDER assembles final package
```

## Data Flow

```
Input → Commander → Research/Gap Analysis → User Greenlight
  → Interview → Differentiator → Tailoring → ATS → Audit → Output
```

## Adding New Agents

To add a new agent:
1. Create `agents/{agent-name}/` directory
2. Add `prompt.md` with agent specification
3. Define structured inputs/outputs
4. Include "Cannot" constraints
5. Update AGENT_ROLES.MD with specification
6. Wire into runtime implementation

## Configuration Files

- `.venv/` - Python virtual environment (gitignored)
- `requirements.txt` - Python dependencies
- `run.sh` - Bash script for quick execution
- Environment variables for API keys (not committed)

## Output Structure

Generated applications follow this structure:
```yaml
application_package:
  meta:
    company: "..."
    role: "..."
    created: "YYYY-MM-DD"
  documents:
    resume: "..."
    cover_letter: "..."
  supporting:
    fit_analysis: "..."
    differentiators: "..."
  audit:
    passed: true
    issues_resolved: [...]
```

## Important Conventions

1. **Truth sources** (in priority order):
   - User-confirmed statements in current session
   - Primary resume documents
   - User-supplied fragments with explicit confirmation

2. **Agent communication**: Always structured YAML, never free-form prose

3. **Error handling**: Max 2 retry loops for audit failures, then escalate to user

4. **Versioning**: All agent prompts include version in frontmatter

5. **State management**: Workflow state maintained across agent executions with full audit trail
