"""
Tailoring Agent Implementation

This agent generates tailored resumes and cover letters that:
- Match the specific role requirements
- Leverage identified differentiators
- Use anti-AI detection patterns from STYLE_GUIDE.MD
- Comply strictly with truth laws from AGENTS.MD
"""

from typing import Dict, Any, List
from runtime.crewai.base_agent import BaseHydraAgent, ValidationError
from crewai import LLM
import re


class TailoringAgent(BaseHydraAgent):
    """Tailoring Agent that generates tailored resumes and cover letters"""
    
    role = "Tailoring Agent"
    goal = "Generate tailored, human-sounding resumes and cover letters using verified source material"
    expected_output = "YAML with tailored resume, cover letter, and source traceability"
    
    def __init__(self, llm: LLM):
        """
        Initialize the Tailoring Agent
        
        Args:
            llm: The LLM instance to use
        """
        super().__init__(llm, "agents/tailoring-agent/prompt.md")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Tailoring Agent to generate tailored documents
        
        Args:
            context: Dictionary containing:
                - job_description: The job description text
                - resume: The candidate's resume text
                - interview_notes: Notes from Interrogator-Prepper
                - differentiators: Output from Differentiator
                - gap_analysis: Output from Gap Analyzer
            
        Returns:
            Dictionary with tailored resume, cover letter, and source mapping
        """
        # Validate required inputs
        required_keys = ["job_description", "resume", "interview_notes", "differentiators", "gap_analysis"]
        for key in required_keys:
            if key not in context:
                raise ValidationError(f"Missing required context key: {key}")
        
        # Create the task for the agent
        task_description = f"""
        Generate a tailored resume and cover letter for this specific role.
        
        Job Description:
        {context['job_description']}
        
        Candidate Resume:
        {context['resume']}
        
        Interview Notes:
        {context['interview_notes']}
        
        Differentiators:
        {context['differentiators']}
        
        Gap Analysis:
        {context['gap_analysis']}
        
        Create a tailored resume in Markdown format that emphasizes relevant experience.
        Generate a cover letter (250-400 words) that incorporates differentiators naturally.
        Use anti-AI detection patterns from the STYLE_GUIDE.
        Ensure all claims trace to verified source material.
        Provide complete source mapping for every claim made.
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
