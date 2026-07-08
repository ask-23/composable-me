"""Executive Synthesizer agent: strategic brief + fit score.

The prompt lives in ``agents/executive-synthesizer/prompt.md`` (loaded like every
other agent's prompt). The recommendation is NOT decided here: the workflow maps the
model's ``fit_score`` to a recommendation deterministically (see
``runtime/crewai/contracts.recommendation_for_fit_score``). This agent supplies the
score, rationale, and strategy; validation only ensures a numeric ``fit_score`` is
present so the deterministic gate has something to act on.
"""

from typing import Any, Dict

from crewai import LLM

from runtime.crewai.base_agent import BaseHydraAgent

PROMPT_PATH = "agents/executive-synthesizer/prompt.md"


class ExecutiveSynthesizerAgent(BaseHydraAgent):
    """Executive Synthesizer that creates strategic intelligence briefs."""

    role = "Executive Synthesizer"
    goal = "Synthesize all agent outputs into an actionable strategic brief and fit score"
    expected_output = "JSON executive brief with a fit score, strategy, and action items"

    def __init__(self, llm: LLM):
        super().__init__(llm, prompt_path=PROMPT_PATH)

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run synthesis over all prior stage outputs and return the brief dict."""
        task_description = f"""
        Synthesize the following into a strategic executive brief (see your output schema).

        ### Job Description
        {context.get("job_description", "Not provided")}

        ### Candidate Résumé
        {context.get("resume", "Not provided")}

        ### Gap Analysis
        {context.get("gap_analysis", "Not available")}

        ### Interview Preparation
        {context.get("interview_notes", "Not available")}

        ### Differentiation Analysis
        {context.get("differentiation", "Not available")}

        ### Tailored Résumé
        {context.get("tailored_resume", "Not available")}

        ### Tailored Cover Letter
        {context.get("tailored_cover_letter", "Not available")}

        ### Audit Report
        {context.get("audit_report", "Not available")}

        Report a fit score (0-100) with a grounded rationale, the strategic angle,
        gap-mitigation strategies, and concrete action items. Be specific and honest.
        """
        task = self.create_task(task_description)
        return self.execute_with_retry(task)

    def _validate_schema(self, data: Dict[str, Any]) -> None:
        """Ensure a ``decision`` object with a numeric ``fit_score`` exists.

        Output shapes vary between models, so we locate the score leniently and
        normalize it to a number. The recommendation is assigned downstream by the
        deterministic gate, so we do not validate or guess it here.
        """
        super()._validate_schema(data)

        decision = data.get("decision")
        if not isinstance(decision, dict):
            decision = {"fit_score": data.get("fit_score", data.get("score", 0))}

        fit_score = decision.get("fit_score", decision.get("score", data.get("fit_score", 0)))
        if isinstance(fit_score, str):
            try:
                fit_score = float(fit_score.strip().rstrip("%"))
            except ValueError:
                fit_score = 0
        decision["fit_score"] = fit_score
        data["decision"] = decision
