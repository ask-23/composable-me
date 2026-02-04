"""
Composable Me Hydra — CrewAI Implementation

This orchestrates the job search pipeline using CrewAI agents.
Each agent loads its system prompt from the agents/ directory.

Usage:
    python -m runtime.crewai.crew --jd path/to/job.txt --resume path/to/resume.md

Environment:
    OPENROUTER_API_KEY: Your OpenRouter API key
    OPENROUTER_MODEL: Model to use (default: anthropic/claude-sonnet-4.5)
"""

import os
import sys
from pathlib import Path
from typing import Optional

# CrewAI imports
from crewai import Agent, Task, Crew, Process
from crewai import LLM

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_TRUTH_RULES = """\
1. Do not fabricate experience, tools, metrics, or outcomes.
2. Keep chronology consistent with provided sources.
3. If a claim cannot be supported by inputs, omit it or ask for clarification.
""".strip()

DEFAULT_STYLE_GUIDE = """\
- Prefer concrete details over hype.
- Avoid generic corporate phrases and AI clichés.
- Use clear, concise language and varied sentence lengths.
""".strip()


def load_prompt(agent_name: str) -> str:
    """Load agent prompt from agents/{agent_name}/prompt.md"""
    prompt_path = PROJECT_ROOT / "agents" / agent_name / "prompt.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")
    return prompt_path.read_text()


def load_docs() -> dict[str, str]:
    """Load all core documentation for agent context."""
    docs = {}
    docs_dir = PROJECT_ROOT / "docs"
    for doc_file in ["AGENTS.MD", "STYLE_GUIDE.MD"]:
        doc_path = docs_dir / doc_file
        if doc_path.exists():
            docs[doc_file] = doc_path.read_text()
    return docs


def get_llm() -> LLM:
    """Configure LLM for CrewAI using OpenRouter."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY not set. Export it:\n"
            "  export OPENROUTER_API_KEY='sk-or-...'"
        )

    model = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4.5")

    return LLM(
        model=f"openrouter/{model}",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )


class HydraCrew:
    """
    The Composable Me Hydra crew.
    
    Workflow:
    1. Commander analyzes JD, decides fit
    2. Gap Analyzer maps requirements to experience
    3. Interrogator-Prepper generates questions (user answers offline)
    4. Differentiator finds unique positioning
    5. Tailoring Agent creates resume + cover letter
    6. Auditor Suite reviews for truth + tone
    """
    
    def __init__(
        self,
        job_description: str,
        resume_text: str,
        interview_notes: Optional[str] = None,
    ):
        self.job_description = job_description
        self.resume_text = resume_text
        self.interview_notes = interview_notes or ""
        self.docs = load_docs()
        self.llm = get_llm()
        
        # Build agents
        self._build_agents()
    
    def _build_agents(self):
        """Create all Hydra agents with their prompts."""
        
        # Core context all agents need
        truth_rules = self.docs.get("AGENTS.MD", DEFAULT_TRUTH_RULES)
        style_guide = self.docs.get("STYLE_GUIDE.MD", DEFAULT_STYLE_GUIDE)
        
        # COMMANDER
        self.commander = Agent(
            role="Commander",
            goal="Orchestrate the job application process, ensure truth compliance, and produce a fit analysis",
            backstory=f"""
{load_prompt("commander")}

TRUTH RULES (INVIOLABLE):
{truth_rules}
""",
            llm=self.llm,
            verbose=True,
            allow_delegation=True,
        )
        
        # GAP ANALYZER
        self.gap_analyzer = Agent(
            role="Gap Analyzer",
            goal="Map job requirements to user experience and identify direct matches, adjacent experience, and gaps",
            backstory=f"""
{load_prompt("gap-analyzer")}

TRUTH RULES:
{truth_rules}
""",
            llm=self.llm,
            verbose=True,
        )
        
        # INTERROGATOR-PREPPER
        self.interrogator = Agent(
            role="Interrogator-Prepper",
            goal="Generate targeted interview questions to extract truthful details that fill gaps between the JD and resume",
            backstory=f"""
{load_prompt("interrogator-prepper")}

