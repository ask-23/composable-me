#!/usr/bin/env python3
"""
Composable Me Hydra — Quick CrewAI Runner

A simpler, single-file version for quick testing.
Prompts are embedded for portability.

Usage:
    ./runtime/crewai/quick_crew.py --jd job.txt --resume resume.md

    Or with venv activated:
    source .venv/bin/activate && python runtime/crewai/quick_crew.py --jd job.txt --resume resume.md

Environment:
    OPENROUTER_API_KEY: Your OpenRouter API key
"""

import os
import sys
import argparse
from pathlib import Path

import litellm

try:
    from crewai import Agent, Task, Crew, Process, LLM
except ImportError:
    print("ERROR: crewai not installed. Run: pip install crewai")
    sys.exit(1)


# ============================================================================
# EMBEDDED PROMPTS (simplified versions)
# ============================================================================

TRUTH_RULES = """
TRUTH LAWS (INVIOLABLE):
1. Chronology must match reality - no reordering dates or jobs
2. No fabrication - no invented tools, metrics, or achievements  
3. The Everest Rule - if it didn't happen, don't write it
4. Source authority - claims must trace to resume or interview notes
5. Adjacent framing - transferable experience framed honestly, not as direct
"""

COMMANDER_PROMPT = """
You are COMMANDER, orchestrator of the Composable Me Hydra job search system.

Your job:
- Analyze job descriptions and determine fit
- Coordinate sub-agents to produce tailored applications
- Enforce truth rules at all times
- Produce clear, actionable recommendations

You are a chief of staff for a senior engineer/leader. Calm, strategic, decisive.
Never invent experience. Never alter chronology. When in doubt, ask or frame as adjacent.
"""

GAP_ANALYZER_PROMPT = """
You are GAP-ANALYZER, the requirement mapping specialist.

Your job:
- Extract all requirements from job descriptions (explicit, implicit, cultural)
- Map each requirement to candidate's experience
- Classify as: direct_match, adjacent, gap, or blocker
- Provide framing suggestions for adjacent experience

Be precise. Cite evidence. Don't assume what's not stated.
"""

INTERROGATOR_PROMPT = """
You are INTERROGATOR-PREPPER, the truth extraction specialist.

Your job:
- Generate targeted interview questions based on gap analysis
- Focus on stories and specifics that prove capability
- Use STAR+ framework (Situation, Task, Actions, Results, Proof)
- Never assume - only ask

Themes to probe:
- Agentic AI / LLM integration in infrastructure
- Cloud architecture (AWS multi-account, security, governance)
- Observability / SRE (SLOs, incident response)
- Leadership and ownership stories
"""

DIFFERENTIATOR_PROMPT = """
You are DIFFERENTIATOR, the positioning specialist.

Your job:
- Find what makes this candidate unique for THIS role
- Identify rare skill combinations
- Extract quantified outcome stories
- Find the narrative thread (career arc)
- Surface contrarian strengths

Output 2-3 primary differentiators with evidence and framing.
"""

TAILOR_PROMPT = """
You are TAILORING-AGENT, the document generation specialist.

Your job:
- Create tailored resumes and cover letters
- Emphasize experience that matches the role's hidden subtext
- Use human voice - no AI clichés or corporate sludge
- Follow the formula: [Action Verb] + [What] + [Scale] + [Result]

FORBIDDEN PHRASES:
- "proven track record"
- "passionate about"  
- "leverage my expertise"
- "cutting-edge"
- "best-in-class"
- "synergy"

Vary sentence lengths. Be specific. Sound like a real senior engineer.
"""

AUDITOR_PROMPT = """
You are AUDITOR-SUITE, the verification specialist.

Your job:
1. TRUTH AUDIT - verify every claim has evidence
2. TONE AUDIT - check for AI-detection triggers
3. ATS AUDIT - verify keyword coverage
4. COMPLIANCE AUDIT - ensure rules followed

Flag issues as: blocking (must fix), warning (should fix), recommendation (nice to have).
Be specific about fixes. Don't approve if there are blockers.
"""


# ============================================================================
# CREW SETUP
# ============================================================================

def get_llm() -> LLM:
    """Configure LLM via OpenRouter."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        print("Run: export OPENROUTER_API_KEY='sk-or-...'")
        sys.exit(1)

    model = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4.5")

    return LLM(
        model=f"openrouter/{model}",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )


def build_crew(jd: str, resume: str, notes: str = "") -> Crew:
    """Build the Hydra crew with all agents and tasks."""
    
    llm = get_llm()
    
    # === AGENTS ===
    
    commander = Agent(
        role="Commander",
        goal="Analyze job fit and orchestrate the application process",
        backstory=f"{COMMANDER_PROMPT}\n\n{TRUTH_RULES}",
        llm=llm,
        verbose=True,
        allow_delegation=True,
    )
    
    gap_analyzer = Agent(
        role="Gap Analyzer", 
        goal="Map job requirements to candidate experience",
        backstory=f"{GAP_ANALYZER_PROMPT}\n\n{TRUTH_RULES}",
        llm=llm,
        verbose=True,
    )
    
    interrogator = Agent(
        role="Interrogator-Prepper",
        goal="Generate interview questions to fill gaps",
        backstory=f"{INTERROGATOR_PROMPT}\n\n{TRUTH_RULES}",
        llm=llm,
        verbose=True,
    )
    
    differentiator = Agent(
        role="Differentiator",
        goal="Find unique positioning for this candidate",
        backstory=f"{DIFFERENTIATOR_PROMPT}\n\n{TRUTH_RULES}",
        llm=llm,
        verbose=True,
    )
    
    tailor = Agent(
        role="Tailoring Agent",
        goal="Generate tailored resume and cover letter",
        backstory=f"{TAILOR_PROMPT}\n\n{TRUTH_RULES}",
        llm=llm,
        verbose=True,
    )
    
    auditor = Agent(
        role="Auditor Suite",
        goal="Verify truth, tone, and compliance",
        backstory=f"{AUDITOR_PROMPT}\n\n{TRUTH_RULES}",
        llm=llm,
        verbose=True,
    )
    
    # === TASKS ===
    
    task_fit = Task(
        description=f"""
