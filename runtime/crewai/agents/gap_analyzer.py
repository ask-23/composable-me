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
        
        # Gap Analyzer output can be nested under 'gap_analysis' key or flat
        # Extract the analysis data
        if "gap_analysis" in data:
            analysis = data["gap_analysis"]
        else:
            analysis = data
        
        # Validate requirements exists (can be in different locations)
        requirements = None
        if "requirements" in analysis:
            requirements = analysis["requirements"]
        elif "requirements_analysis" in analysis:
            # Some prompts use requirements_analysis
            req_analysis = analysis["requirements_analysis"]
            if isinstance(req_analysis, dict):
                # Extract requirements from nested structure
                requirements = []
                for key in ["explicit_required", "explicit_preferred", "implicit_requirements"]:
                    if key in req_analysis:
                        items = req_analysis[key]
                        if isinstance(items, list):
                            requirements.extend(items)
        
        if requirements is None:
            raise ValidationError("Missing required field: requirements (or requirements_analysis)")
        
        # Validate requirements is a list
        requirements = requirements if isinstance(requirements, list) else []
        if not isinstance(requirements, list):
            raise ValidationError("requirements must be a list")
        
        # Validate each requirement is a dictionary (be lenient about field names)
        for i, req in enumerate(requirements):
            if not isinstance(req, dict):
                raise ValidationError(f"Requirement {i} must be a dictionary")
            
            # Check for classification field (required)
            if "classification" in req:
                # Validate classification is one of allowed values
                allowed_classifications = {"direct_match", "adjacent_experience", "adjacent", "gap", "blocker"}
                if req["classification"] not in allowed_classifications:
                    raise ValidationError(
                        f"Invalid classification in requirement {i}: {req['classification']}. "
                        f"Must be one of {allowed_classifications}"
                    )
            
            # Validate confidence if present
            if "confidence" in req:
                confidence = req["confidence"]
                # Handle string confidence like "high", "medium", "low"
                if isinstance(confidence, str):
                    continue  # Allow string confidence values
                if isinstance(confidence, (int, float)):
                    if not 0.0 <= confidence <= 1.0:
                        raise ValidationError(f"Confidence in requirement {i} must be between 0.0 and 1.0")
        
        # Validate fit_score (can be in different locations) - be lenient
        fit_score = analysis.get("fit_score")
        if fit_score is None and "summary" in analysis:
            # Try to extract from summary
            summary = analysis["summary"]
            if isinstance(summary, dict) and "fit_score" in summary:
                fit_score = summary["fit_score"]
        
        if fit_score is not None:
            # Try to convert to number if it's a string
            if isinstance(fit_score, str):
                # Handle percentage strings like "92%"
                if fit_score.endswith("%"):
                    try:
                        fit_score = float(fit_score.rstrip("%"))
                    except ValueError:
                        pass  # Ignore invalid format
                else:
                    try:
                        fit_score = float(fit_score)
                    except ValueError:
                        pass  # Ignore invalid format
            
            # Only validate if it's a number
            if isinstance(fit_score, (int, float)):
                if not 0.0 <= fit_score <= 100.0:
                    # Clamp to valid range instead of failing
                    fit_score = max(0.0, min(100.0, fit_score))
        
        # Gaps and blockers are optional - don't fail if missing
        # They might be embedded in the requirements list
