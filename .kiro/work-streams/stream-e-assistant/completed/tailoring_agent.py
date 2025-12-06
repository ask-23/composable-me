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
        # First run base validation
        super()._validate_schema(data)
        
        # Validate required fields for Tailoring Agent
        required_fields = ["tailored_resume", "cover_letter", "sources_used"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate tailored_resume structure
        tailored_resume = data.get("tailored_resume", {})
        if not isinstance(tailored_resume, dict):
            raise ValidationError("tailored_resume must be a dictionary")
        
        resume_fields = ["format", "content"]
        for field in resume_fields:
            if field not in tailored_resume:
                raise ValidationError(f"tailored_resume missing field: {field}")
        
        # Validate resume format is markdown
        if tailored_resume.get("format") != "markdown":
            raise ValidationError("tailored_resume format must be 'markdown'")
        
        # Validate cover_letter structure
        cover_letter = data.get("cover_letter", {})
        if not isinstance(cover_letter, dict):
            raise ValidationError("cover_letter must be a dictionary")
        
        cover_fields = ["format", "content", "word_count"]
        for field in cover_fields:
            if field not in cover_letter:
                raise ValidationError(f"cover_letter missing field: {field}")
        
        # Validate cover letter format is markdown
        if cover_letter.get("format") != "markdown":
            raise ValidationError("cover_letter format must be 'markdown'")
        
        # Validate word count is within range (250-400 words)
        word_count = cover_letter.get("word_count")
        if not isinstance(word_count, int):
            raise ValidationError("cover_letter word_count must be an integer")
        if not 250 <= word_count <= 400:
            raise ValidationError(f"cover_letter word_count must be 250-400, got {word_count}")
        
        # Validate sources_used is a list
        sources_used = data.get("sources_used", [])
        if not isinstance(sources_used, list):
            raise ValidationError("sources_used must be a list")
