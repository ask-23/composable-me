"""
Gap Analyzer Agent Implementation

This agent maps job requirements to candidate experience and classifies each as:
- direct_match: Clear evidence of meeting/exceeding requirement
- adjacent_experience: Related experience that demonstrates capability  
- gap: No direct or adjacent experience found
- blocker: Cannot be addressed through framing or transfer
"""

from typing import Dict, Any, List
from runtime.crewai.base_agent import BaseHydraAgent, ValidationError
from crewai import LLM
import re


class GapAnalyzerAgent(BaseHydraAgent):
    """Gap Analyzer Agent that maps job requirements to candidate experience"""
    
    role = "Gap Analyzer"
    goal = "Map job requirements to candidate experience and classify fit levels"
    expected_output = "YAML with requirements analysis, classifications, and fit scoring"
    
    def __init__(self, llm: LLM):
        """
        Initialize the Gap Analyzer Agent
        
        Args:
            llm: The LLM instance to use
        """
        super().__init__(llm, "agents/gap-analyzer/prompt.md")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Gap Analyzer agent to map requirements to experience
        
        Args:
            context: Dictionary containing:
                - job_description: The job description text
                - resume: The candidate's resume text
                - research_data: Optional research data
            
        Returns:
            Dictionary with requirements analysis and fit scoring
        """
        # Validate required inputs
        required_keys = ["job_description", "resume"]
        for key in required_keys:
            if key not in context:
                raise ValidationError(f"Missing required context key: {key}")
        
        # Create the task for the agent
        task_description = f"""
        Analyze the job requirements and map them to the candidate's experience.
        
        Job Description:
        {context['job_description']}
        
        Candidate Resume:
        {context['resume']}
        
        Research Data:
        {context.get('research_data', 'Not provided')}
        
        Extract all requirements (explicit and implicit) from the job description.
        Map each requirement to the candidate's experience from the resume.
        Classify each as direct_match, adjacent_experience, gap, or blocker.
        Provide evidence and confidence levels for each classification.
        Calculate overall fit score based on the classifications.
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
        
        # Validate required fields for Gap Analyzer
        required_fields = ["requirements", "fit_score", "gaps", "blockers"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate requirements is a list
        requirements = data.get("requirements", [])
        if not isinstance(requirements, list):
            raise ValidationError("requirements must be a list")
        
        # Validate each requirement has required fields
        for i, req in enumerate(requirements):
            if not isinstance(req, dict):
                raise ValidationError(f"Requirement {i} must be a dictionary")
            
            req_fields = ["requirement", "classification", "evidence", "source_location", "confidence"]
            for field in req_fields:
                if field not in req:
                    raise ValidationError(f"Requirement {i} missing field: {field}")
            
            # Validate classification is one of allowed values
            allowed_classifications = {"direct_match", "adjacent_experience", "gap", "blocker"}
            if req["classification"] not in allowed_classifications:
                raise ValidationError(
                    f"Invalid classification in requirement {i}: {req['classification']}. "
                    f"Must be one of {allowed_classifications}"
                )
            
            # Validate confidence is a number between 0 and 1
            confidence = req.get("confidence")
            if not isinstance(confidence, (int, float)):
                raise ValidationError(f"Confidence in requirement {i} must be a number")
            if not 0.0 <= confidence <= 1.0:
                raise ValidationError(f"Confidence in requirement {i} must be between 0.0 and 1.0")
        
        # Validate fit_score is a number between 0 and 100
        fit_score = data.get("fit_score")
        if not isinstance(fit_score, (int, float)):
            raise ValidationError("fit_score must be a number")
        if not 0.0 <= fit_score <= 100.0:
            raise ValidationError("fit_score must be between 0.0 and 100.0")
        
        # Validate gaps and blockers are lists
        gaps = data.get("gaps", [])
        if not isinstance(gaps, list):
            raise ValidationError("gaps must be a list")
        
        blockers = data.get("blockers", [])
        if not isinstance(blockers, list):
            raise ValidationError("blockers must be a list")