TRUTH RULES:
{truth_rules}
""",
            llm=self.llm,
            verbose=True,
        )
        
        # DIFFERENTIATOR
        self.differentiator = Agent(
            role="Differentiator",
            goal="Identify unique value propositions and positioning that set this candidate apart",
            backstory=f"""
{load_prompt("differentiator")}

TRUTH RULES:
{truth_rules}
""",
            llm=self.llm,
            verbose=True,
        )
        
        # TAILORING AGENT
        self.tailor = Agent(
            role="Tailoring Agent",
            goal="Generate a tailored resume and cover letter that honestly positions the candidate for this specific role",
            backstory=f"""
{load_prompt("tailoring-agent")}

STYLE GUIDE:
{style_guide}

TRUTH RULES:
{truth_rules}
""",
            llm=self.llm,
            verbose=True,
        )
        
        # AUDITOR SUITE
        self.auditor = Agent(
            role="Auditor Suite",
            goal="Verify all claims for truthfulness, check tone for AI detection risk, and ensure compliance with rules",
            backstory=f"""
{load_prompt("auditor-suite")}

STYLE GUIDE:
{style_guide}

TRUTH RULES:
{truth_rules}
""",
            llm=self.llm,
            verbose=True,
        )
    
    def build_tasks(self) -> list[Task]:
        """Build the task sequence for the crew."""
        
        # Task 1: Commander analyzes fit
        fit_analysis = Task(
            description=f"""
Analyze this job description and determine if it's worth pursuing.

JOB DESCRIPTION:
{self.job_description}

CANDIDATE RESUME:
{self.resume_text}

Provide:
1. Role level assessment (is this Sr+/Lead/Principal/Architect/VP?)
2. Key requirements extracted (explicit and implicit)
3. Initial fit assessment (percentage match estimate)
4. Red flags if any (CTH, vague comp, level mismatch)
5. Recommendation: PROCEED or PASS with brief rationale

Output as structured JSON.
""",
            expected_output="JSON fit analysis with role level, requirements, match percentage, red flags, and recommendation",
            agent=self.commander,
        )
        
        # Task 2: Gap analysis
        gap_analysis = Task(
            description=f"""
Using the job description and resume, map each requirement to the candidate's experience.

JOB DESCRIPTION:
{self.job_description}

CANDIDATE RESUME:
{self.resume_text}

For each requirement, classify as:
- direct_match: Clear evidence in resume
- adjacent: Related experience, transferable
- gap: No evidence, needs interview
- blocker: Critical requirement with no path

Output structured JSON with:
- requirement
- classification
- evidence (if any)
- framing_suggestion (for adjacent experience)
""",
            expected_output="JSON gap analysis mapping each JD requirement to evidence classification",
            agent=self.gap_analyzer,
            context=[fit_analysis],
        )
        
        # Task 3: Generate interview questions
        interview_questions = Task(
            description=f"""
Based on the gap analysis, generate targeted interview questions to extract truthful details.

Focus on:
1. Gaps identified - what experience might fill them?
2. Adjacent experience - how to frame it honestly?
3. Agentic AI / LLM integration if relevant
4. Cloud architecture specifics
5. Observability / SRE practices
6. Leadership and ownership stories

Generate 8-12 questions grouped by theme.
Use STAR+ format (Situation, Task, Actions, Results, Proof).
""",
            expected_output="Grouped interview questions in JSON format, 8-12 questions total",
            agent=self.interrogator,
            context=[gap_analysis],
        )
        
        # Task 4: Find differentiators
        differentiators = Task(
            description=f"""
Analyze the candidate's background and identify unique differentiators for this role.

RESUME:
{self.resume_text}

INTERVIEW NOTES (if available):
{self.interview_notes or "(No interview notes provided yet)"}

GAP ANALYSIS CONTEXT:
Use context from previous tasks.

Identify:
1. Rare skill combinations
2. Quantified outcome stories
3. Narrative through-line (career arc)
4. Contrarian strengths (weaknesses reframed)
5. Cultural fit signals