Analyze this job description and determine fit.

JOB DESCRIPTION:
{jd}

CANDIDATE RESUME:
{resume}

Output JSON with:
- role_level: (Junior/Mid/Senior/Lead/Principal/Architect/VP)
- key_requirements: list of 5-10 key requirements
- match_estimate: percentage
- red_flags: list (CTH, vague comp, etc.)
- recommendation: PROCEED or PASS
- rationale: 2-3 sentences
""",
        expected_output="JSON fit analysis",
        agent=commander,
    )
    
    task_gap = Task(
        description=f"""
Map each requirement to candidate experience.

JOB DESCRIPTION:
{jd}

RESUME:
{resume}

For each requirement from the fit analysis, output:
- requirement: the requirement
- classification: direct_match | adjacent | gap | blocker
- evidence: quote or reference from resume (if any)
- framing: how to position this (for adjacent/gap)
""",
        expected_output="JSON gap analysis",
        agent=gap_analyzer,
        context=[task_fit],
    )
    
    task_questions = Task(
        description="""
Generate 8-12 targeted interview questions based on the gap analysis.

Group by theme:
- Agentic AI / LLM (if relevant to JD)
- Cloud / Infrastructure
- Observability / SRE
- Leadership / Ownership

Use STAR+ format. Focus on gaps and adjacent experience.
""",
        expected_output="Grouped interview questions",
        agent=interrogator,
        context=[task_gap],
    )
    
    task_diff = Task(
        description=f"""
Find 2-3 primary differentiators for this candidate.

RESUME:
{resume}

INTERVIEW NOTES:
{notes if notes else "(none provided - use gap analysis context)"}

For each differentiator:
- differentiator: one sentence hook
- evidence: specific proof from resume/notes
- framing: how to use in resume/cover letter
""",
        expected_output="2-3 differentiators with evidence",
        agent=differentiator,
        context=[task_gap, task_questions],
    )
    
    task_tailor = Task(
        description=f"""
Generate a tailored resume and cover letter.

JOB DESCRIPTION:
{jd}

BASELINE RESUME:
{resume}

INTERVIEW NOTES:
{notes if notes else "(use differentiators from context)"}

Output:
1. TAILORED RESUME (Markdown format)
2. COVER LETTER (3-4 paragraphs)
3. KEY CHOICES (brief rationale)

NO FABRICATION. Use human voice. Vary sentence lengths.
""",
        expected_output="Resume, cover letter, and rationale",
        agent=tailor,
        context=[task_diff, task_gap],
    )
    
    task_audit = Task(
        description="""
Audit the tailored documents.

Check:
1. Truth - every claim has evidence?
2. Tone - sounds human, not AI?
3. ATS - keywords from JD present?
4. Compliance - rules followed?

Output:
- issues: list with severity (blocking/warning/recommendation)
- fixes: specific fix for each issue
- verdict: APPROVED or NEEDS_REVISION
""",
        expected_output="Audit report with verdict",
        agent=auditor,
        context=[task_tailor],
    )
    
    return Crew(
        agents=[commander, gap_analyzer, interrogator, differentiator, tailor, auditor],
        tasks=[task_fit, task_gap, task_questions, task_diff, task_tailor, task_audit],
        process=Process.sequential,
        verbose=True,
    )


def main():
    parser = argparse.ArgumentParser(description="Composable Me Hydra - Quick CrewAI Runner")
    parser.add_argument("--jd", required=True, help="Job description file")
    parser.add_argument("--resume", required=True, help="Resume file")
    parser.add_argument("--notes", help="Interview notes file (optional)")
    parser.add_argument("--out", help="Output file (optional)")
    args = parser.parse_args()
    
    jd = Path(args.jd).read_text()
    resume = Path(args.resume).read_text()
    notes = Path(args.notes).read_text() if args.notes else ""
    
    print("=" * 70)
    print("COMPOSABLE ME HYDRA — CrewAI Pipeline")
    print("=" * 70)
    print(f"JD: {args.jd} ({len(jd)} chars)")
    print(f"Resume: {args.resume} ({len(resume)} chars)")
    print(f"Notes: {args.notes or '(none)'}")
    print("=" * 70)
    print()
    
    crew = build_crew(jd, resume, notes)
    result = crew.kickoff()
    
    print()
    print("=" * 70)
    print("FINAL OUTPUT")
    print("=" * 70)
    print(result)
    
    if args.out:
        Path(args.out).write_text(str(result))
        print(f"\nSaved to: {args.out}")


if __name__ == "__main__":
    main()
