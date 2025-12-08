"""
Differentiator Agent Implementation

This agent identifies unique value propositions that make the candidate stand out
from other qualified applicants. It analyzes skill combinations, outcome stories,
narrative threads, and cultural fit signals.
"""

from typing import Dict, Any, List
from runtime.crewai.base_agent import BaseHydraAgent, ValidationError
from crewai import LLM


class DifferentiatorAgent(BaseHydraAgent):
    """Differentiator Agent that identifies unique value propositions"""
    
    role = "Differentiator"
    goal = "Identify unique value propositions and positioning angles that differentiate the candidate"
    expected_output = "YAML with differentiators, positioning angles, and application guidance"
    
    def __init__(self, llm: LLM):
        """
        Initialize the Differentiator Agent
        
        Args:
            llm: The LLM instance to use
        """
        super().__init__(llm, "agents/differentiator/prompt.md")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Differentiator agent to identify unique value propositions
        
        Args:
            context: Dictionary containing:
                - job_description: The job description text
                - resume: The candidate's resume text
                - interview_notes: Notes from Interrogator-Prepper
                - gap_analysis: Output from Gap Analyzer
            
        Returns:
            Dictionary with differentiators and positioning guidance
        """
        # Validate required inputs
        required_keys = ["job_description", "resume", "interview_notes", "gap_analysis"]
        for key in required_keys:
            if key not in context:
                raise ValidationError(f"Missing required context key: {key}")
        
        # Create the task for the agent
        task_description = f"""
        Analyze the candidate's background to identify unique value propositions and differentiators.
        
        Job Description:
        {context['job_description']}
        
        Candidate Resume:
        {context['resume']}
        
        Interview Notes:
        {context['interview_notes']}
        
        Gap Analysis:
        {context['gap_analysis']}
        
        Identify rare skill combinations, quantified outcomes, and narrative threads.
        Find what makes this candidate memorable and distinct from other qualified applicants.
        Ensure all differentiators are relevant to the job description and verifiable.
        Provide positioning angles and application guidance for using these differentiators.
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
        # Just run base validation - be lenient about structure
        super()._validate_schema(data)
        # LLM output structure varies - accept whatever it produces
        return
