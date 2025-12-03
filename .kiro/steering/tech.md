# Technical Stack

## Primary Implementation

**Runtime:** Python 3.x with CrewAI framework
**LLM Provider:** OpenRouter (supports multiple models)
**Default Model:** `anthropic/claude-3.5-sonnet`

## Dependencies

Core libraries (see `requirements.txt`):
- `crewai>=0.86.0` - Multi-agent orchestration framework
- `crewai-tools>=0.17.0` - Agent tooling
- `openai>=1.0.0` - API compatibility layer
- `langchain>=0.3.0` - LLM abstractions
- `pyyaml>=6.0` - Structured data handling
- `python-dotenv>=1.0.0` - Environment configuration
- `rich>=13.0.0` - Console output formatting

## Alternative Runtimes

- **Go implementation** (in `runtime/go/`) - Native Go with LLM client (requires wiring)
- **Prompt-only mode** - Copy agent prompts from `agents/*/prompt.md` and use with Claude/GPT-4 directly

## Environment Configuration

Required:
```bash
export OPENROUTER_API_KEY='sk-or-...'  # Get from openrouter.ai/keys
```

Optional:
```bash
export OPENROUTER_MODEL='anthropic/claude-3-5-sonnet'  # Override default model
```

## Common Commands

### Setup
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the System

Quick run with sample files:
```bash
./run.sh examples/sample_jd.md examples/sample_resume.md
```

With interview notes:
```bash
./run.sh path/to/jd.md path/to/resume.md path/to/notes.md
```

Direct Python execution:
```bash
python runtime/crewai/quick_crew.py \
    --jd examples/sample_jd.md \
    --resume examples/sample_resume.md \
    --out output.txt
```

### Development

Activate virtual environment:
```bash
source .venv/bin/activate
```

Update dependencies:
```bash
pip install -r requirements.txt --upgrade
```

## Architecture Patterns

### Agent Communication
- Agents communicate via structured YAML, not prose
- Each agent has single responsibility (no generation + verification in same agent)
- Commander orchestrates workflow and enforces truth constraints

### State Management
- Workflow state maintained across agent executions
- Audit trail logs all decisions and sources
- Context passed between agents via CrewAI task dependencies

### Error Handling
- Audit failures trigger retry loops (max 2 iterations)
- Blocking issues prevent document approval
- User escalation after max retries

## File Structure Conventions

```
agents/                    # Agent prompt definitions
  {agent-name}/
    prompt.md             # Agent system prompt

docs/                     # Core documentation (immutable rules)
  AGENTS.MD              # Truth laws (non-negotiable)
  AGENT_ROLES.MD         # Agent specifications
  ARCHITECTURE.MD        # System design
  STYLE_GUIDE.MD         # Language rules

runtime/                  # Implementation options
  crewai/               # Python/CrewAI implementation
  go/                   # Go implementation (alternative)

examples/                 # Sample inputs for testing
sources/                  # User source documents (resumes, etc.)
output/                   # Generated applications
```

## Testing Strategy

- Unit tests per agent (verify output structure)
- Integration tests for workflow (happy path + error cases)
- Prompt tests to validate agent quality
- All agent prompts versioned in frontmatter

## Model Recommendations

Works well with:
- `anthropic/claude-3.5-sonnet` (default, recommended - fast and high quality)
- `anthropic/claude-sonnet-4.5` (latest, most advanced if available)
- `anthropic/claude-3-opus` (slower, highest quality)
- `openai/gpt-4-turbo` (alternative provider)
