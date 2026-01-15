# Composable Me — Multi-Agent Job Search Hydra

A truth-constrained, multi-agent system for generating high-quality job applications.

## Quick Start

```bash
# 1. Set your API key (choose one)
export TOGETHER_API_KEY='tgp_v1_...'        # Recommended (Together AI)
export OPENROUTER_API_KEY='sk-or-...'       # Alternative (OpenRouter)  
export CHUTES_API_KEY='your-key'            # Alternative (Chutes.ai)

# 2. Run with your files
./run.sh --jd path/to/job-description.md \
         --resume path/to/your-resume.md \
         --sources sources/ \
         --out output/

# Or with sample files
./run.sh --jd examples/sample_jd.md \
         --resume examples/sample_resume.md \
         --sources examples/ \
         --out output/
```

## How to Use This Right Now

**You have a job description and resume? Here's how to get tailored documents:**

1. **Put your files in the right place:**
   ```bash
   # Your job description (any .md or .txt file)
   cp your-job-posting.txt examples/my_jd.md
   
   # Your resume (any .md or .txt file)  
   cp your-resume.pdf examples/my_resume.md  # Convert PDF to text first
   
   # Create a sources directory with your background materials
   mkdir -p sources/
   cp your-resume.md sources/
   # Add any other docs that prove your experience
   ```

2. **Run the system:**
   ```bash
   ./run.sh --jd examples/my_jd.md \
            --resume examples/my_resume.md \
            --sources sources/ \
            --out my_application/
   ```

3. **Get your results:**
   ```bash
   ls my_application/
   # resume.md          <- Tailored resume
   # cover_letter.md    <- Tailored cover letter  
   # audit_report.yaml  <- Quality verification
   # execution_log.txt  <- What the system did
   ```

**That's it!** The system will analyze the job, map your experience, and generate tailored documents.

## File Picker Support

The CLI includes file picker support for easier file selection:

```bash
# Interactive file selection (if supported)
./run.sh --interactive

# Or specify files directly
./run.sh --jd "$(find . -name '*job*' -type f | head -1)" \
         --resume "$(find . -name '*resume*' -type f | head -1)" \
         --sources sources/ \
         --out output/
```

## Interactive Mode (Human-in-the-Loop)

You can run the workflow in interactive mode to review analysis and answer interview questions in real-time:

```bash
# Run with interaction enabled
python -m runtime.crewai.cli \
    --jd examples/sample_jd.md \
    --resume examples/sample_resume.md \
    --interactive
```

This allows you to:
1. **Review Gap Analysis:** Approve or reject the agent's findings before proceeding.
2. **Answer Interview Questions:** Provide specific details for identified gaps, which are then used to tailor the resume.

## What the System Does

The crew will:
1. **Gap Analyzer** — Map JD requirements to your experience
2. **Interrogator-Prepper** — Generate interview questions for gaps
3. **Differentiator** — Find your unique positioning
4. **Tailoring Agent** — Generate resume + cover letter
5. **ATS Optimizer** — Ensure keyword coverage
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

# Set API key (choose one)
export TOGETHER_API_KEY='tgp_v1_...'        # Recommended
export OPENROUTER_API_KEY='sk-or-...'       # Alternative

# Run CLI directly
python -m runtime.crewai.cli \
    --jd examples/sample_jd.md \
    --resume examples/sample_resume.md \
    --sources examples/ \
    --out output/

# Or use the quick runner (simplified)
python runtime/crewai/quick_crew.py \
    --jd examples/sample_jd.md \
    --resume examples/sample_resume.md \
    --out output.txt
```

## Configuration

### API Keys (choose one)

**Together AI (Recommended):**
```bash
export TOGETHER_API_KEY='tgp_v1_...'        # Get from together.ai
export TOGETHER_MODEL='meta-llama/Llama-3.3-70B-Instruct-Turbo'  # Optional override
```

**OpenRouter (Alternative):**
```bash
export OPENROUTER_API_KEY='sk-or-...'       # Get from openrouter.ai/keys
export OPENROUTER_MODEL='anthropic/claude-sonnet-4.5'  # Optional override
```

**Chutes.ai (Alternative):**
```bash
export CHUTES_API_KEY='your-key'            # Get from chutes.ai
export CHUTES_MODEL='deepseek-ai/DeepSeek-V3.1'  # Optional override
```

### Recommended Models

- **Llama 3.3 70B** (Together AI) — Fast, good quality, cost-effective
- **Claude Sonnet 4.5** (OpenRouter) — Highest quality, more expensive
- **DeepSeek V3.1** (Chutes.ai) — Good alternative

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

### Option 1: Full CLI (Recommended)

```bash
./run.sh --jd your-job.md --resume your-resume.md --sources sources/ --out output/
```

### Option 2: Quick Runner (Simplified)

```bash
python runtime/crewai/quick_crew.py --jd job.md --resume resume.md --out output.txt
```

### Option 3: Use as Prompts (Zero Setup)

1. Copy agent prompts from `agents/*/prompt.md`
2. Use with Claude, GPT-4, or similar
3. Feed in your resume and JD
4. Execute agents in sequence

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

## Troubleshooting

**"No API key found" error:**
```bash
# Set one of these API keys
export TOGETHER_API_KEY='tgp_v1_...'        # Recommended
export OPENROUTER_API_KEY='sk-or-...'       # Alternative
export CHUTES_API_KEY='your-key'            # Alternative
```

**"Invalid JSON output" error:**
- This usually means the LLM is having trouble with structured output
- Try switching to a different model or provider
- Claude models (OpenRouter) tend to be more reliable for structured output

**"Workflow failed: Document failed audit after maximum retries":**
- This is expected behavior - the auditor found issues it couldn't auto-fix
- Check the `audit_report.yaml` file for specific issues
- The system is working correctly by refusing to approve flawed documents

**Need help?**
- Check the `execution_log.txt` file for detailed workflow steps
- All outputs are saved even if the final audit fails
- The system prioritizes truth over convenience

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
   
6. USER: "Yes, at Limecord I built a Claude-based PR review bot..."

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
