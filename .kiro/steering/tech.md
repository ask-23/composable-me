# Technical Stack

## Primary Implementation

**Runtime:** Python 3.x with CrewAI framework
**LLM Providers:** Together AI (recommended), OpenRouter, Chutes.ai
**Default Model:** `meta-llama/Llama-3.3-70B-Instruct-Turbo` (Together AI)

## Dependencies

Core libraries (see `requirements.txt`):
- `crewai>=0.86.0` - Multi-agent orchestration framework
- `crewai-tools>=0.17.0` - Agent tooling
- `litellm>=1.0.0` - Multi-provider LLM client
- `openai>=1.0.0` - API compatibility layer
- `langchain>=0.3.0` - LLM abstractions
- `python-dotenv>=1.0.0` - Environment configuration
- `rich>=13.0.0` - Console output formatting

## Alternative Runtimes

- **Go implementation** (in `runtime/go/`) - Native Go with LLM client (requires wiring)
- **Prompt-only mode** - Copy agent prompts from `agents/*/prompt.md` and use with Claude/GPT-4 directly

## Environment Configuration

**Choose one provider:**

Together AI (recommended):
```bash
export TOGETHER_API_KEY='tgp_v1_...'  # Get from together.ai
export TOGETHER_MODEL='meta-llama/Llama-3.3-70B-Instruct-Turbo'  # Optional override
```

OpenRouter (alternative):
```bash
export OPENROUTER_API_KEY='sk-or-...'  # Get from openrouter.ai/keys
export OPENROUTER_MODEL='anthropic/claude-sonnet-4.5'  # Optional override
```

Chutes.ai (alternative):
```bash
export CHUTES_API_KEY='your-key'  # Get from chutes.ai
export CHUTES_MODEL='deepseek-ai/DeepSeek-V3.1'  # Optional override
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

Full CLI (recommended):
```bash
./run.sh --jd path/to/job.md \
         --resume path/to/resume.md \
         --sources sources/ \
         --out output/
```

Direct CLI execution:
```bash
python -m runtime.crewai.cli \
    --jd examples/sample_jd.md \
    --resume examples/sample_resume.md \
    --sources examples/ \
    --out output/
```

Quick runner (simplified):
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
- Agents communicate via structured JSON, not prose
- Each agent has single responsibility (no generation + verification in same agent)
- Workflow orchestrator coordinates agents and enforces truth constraints

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

**Recommended (Together AI):**
- `meta-llama/Llama-3.3-70B-Instruct-Turbo` - Fast, good quality, cost-effective

**High Quality (OpenRouter):**
- `anthropic/claude-sonnet-4.5` - Latest, highest quality (more expensive)
- `anthropic/claude-3.5-sonnet` - Fast and reliable
- `anthropic/claude-3-opus` - Slower, highest quality

**Alternative (Chutes.ai):**
- `deepseek-ai/DeepSeek-V3.1` - Good performance, competitive pricing
