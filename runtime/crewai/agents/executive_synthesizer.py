"""
Executive Synthesizer Agent Implementation

This agent synthesizes ALL prior agent outputs into a strategic executive brief.
It provides a decision recommendation (STRONG_PROCEED, PROCEED, etc.), strategic
positioning, gap mitigation strategies, and action items.

Model: Claude Sonnet 4 (or fallback to Llama 3.3)
"""

from typing import Dict, Any
from runtime.crewai.base_agent import BaseHydraAgent, ValidationError
from crewai import LLM


# Decision thresholds
DECISION_THRESHOLDS = {
    "STRONG_PROCEED": {
        "min_fit_score": 80,
        "max_blockers": 0,
        "requires_differentiator": True,
    },
    "PROCEED": {
        "min_fit_score": 65,
        "max_blockers": 0,
    },
    "PROCEED_WITH_CAUTION": {
        "min_fit_score": 50,
        "max_blockers": 1,
    },
    "PASS": {
        "min_fit_score": 0,  # Default for anything below thresholds
    }
}


class ExecutiveSynthesizerAgent(BaseHydraAgent):
    """Executive Synthesizer that creates strategic intelligence briefs"""
    
    role = "Executive Synthesizer"
    goal = "Transform all agent outputs into actionable strategic intelligence for job application decisions"
    expected_output = "JSON executive brief with decision, strategy, and action items"
    
    def __init__(self, llm: LLM):
        """
        Initialize the Executive Synthesizer Agent
        
        Args:
            llm: The LLM instance to use (should be frontier model)
        """
        # Use inline prompt since this is a new agent
        super().__init__(llm, prompt_path=None)
        self._custom_prompt = self._get_executive_prompt()
    
    def _get_executive_prompt(self) -> str:
        """Return the executive synthesizer prompt."""
        return """
# Executive Synthesizer Agent

You are a strategic career advisor who synthesizes complex analysis into clear, 
actionable executive briefs. Your role is to transform multiple agent outputs 
into a single decision-ready document.

## Your Task

Review all prior agent outputs and create a strategic executive brief that includes:

1. **Decision Recommendation**
   - STRONG_PROCEED: Fit score >= 80%, no blockers, strong differentiators
   - PROCEED: Fit score >= 65%, no blockers, gaps have mitigation
   - PROCEED_WITH_CAUTION: Fit score >= 50%, 1 blocker max with mitigation
   - PASS: Below 50% or multiple blockers

2. **Strategic Positioning**
   - Primary hook (memorable one-liner)
   - Key differentiators to emphasize
   - Narrative thread connecting the career

3. **Gap Strategy**
   - Critical gaps with specific mitigation approaches
   - Interview landmines to prepare for
   - Adjacent skill framing

4. **Action Items**
   - Immediate: What to do right now
   - Pre-interview: What to prepare
   - Research needed: What to learn about the company

## Output Format

Return valid JSON with this structure:
{
  "decision": {
    "recommendation": "STRONG_PROCEED|PROCEED|PROCEED_WITH_CAUTION|PASS",
    "fit_score": <number 0-100>,
    "rationale": "<2-3 sentence explanation>",
    "deal_makers": ["<strength 1>", "<strength 2>"],
    "deal_breakers": []
  },
  "strategic_angle": {
    "primary_hook": "<memorable one-liner>",
    "positioning_summary": "<2-3 sentences on how to position>",
    "differentiators": [
      {"hook": "<differentiator>", "when_to_use": "<context>"}
    ],
    "narrative_thread": "<career story arc>"
  },
  "gap_strategy": {
    "critical_gaps": [
      {"gap": "<skill>", "mitigation": "<approach>", "risk_level": "low|medium|high"}
    ],
    "interview_landmines": [
      {"topic": "<topic>", "preparation": "<how to handle>"}
    ]
  },
  "action_items": {
    "immediate": ["<action 1>", "<action 2>"],
    "pre_interview": ["<prep 1>", "<prep 2>"],
    "research_needed": ["<question 1>", "<question 2>"]
  },
  "application_materials": {
    "resume_verdict": "APPROVED|NEEDS_REVISION",
    "cover_letter_verdict": "APPROVED|NEEDS_REVISION",
    "key_changes_made": ["<change 1>", "<change 2>"]
  }
}

## Guidelines

- Be decisive. Executives want recommendations, not options.
- Be specific. Generic advice is useless.
- Be honest. Flag real risks, don't sugarcoat.
- Be actionable. Every insight should have a next step.
"""
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Executive Synthesizer to create strategic brief
        
        Args:
            context: Dictionary containing all prior agent outputs:
                - job_description: The job description text
                - resume: The candidate's resume text
                - gap_analysis: Output from Gap Analyzer
                - interview_notes: Notes from Interrogator-Prepper  
                - differentiation: Output from Differentiator
                - tailored_resume: Final tailored resume
                - tailored_cover_letter: Final cover letter
                - audit_report: Output from Auditor Suite
            
        Returns:
            Dictionary with executive brief
        """
        # Build comprehensive context for synthesis
        task_description = f"""
        Synthesize all agent outputs into a strategic executive brief.
        
        ## Original Inputs
        
        ### Job Description:
        {context.get('job_description', 'Not provided')}
        
        ### Candidate Resume:
        {context.get('resume', 'Not provided')}
        
        ## Agent Outputs
        
        ### Gap Analysis:
        {context.get('gap_analysis', 'Not available')}
        
        ### Interview Preparation:
        {context.get('interview_notes', 'Not available')}
        
        ### Differentiation Analysis:
        {context.get('differentiation', 'Not available')}
        
        ### Tailored Resume:
        {context.get('tailored_resume', 'Not available')}
        
        ### Tailored Cover Letter:
        {context.get('tailored_cover_letter', 'Not available')}
        
        ### Audit Report:
        {context.get('audit_report', 'Not available')}
        
        ## Instructions
        
        Create an executive brief that:
        1. Makes a clear decision recommendation (STRONG_PROCEED, PROCEED, PROCEED_WITH_CAUTION, or PASS)
        2. Identifies the primary strategic angle and positioning
        3. Provides specific gap mitigation strategies
        4. Lists concrete action items for the candidate
        
        Focus on actionable intelligence, not just summarization.
        """
        
        # Override prompt for this task
        if hasattr(self, '_custom_prompt'):
            self.prompt_content = self._custom_prompt
        
        task = self.create_task(task_description)
        
        # Execute with retry logic
        return self.execute_with_retry(task)
    
    def _validate_schema(self, data: Dict[str, Any]) -> None:
        """
        Validate that the output conforms to the required schema.

        This validation is lenient - it tries multiple locations for required fields
        and promotes/normalizes them to the expected structure.

        Args:
            data: The parsed output data

        Raises:
            ValidationError: If schema validation fails after all recovery attempts
        """
        # Base validation
        super()._validate_schema(data)

        valid_recommendations = ["STRONG_PROCEED", "PROCEED", "PROCEED_WITH_CAUTION", "PASS"]

        # Try to find decision in multiple locations (LLMs are inconsistent)
        decision = data.get("decision")

        # Check nested structures: executive_brief.decision, summary.decision, etc.
        if decision is None:
            for key in ["executive_brief", "summary", "analysis", "result", "output", "brief"]:
                nested = data.get(key)
                if isinstance(nested, dict) and "decision" in nested:
                    decision = nested["decision"]
                    break

        # Check for recommendation at root level (flat structure)
        if decision is None and "recommendation" in data:
            decision = {
                "recommendation": data["recommendation"],
                "fit_score": data.get("fit_score", data.get("score", 0)),
                "rationale": data.get("rationale", data.get("summary", ""))
            }

        # Last resort: infer from other fields
        if decision is None:
            # Try to construct decision from available data
            fit_score = data.get("fit_score", data.get("score", data.get("match_score", 0)))
            if isinstance(fit_score, str):
                try:
                    fit_score = int(fit_score.replace("%", ""))
                except ValueError:
                    fit_score = 50  # Default mid-range

            # Infer recommendation from fit_score if we have one
            if fit_score is not None:
                if fit_score >= 80:
                    rec = "STRONG_PROCEED"
                elif fit_score >= 65:
                    rec = "PROCEED"
                elif fit_score >= 50:
                    rec = "PROCEED_WITH_CAUTION"
                else:
                    rec = "PASS"

                decision = {
                    "recommendation": rec,
                    "fit_score": fit_score,
                    "rationale": data.get("rationale", data.get("summary", "Recommendation inferred from fit score"))
                }

        if decision is None:
            raise ValidationError("Executive brief must include 'decision' section (checked: root, executive_brief, summary, recommendation)")

        # Normalize decision to standard structure
        if isinstance(decision, dict):
            recommendation = decision.get("recommendation")
            # Try alternate keys if recommendation not found
            if recommendation is None:
                recommendation = decision.get("verdict", decision.get("status", decision.get("result")))
            if recommendation is None:
                raise ValidationError("Decision must include 'recommendation' field")

            # Normalize recommendation to uppercase
            recommendation = str(recommendation).upper().replace(" ", "_").replace("-", "_")

            # Map common variations
            rec_mapping = {
                "STRONG_PROCEED": "STRONG_PROCEED",
                "PROCEED": "PROCEED",
                "PROCEED_WITH_CAUTION": "PROCEED_WITH_CAUTION",
                "CAUTION": "PROCEED_WITH_CAUTION",
                "PASS": "PASS",
                "REJECT": "PASS",
                "NO": "PASS",
                "YES": "PROCEED",
                "APPROVED": "PROCEED",
                "STRONG_YES": "STRONG_PROCEED",
            }
            recommendation = rec_mapping.get(recommendation, recommendation)

            if recommendation not in valid_recommendations:
                # Default to PROCEED if we can't parse
                recommendation = "PROCEED"
            decision["recommendation"] = recommendation

        # Handle flat structure: {"decision": "PROCEED", ...}
        elif isinstance(decision, str):
            rec = decision.upper().replace(" ", "_").replace("-", "_")
            if rec not in valid_recommendations:
                rec = "PROCEED"
            decision = {"recommendation": rec}
        else:
            raise ValidationError(f"Decision must be a dict or string, got: {type(decision).__name__}")

        # Store normalized decision back to data
        data["decision"] = decision

        # Normalize fit_score into decision object (may be at root level)
        decision_obj = data["decision"]
        if "fit_score" not in decision_obj:
            # Check root level for fit_score
            root_fit_score = data.get("fit_score")
            if root_fit_score is not None:
                decision_obj["fit_score"] = root_fit_score
            else:
                # Default to 0 if not found anywhere
                decision_obj["fit_score"] = 0
        
        # Ensure fit_score is a number
        fit_score = decision_obj.get("fit_score", 0)
        if isinstance(fit_score, str):
            try:
                decision_obj["fit_score"] = int(fit_score.replace("%", ""))
            except ValueError:
                decision_obj["fit_score"] = 0

