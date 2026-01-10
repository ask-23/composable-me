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
        
        # Execute with retry logic
        result = self.execute_with_retry(task_description, context)
        
        # Validate the output
        self._validate_schema(result)
        
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
        
        # Required top-level fields
        required_fields = [
            "ats_report",
            "summary", 
            "keyword_analysis",
            "format_analysis",
            "optimized_resume",
            "changes_made",
            "verification"
        ]
        
        for field in required_fields:
            if field not in output:
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate ats_report structure
        ats_report = output["ats_report"]
        required_ats_fields = ["meta", "summary", "keyword_analysis", "format_analysis"]
        for field in required_ats_fields:
            if field not in ats_report:
                raise ValidationError(f"Missing required ats_report field: {field}")
        
        # Validate summary fields
        summary = output["summary"]
        required_summary_fields = ["keyword_coverage", "format_score", "ats_ready", "human_readable"]
        for field in required_summary_fields:
            if field not in summary:
                raise ValidationError(f"Missing required summary field: {field}")
        
        # Validate keyword_coverage is a percentage string
        coverage = summary["keyword_coverage"]
        if not isinstance(coverage, str) or not coverage.endswith('%'):
            raise ValidationError("keyword_coverage must be a percentage string (e.g., '85%')")
        
        # Validate format_score is a percentage string  
        format_score = summary["format_score"]
        if not isinstance(format_score, str) or not format_score.endswith('%'):
            raise ValidationError("format_score must be a percentage string (e.g., '90%')")
        
        # Validate boolean fields
        if not isinstance(summary["ats_ready"], bool):
            raise ValidationError("ats_ready must be a boolean")
        if not isinstance(summary["human_readable"], bool):
            raise ValidationError("human_readable must be a boolean")
        
        # Validate verification structure
        verification = output["verification"]
        required_verification_fields = ["all_additions_truthful", "human_readable"]
        for field in required_verification_fields:
            if field not in verification:
                raise ValidationError(f"Missing required verification field: {field}")
            if not isinstance(verification[field], bool):
                raise ValidationError(f"verification.{field} must be a boolean")
        
        # Validate changes_made is a list
        if not isinstance(output["changes_made"], list):
            raise ValidationError("changes_made must be a list")
        
        # Validate optimized_resume is a string
        if not isinstance(output["optimized_resume"], str):
            raise ValidationError("optimized_resume must be a string")
