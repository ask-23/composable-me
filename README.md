# **Composable Crew (Hydra)**





**Composable Crew** is a truth-constrained, multi-agent system for generating *high-quality, defensible job applications*.



It is designed for practitioners who want AI to act as a **force multiplier**, not a fabrication engine.



> **Hydra** is the internal codename for the system’s multi-headed agent architecture.

> The repository name reflects its core principle: *composable intelligence under explicit constraints*.



------





## **TL;DR**





Composable Crew generates tailored résumés and cover letters

**without fabricating experience, distorting timelines, or inflating claims**.



It optimizes for:



* accuracy over polish
* credibility over conversion
* long-term trust over short-term tricks





If the system cannot justify a claim, it will not produce it.



------





## **Why This Exists**





Most AI résumé tools optimize for plausibility.



Composable Crew optimizes for **truth under scrutiny**.



This system assumes:



* you already have real experience
* accuracy matters more than surface-level fit
* credibility compounds, but small distortions don’t stay hidden





Hydra will refuse to generate content it cannot defend.



That refusal is intentional.



------





## **Design Constraints**





This project is intentionally constrained.

Those constraints *are the product*.





### **1. Truth is a hard boundary**





Agents are not allowed to invent tools, metrics, roles, or outcomes.

Every claim must trace back to supplied source material or explicit user input.





### **2. Chronology is immutable**





Dates and role sequences are never altered to improve fit.

Career history is treated as an ordered system, not a bag of keywords.





### **3. Narrow agents, strong orchestration**





Each agent has a single responsibility.

Coordination and judgment live in the orchestrator, not in oversized prompts.





### **4. Bounded optimization**





ATS optimization is allowed only within verified facts.

Keyword coverage must never change meaning.





### **5. Failing is acceptable**





If constraints cannot be satisfied, the system fails loudly.

Silent degradation is considered a defect.





### **6. Human-in-the-loop by design**





The system assumes human review for:



* ambiguous claims
* adjacent experience framing
* final approval





Automation stops where judgment begins.



------





## **What It Does**





Composable Crew uses a coordinated set of specialized agents to turn raw career material into **credible, role-specific output**.





### **The Workflow**





1. **Analyze**

   Map job requirements against documented experience.

2. **Interrogate**

   Extract missing but *real* details through targeted Q&A.

3. **Differentiate**

   Identify authentic positioning signals (not buzzwords).

4. **Generate**

   Produce tailored résumé and cover letter drafts.

5. **Optimize**

   Improve ATS keyword coverage *without distorting truth*.

6. **Audit**

   Verify that every claim is justified and traceable.





------





## **Output Artifacts**





A successful run produces a fully auditable result set:

| **File**          | **Purpose**                       |
| ----------------- | --------------------------------- |
| resume.md         | Tailored résumé (Markdown)        |
| cover_letter.md   | Tailored cover letter             |
| audit_report.yaml | Claim-by-claim truth verification |
| execution_log.txt | Detailed agent execution trace    |

The audit report is not decorative.

It is the system’s accountability layer.



------





## **Architecture Overview**



```
COMMANDER (Orchestrator)
    │
    ├── GAP-ANALYZER ─────────→ Requirement / experience fit
    ├── INTERROGATOR-PREPPER ─→ Targeted detail extraction
    ├── DIFFERENTIATOR ───────→ Authentic positioning
    ├── TAILORING-AGENT ──────→ Document generation
    ├── ATS-OPTIMIZER ────────→ Keyword optimization (bounded)
    └── AUDITOR-SUITE ────────→ Truth enforcement
```

Each agent is intentionally narrow.

Coordination happens at the orchestration layer.



------





## **Tech Stack**



| **Layer**       | **Technology**                  |
| --------------- | ------------------------------- |
| Agent Framework | CrewAI 0.86+                    |
| LLM Abstraction | LiteLLM                         |
| Runtime         | Python 3.11+ (3.13 recommended) |
| Web Frontend    | Astro 5 + Svelte 5              |
| Web Backend     | Litestar                        |
| Database        | PostgreSQL 16                   |
| Observability   | OpenTelemetry                   |
| Testing         | pytest, Playwright              |



------





## **Requirements**





* **Python 3.11+**
* **Node.js 18+** (for the web interface)
* At least one supported LLM API key





------





## **Quick Start (CLI)**



```
git clone https://github.com/ask-23/composable-crew.git
cd composable-crew

cp .env.example .env
# Add at least one LLM API key

chmod +x run.sh

./run.sh \
  --jd examples/sample_jd.md \
  --resume examples/sample_resume.md \
  --sources sources/ \
  --out output/
```

The run.sh script will:



* create and manage a Python virtual environment
* install dependencies
* execute the full workflow







### **Manual Setup (if needed)**



```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m runtime.crewai.cli --help
```



------





## **Configuration**







### **LLM Providers**





The CLI checks providers in this order and uses the first available key:

```
TOGETHER_API_KEY=tgp_v1_...
CHUTES_API_KEY=cpk_...
OPENROUTER_API_KEY=sk-or-...
```

> **Note:**

> Anthropic Claude models are accessed via OpenRouter.



------





### **Database (Web Interface)**



```
HYDRA_DATABASE_URL=postgresql://hydra:hydra@localhost:5432/hydra
```



------





### **Observability (Optional)**



```
OTEL_ENABLED=false
OTEL_SERVICE_NAME=hydra-backend
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```



------





## **Web Interface (Optional)**



```
docker run -d --name hydra-db \
  -e POSTGRES_USER=hydra \
  -e POSTGRES_PASSWORD=hydra \
  -e POSTGRES_DB=hydra \
  -p 5432:5432 \
  postgres:16

PYTHONPATH="$(pwd)" python -m web.backend.db.migrate

cd web/backend && ./run.sh
cd web/frontend && npm install && npm run dev
```



* Frontend: http://localhost:4321
* Backend API: http://localhost:8000





------





## **Project Structure**



```
composable-crew/
├── runtime/crewai/        # Core runtime & orchestration
├── agents/                # Agent prompt templates
├── web/                   # Optional UI (Astro + Litestar)
├── tests/                 # pytest + E2E tests
├── examples/              # Sample inputs
└── run.sh                 # Primary entry point
```



------





## **Failure Modes (By Design)**





* **No API key found**

  → Set at least one provider key.

* **Document failed audit**

  → The system refused to approve unverifiable claims.

  This is expected behavior.

* **Permission denied:** **run.sh**

  → Run chmod +x run.sh.

* **Database connection failed**

  → Ensure PostgreSQL is running and HYDRA_DATABASE_URL is set correctly.





------





## **License**





MIT License.



Use responsibly.

This system exists to **amplify real experience**, not invent it.
