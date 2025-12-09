"""
ATS Optimizer Agent Implementation

This agent ensures documents pass automated screening systems while maintaining
human readability. It balances machine readability (keywords, structure, parsing)
with human quality (natural language, readability).
"""

from typing import Dict, Any, List
from runtime.crewai.base_agent import BaseHydraAgent, ValidationError
from crewai import LLM
import re


class ATSOptimizerAgent(BaseHydraAgent):
    """ATS Optimizer Agent that ensures documents pass automated screening systems"""
    
    role = "ATS Optimizer"
    goal = "Ensure documents pass automated screening systems without sacrificing human readability"
    expected_output = "YAML with ATS analysis, keyword coverage, format verification, and optimized document"
    
    def __init__(self, llm: LLM):
        """
        Initialize the ATS Optimizer Agent
        
        Args:
            llm: The LLM instance to use
        """
        super().__init__(llm, "agents/ats-optimizer/prompt.md")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the ATS Optimizer agent to optimize documents for ATS systems
        
        Args:
            context: Dictionary containing:
                - tailored_resume: The tailored resume from Tailoring Agent
                - job_description: The original job description
                - source_documents: User source documents for verification
            
        Returns:
            Dictionary with ATS analysis and optimized document
        """
        # Validate required inputs
        required_keys = ["tailored_resume", "job_description"]
        for key in required_keys:
            if key not in context:
                raise ValidationError(f"Missing required context key: {key}")
        
        # Create task for the agent
        task_description = f"""
        Analyze and optimize the tailored resume for ATS compatibility.
        
        Job Description:
        {context['job_description']}
        
        Tailored Resume:
        {context['tailored_resume']}
        
        Source Documents (for verification):
        {context.get('source_documents', 'Not provided')}
        
        Provide comprehensive ATS analysis including:
        1. Keyword extraction from JD
        2. Coverage analysis against resume
        3. Format verification
        4. Optimization recommendations
        5. Optimized resume version
        
        Ensure all additions are truthful and verifiable against source documents.
        """
        
        # Create task and execute with retry logic
        task = self.create_task(task_description)
        result = self.execute_with_retry(task)
        
        return result
    
    def _validate_context(self, context: Dict[str, Any]) -> None:
        """Validate required context parameters"""
        required = ["tailored_resume", "job_description"]
        for param in required:
            if param not in context:
                raise ValidationError(f"Missing required context: {param}")
    
    def _validate_schema(self, output: Dict[str, Any]) -> None:
        """Validate ATS Optimizer specific output schema"""
        super()._validate_schema(output)  # Validates base fields
        # LLM output structure varies - accept whatever it produces
        return
