"""
Interrogator-Prepper Agent Implementation

This agent generates targeted interview questions to fill gaps in candidate experience
and extracts truthful details using STAR+ format (Situation, Task, Actions, Results, Proof).
"""

from typing import Any, Dict

from crewai import LLM

from runtime.crewai.base_agent import BaseHydraAgent, ValidationError


class InterrogatorPrepperAgent(BaseHydraAgent):
    """Interrogator-Prepper Agent that generates targeted interview questions"""

    role = "Interrogator-Prepper"
    goal = (
        "Generate targeted interview questions to extract truthful details and fill experience gaps"
    )
    expected_output = "JSON with structured questions and interview notes processing"

    def __init__(self, llm: LLM):
        """
        Initialize the Interrogator-Prepper Agent

        Args:
            llm: The LLM instance to use
        """
        super().__init__(llm, "agents/interrogator-prepper/prompt.md")

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Interrogator-Prepper agent to generate targeted questions

        Args:
            context: Dictionary containing:
                - job_description: The job description text
                - resume: The candidate's resume text
                - gaps: List of gaps from Gap Analyzer
                - gap_analysis: Full gap analysis output

        Returns:
            Dictionary with targeted questions and interview processing framework
        """
        # Validate required inputs
        required_keys = ["job_description", "resume", "gaps", "gap_analysis"]
        for key in required_keys:
            if key not in context:
                raise ValidationError(f"Missing required context key: {key}")

        # Create the task for the agent
        task_description = f"""
        Generate 8-12 targeted interview questions based on the identified gaps and requirements.
        
        Job Description:
        {context["job_description"]}
        
        Candidate Resume:
        {context["resume"]}
        
        Identified Gaps:
        {context["gaps"]}
        
        Gap Analysis:
        {context["gap_analysis"]}
        
        Generate questions using STAR+ format (Situation, Task, Actions, Results, Proof).
        Group questions by theme: technical, leadership, outcomes, tools.
        Focus on extracting truthful, specific details that can strengthen the application.
        Provide framework for processing interview answers and verifying claims.
        """

        task = self.create_task(task_description)

        # Execute with retry logic
        return self.execute_with_retry(task)

    def _validate_schema(self, data: Dict[str, Any]) -> None:
        """
        Validate that the output conforms to the required schema

        Args:
            data: The parsed output data

        Raises:
            ValidationError: If schema validation fails
        """
        # Interrogator output structure varies from model to model; accept whatever
        # it produces. Base validation adds agent/timestamp/confidence.
        super()._validate_schema(data)