Output 2-3 primary differentiators with evidence and framing.
""",
            expected_output="2-3 primary differentiators with evidence and recommended framing",
            agent=self.differentiator,
            context=[gap_analysis, interview_questions],
        )
        
        # Task 5: Generate tailored resume + cover letter
        tailored_docs = Task(
            description=f"""
Generate a tailored resume and cover letter for this role.

JOB DESCRIPTION:
{self.job_description}

BASELINE RESUME:
{self.resume_text}

INTERVIEW NOTES:
{self.interview_notes or "(Use differentiators and gap analysis context)"}

REQUIREMENTS:
- Resume: Markdown format, emphasize relevant experience
- Cover letter: 3-4 paragraphs, specific to role, human voice
- Use differentiators from previous task
- NO FABRICATION - only use evidence from resume/interview notes
- Follow STYLE_GUIDE.MD for tone and anti-AI patterns

Output:
1. Complete tailored resume (Markdown)
2. Cover letter
3. Brief rationale for key choices
""",
            expected_output="Tailored resume (Markdown), cover letter, and rationale",
            agent=self.tailor,
            context=[differentiators, gap_analysis],
        )
        
        # Task 6: Audit everything
        audit_report = Task(
            description=f"""
Audit the tailored resume and cover letter for:

1. TRUTH AUDIT
   - Verify every claim has evidence in source materials
   - Flag any potential fabrications or exaggerations
   - Check dates, titles, company names

2. TONE AUDIT
   - Check for AI-detection triggers (forbidden phrases)
   - Verify sentence variation and human rhythm
   - Ensure senior, confident voice

3. ATS AUDIT
   - Check keyword coverage from JD
   - Verify format is parseable
   
4. COMPLIANCE AUDIT
   - Verify AGENTS.MD rules followed
   - Check chronology unchanged

Output:
- Issues found (blocking, warning, recommendation)
- Specific fixes for each issue
- Overall verdict: APPROVED or NEEDS_REVISION
""",
            expected_output="Structured audit report with issues, fixes, and verdict",
            agent=self.auditor,
            context=[tailored_docs],
        )
        
        return [
            fit_analysis,
            gap_analysis,
            interview_questions,
            differentiators,
            tailored_docs,
            audit_report,
        ]
    
    def run(self) -> dict:
        """Execute the Hydra crew and return results."""
        tasks = self.build_tasks()
        
        crew = Crew(
            agents=[
                self.commander,
                self.gap_analyzer,
                self.interrogator,
                self.differentiator,
                self.tailor,
                self.auditor,
            ],
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )
        
        result = crew.kickoff()
        return {
            "raw_output": str(result),
            "tasks_output": {
                task.description[:50]: str(task.output) 
                for task in tasks if task.output
            },
        }


def main():
    import argparse
    import json
    
    parser = argparse.ArgumentParser(
        description="Composable Me Hydra - CrewAI Job Search Pipeline"
    )
    parser.add_argument("--jd", required=True, help="Path to job description file")
    parser.add_argument("--resume", required=True, help="Path to resume file")
    parser.add_argument("--notes", help="Path to interview notes file (optional)")
    parser.add_argument("--out", help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    # Load inputs
    jd_text = Path(args.jd).read_text()
    resume_text = Path(args.resume).read_text()
    notes_text = Path(args.notes).read_text() if args.notes else None
    
    print("=" * 60)
    print("COMPOSABLE ME HYDRA - CrewAI Pipeline")
    print("=" * 60)
    print(f"JD: {args.jd}")
    print(f"Resume: {args.resume}")
    print(f"Notes: {args.notes or '(none)'}")
    print("=" * 60)
    
    # Run the crew
    hydra = HydraCrew(
        job_description=jd_text,
        resume_text=resume_text,
        interview_notes=notes_text,
    )
    
    result = hydra.run()
    
    # Output
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2))
        print(f"\nResults written to: {args.out}")
    else:
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(result["raw_output"])


if __name__ == "__main__":
    main()
