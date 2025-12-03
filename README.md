# Composable Me — Multi-Agent Job Search Hydra

A truth-constrained, multi-agent system for generating high-quality job applications.

## Quick Start (CrewAI)

```bash
# 1. Clone/download the repo
cd composable-me

# 2. Set your OpenRouter API key
export OPENROUTER_API_KEY='sk-or-...'

# 3. Run with sample files
./run.sh examples/sample_jd.md examples/sample_resume.md

# Or with interview notes
./run.sh path/to/jd.md path/to/resume.md path/to/notes.md
```

The crew will:
1. **Commander** — Analyze fit, extract requirements
2. **Gap Analyzer** — Map JD requirements to your experience
3. **Interrogator-Prepper** — Generate interview questions for gaps
4. **Differentiator** — Find your unique positioning
5. **Tailoring Agent** — Generate resume + cover letter
6. **Auditor Suite** — Verify truth, tone, and compliance

## The Problem

Job applications are tedious and repetitive, but:
- AI-generated content gets flagged by detection tools
- Generic resumes don't convert
- Lying or embellishing backfires in interviews
- Tailoring takes hours per application

## The Solution

A "Hydra" of specialized agents that:
1. **Never lie** — All claims traced to source documents
2. **Sound human** — Anti-AI-detection patterns built in
3. **Tailor precisely** — Match JD subtext, not just keywords
4. **Find your edge** — Surface differentiators, not generic strengths

## Manual Setup

If `run.sh` doesn't work for you:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set API key
export OPENROUTER_API_KEY='sk-or-...'

# Run directly
python runtime/crewai/quick_crew.py \
    --jd examples/sample_jd.md \
    --resume examples/sample_resume.md \
    --out output.txt
```

## Configuration

Environment variables:
- `OPENROUTER_API_KEY` — **Required**. Get from [openrouter.ai/keys](https://openrouter.ai/keys)
- `OPENROUTER_MODEL` — Optional. Default: `anthropic/claude-3.5-sonnet`

Other models that work well:
- `anthropic/claude-sonnet-4.5` — Latest, most advanced (if available)
- `anthropic/claude-3.5-sonnet` — Fast, good quality (recommended)
- `anthropic/claude-3-opus` — Slower, highest quality
- `openai/gpt-4-turbo` — Alternative

## Architecture

```
COMMANDER (Orchestrator)
    │
    ├─→ RESEARCH-AGENT ─────→ Company intel
    ├─→ GAP-ANALYZER ────────→ Fit assessment
    │       │
    │       ▼
    │   [User Greenlight]
    │       │
    ├─→ INTERROGATOR-PREPPER → Deep truth extraction
    ├─→ DIFFERENTIATOR ──────→ Unique positioning
    ├─→ TAILORING-AGENT ─────→ Document generation
    ├─→ ATS-OPTIMIZER ───────→ Keyword optimization
    └─→ AUDITOR-SUITE ───────→ Final verification
```

## Quick Start

### Option 1: Use as Prompts (Zero Setup)

1. Copy agent prompts from `agents/*/prompt.md`
2. Use with Claude, GPT-4, or similar
3. Feed in your resume and JD
4. Execute agents in sequence

### Option 2: Go Implementation

```bash
cd runtime/go
go build -o hydra
./hydra --jd job.txt --resume resume.md
```

(Requires wiring up an LLM client—see `main.go`)

## Core Documents

| Document | Purpose |
|----------|---------|
| `docs/AGENTS.MD` | Truth rules (immutable) |
| `docs/AGENT_ROLES.MD` | Agent specifications |
| `docs/STYLE_GUIDE.MD` | Anti-AI language patterns |
| `docs/ARCHITECTURE.MD` | System design |

## Agents

| Agent | Purpose |
|-------|---------|
| Commander | Orchestrates workflow |
| Research-Agent | Company intel gathering |
| Gap-Analyzer | Requirement vs. experience matching |
| Interrogator-Prepper | Interview for missing details |
| Differentiator | Find unique positioning |
| Tailoring-Agent | Generate documents |
| ATS-Optimizer | Keyword optimization |
| Auditor-Suite | Truth/tone verification |

## Truth Laws (Non-Negotiable)

1. **Chronology is sacred** — No date changes, no reordering
2. **No fabrication** — No invented tools, metrics, or achievements
3. **The Everest Rule** — If you didn't climb it, don't say you climbed it
4. **Source authority** — Claims must trace to verified documents
5. **Adjacent framing** — Transferable experience framed honestly, not as direct

## Example Workflow

```
1. USER: Pastes job description

2. COMMANDER: 
   - Runs Research-Agent on company
   - Runs Gap-Analyzer on fit
   - Presents summary: "85% match, 2 gaps to address"
   - Asks: "Proceed?"

3. USER: "Yes"

4. COMMANDER:
   - Runs Interrogator-Prepper
   
5. INTERROGATOR-PREPPER:
   - "The JD mentions 'agentic AI tools.' Have you introduced 
      AI agents into infrastructure workflows?"
   
6. USER: "Yes, at [Current Company] I built a Claude-based PR review bot..."

7. [Interview continues for key gaps]

8. COMMANDER:
   - Runs Differentiator (finds unique angles)
   - Runs Tailoring-Agent (generates resume + cover letter)
   - Runs ATS-Optimizer (keyword coverage)
   - Runs Auditor-Suite (verification)

9. OUTPUT: 
   - Tailored resume
   - Cover letter
   - Audit trail
   - Differentiator notes
```

## Anti-AI Detection

The system includes built-in countermeasures:

- **Forbidden phrases** — "proven track record," "passionate about," etc.
- **Required variation** — Mixed sentence lengths, natural rhythm
- **Human elements** — Occasional asides, contractions, specificity
- **Tone calibration** — Different voice for resume vs. cover letter

See `docs/STYLE_GUIDE.MD` for full patterns.

## Configuration

### User Titles (Informal)
- Hautcake
- Master of Chocolates
- DJ Hautcake
- Your Grace

### Auto-Reject Criteria
- Contract-to-hire
- Below Senior level
- No compensation disclosed
- Relocation required (unless overridden)

## Directory Structure

```
composable-me/
├── docs/                    # Core documentation
│   ├── AGENTS.MD           # Truth rules
│   ├── AGENT_ROLES.MD      # Agent specs
│   ├── ARCHITECTURE.MD     # System design
│   └── STYLE_GUIDE.MD      # Language rules
│
├── agents/                  # Agent prompts
│   ├── commander/
│   ├── interrogator-prepper/
│   ├── gap-analyzer/
│   ├── differentiator/
│   ├── tailoring-agent/
│   ├── ats-optimizer/
│   └── auditor-suite/
│
├── runtime/                 # Implementation options
│   └── go/                 # Go orchestrator
│
├── sources/                 # Your resume files (add here)
│
└── output/                  # Generated applications
```

## Contributing

This is a personal job search tool, but the architecture is extensible:

1. **New agents** — Add to `agents/` with `prompt.md`
2. **Update specs** — Add to `AGENT_ROLES.MD`
3. **Test** — Run against real JDs, verify truth compliance

## License

Personal use. Don't use this to lie on applications.
