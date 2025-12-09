"""
Commander Agent Implementation

This agent consumes inputs (JD, resume, optional research) and the output of the 
Gap Analyzer to produce:
  - action: "proceed" | "pass" | "discuss"
  - fit_analysis: including auto-rejects and fit percentage
  - next_step: recommended next action
"""

from typing import Dict, Any, List
from runtime.crewai.base_agent import BaseHydraAgent, ValidationError
from crewai import LLM


class CommanderAgent(BaseHydraAgent):
    """Commander Agent that evaluates job fit and makes strategic decisions"""
    
    role = "Commander"
    goal = "Evaluate job fit and make strategic decisions about proceeding with applications"
    expected_output = "JSON decision with action, fit analysis, and next step"
    
    def __init__(self, llm: LLM):
        """
        Initialize the Commander Agent
        
        Args:
            llm: The LLM instance to use
        """
        super().__init__(llm, "agents/commander/prompt.md")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Commander agent to evaluate job fit
        
        Args:
            context: Dictionary containing:
                - job_description: The job description text
                - resume: The candidate's resume text
                - research_data: Optional research data
                - gap_analysis: Output from Gap Analyzer
            
        Returns:
            Dictionary with action, fit_analysis, and next_step
        """
        # Validate required inputs
        required_keys = ["job_description", "resume", "gap_analysis"]
        for key in required_keys:
            if key not in context:
                raise ValidationError(f"Missing required context key: {key}")
        
        # Create the task for the agent
        task_description = f"""
        Evaluate the job opportunity based on the provided inputs and Gap Analyzer output.
        
        Job Description:
        {context['job_description']}
        
        Candidate Resume:
        {context['resume']}
        
        Research Data:
        {context.get('research_data', 'Not provided')}
        
        Gap Analyzer Output:
        {context['gap_analysis']}
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
        
        # Validate required fields for Commander
        required_fields = ["action", "fit_analysis", "next_step"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate action is one of the allowed values
        allowed_actions = {"proceed", "pass", "discuss"}
        if data["action"] not in allowed_actions:
            raise ValidationError(
                f"Invalid action: {data['action']}. Must be one of {allowed_actions}"
            )
        
        # Validate fit_analysis structure
        fit_analysis = data.get("fit_analysis", {})
        if not isinstance(fit_analysis, dict):
            raise ValidationError("fit_analysis must be a dictionary")
        
        # Check required fit_analysis fields
        fit_required = ["fit_percentage", "auto_reject_triggered", "red_flags"]
        for field in fit_required:
            if field not in fit_analysis:
                raise ValidationError(f"Missing fit_analysis field: {field}")
        
        # Validate fit_percentage is a number between 0 and 100
        fit_percentage = fit_analysis.get("fit_percentage")
        if not isinstance(fit_percentage, (int, float)):
            raise ValidationError("fit_percentage must be a number")
        if not 0 <= fit_percentage <= 100:
            raise ValidationError("fit_percentage must be between 0 and 100")
        
        # Validate auto_reject_triggered is boolean
        auto_reject = fit_analysis.get("auto_reject_triggered")
        if not isinstance(auto_reject, bool):
            raise ValidationError("auto_reject_triggered must be a boolean")
        
        # Validate red_flags is a list
        red_flags = fit_analysis.get("red_flags")
        if not isinstance(red_flags, list):
            raise ValidationError("red_flags must be a list")
        
        # Validate next_step is a string
        next_step = data.get("next_step")
        if not isinstance(next_step, str):
            raise ValidationError("next_step must be a string")

    def _compute_fit_percentage(self, gap_output: Dict[str, Any]) -> float:
        """
        Compute fit percentage based on Gap Analyzer output
        
        Args:
            gap_output: Output from Gap Analyzer
            
        Returns:
            Fit percentage as a float between 0 and 100
        """
        # Extract requirements and classifications
        requirements = gap_output.get("requirements", [])
        if not requirements:
            return 0.0
        
        # Count classifications
        direct_matches = 0
        adjacent = 0
        gaps = 0
        blockers = 0
        
        for req in requirements:
            classification = req.get("classification", "")
            if classification == "direct_match":
                direct_matches += 1
            elif classification == "adjacent_experience":
                adjacent += 1
            elif classification == "gap":
                gaps += 1
            elif classification == "blocker":
                blockers += 1
        
        total = len(requirements)
        if total == 0:
            return 0.0
        
        # Calculate weighted score
        # Direct matches: full credit
        # Adjacent: partial credit (0.7 weight)
        # Gaps: penalty (-0.5 weight)
        # Blockers: heavy penalty (-1.0 weight)
        score = (
            (direct_matches * 1.0) +
            (adjacent * 0.7) +
            (gaps * -0.5) +
            (blockers * -1.0)
        )
        
        # Convert to percentage (0-100 scale)
        max_possible = total * 1.0  # All direct matches
        if max_possible == 0:
            return 0.0
            
        percentage = (score / max_possible) * 100
        
        # Clamp to 0-100 range
        return max(0.0, min(100.0, percentage))
    
    def _check_auto_reject(self, job_description: str) -> List[str]:
        """
        Check for auto-reject criteria in job description
        
        Args:
            job_description: The job description text
            
        Returns:
            List of auto-reject reasons found
        """
        reasons = []
        job_desc_lower = job_description.lower()
        
        # Check for contract-to-hire
        cth_indicators = [
            "contract to hire",
            "contract-to-hire",
            "cth",
            "contract perm",
            "temp to perm"
        ]
        if any(indicator in job_desc_lower for indicator in cth_indicators):
            reasons.append("Contract-to-hire position detected")
        
        # Check for missing compensation
        comp_indicators = [
            "compensation",
            "salary",
            "pay",
            "rate",
            "benefits"
        ]
        # If none of the compensation indicators are found, it might be missing
        if not any(indicator in job_desc_lower for indicator in comp_indicators):
            reasons.append("No compensation information provided")
        
        # Additional auto-reject criteria can be added here
        
        return reasons
    
    def _generate_red_flags(self, job_description: str, research_data: Dict[str, Any]) -> List[str]:
        """
        Generate red flags based on job description and research data
        
        Args:
            job_description: The job description text
            research_data: Research data about the company
            
        Returns:
            List of red flags identified
        """
        red_flags = []
        job_desc_lower = job_description.lower()
        
        # Check for vague job descriptions
        vague_indicators = [
            "assorted projects",
            "various tasks",
            "general duties",
            "day to day",
            "ongoing support"
        ]
        if any(indicator in job_desc_lower for indicator in vague_indicators):
            red_flags.append("Vague job description with unclear responsibilities")
        
        # Check research data for red flags
        if research_data:
            research_flags = research_data.get("red_flags", [])
            red_flags.extend(research_flags)
        
        return red_flags