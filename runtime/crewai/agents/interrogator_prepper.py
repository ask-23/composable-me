"""
Interrogator-Prepper Agent Implementation

This agent generates targeted interview questions to fill gaps in candidate experience
and extracts truthful details using STAR+ format (Situation, Task, Actions, Results, Proof).
"""

from typing import Dict, Any, List
from runtime.crewai.base_agent import BaseHydraAgent, ValidationError
from crewai import LLM


class InterrogatorPrepperAgent(BaseHydraAgent):
    """Interrogator-Prepper Agent that generates targeted interview questions"""
    
    role = "Interrogator-Prepper"
    goal = "Generate targeted interview questions to extract truthful details and fill experience gaps"
    expected_output = "YAML with structured questions and interview notes processing"
    
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
        {context['job_description']}
        
        Candidate Resume:
        {context['resume']}
        
        Identified Gaps:
        {context['gaps']}
        
        Gap Analysis:
        {context['gap_analysis']}
        
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
        # First run base validation
        super()._validate_schema(data)
        
        # Validate required fields for Interrogator-Prepper
        required_fields = ["questions", "interview_notes"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate questions is a list
        questions = data.get("questions", [])
        if not isinstance(questions, list):
            raise ValidationError("questions must be a list")
        
        # Validate question count (8-12 questions)
        if not 8 <= len(questions) <= 12:
            raise ValidationError(f"Must have 8-12 questions, got {len(questions)}")
        
        # Validate each question has required fields
        allowed_themes = {"technical", "leadership", "outcomes", "tools"}
        for i, question in enumerate(questions):
            if not isinstance(question, dict):
                raise ValidationError(f"Question {i} must be a dictionary")
            
            question_fields = ["id", "theme", "question", "format", "target_gap", "why_asking"]
            for field in question_fields:
                if field not in question:
                    raise ValidationError(f"Question {i} missing field: {field}")
            
            # Validate theme is one of allowed values
            if question["theme"] not in allowed_themes:
                raise ValidationError(
                    f"Invalid theme in question {i}: {question['theme']}. "
                    f"Must be one of {allowed_themes}"
                )
            
            # Validate format is STAR+
            if question["format"] != "STAR+":
                raise ValidationError(f"Question {i} format must be 'STAR+', got '{question['format']}'")
        
        # Validate interview_notes is a list
        interview_notes = data.get("interview_notes", [])
        if not isinstance(interview_notes, list):
            raise ValidationError("interview_notes must be a list")
        
        # Validate each interview note has required fields (if any notes exist)
        for i, note in enumerate(interview_notes):
            if not isinstance(note, dict):
                raise ValidationError(f"Interview note {i} must be a dictionary")
            
            note_fields = ["question_id", "answer", "verified", "source_material"]
            for field in note_fields:
                if field not in note:
                    raise ValidationError(f"Interview note {i} missing field: {field}")
            
            # Validate verified and source_material are booleans
            if not isinstance(note["verified"], bool):
                raise ValidationError(f"Interview note {i} 'verified' must be a boolean")
            if not isinstance(note["source_material"], bool):
                raise ValidationError(f"Interview note {i} 'source_material' must be a boolean")
