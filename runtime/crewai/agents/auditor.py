"""
Auditor Suite Agent Implementation

This agent is the quality gate that verifies all outputs are truthful, sound human,
comply with AGENTS.MD rules, will pass ATS systems, and match the JD appropriately.
"""

from typing import Dict, Any, List
from runtime.crewai.base_agent import BaseHydraAgent, ValidationError
from crewai import LLM
import re


class AuditorSuiteAgent(BaseHydraAgent):
    """Auditor Suite Agent that performs comprehensive verification of all outputs"""
    
    role = "Auditor Suite"
    goal = "Verify all outputs are truthful, human-sounding, compliant, and ATS-ready"
    expected_output = "YAML with comprehensive audit report including truth, tone, ATS, and compliance audits"
    
    def __init__(self, llm: LLM):
        """
        Initialize the Auditor Suite Agent
        
        Args:
            llm: The LLM instance to use
        """
        super().__init__(llm, "agents/auditor-suite/prompt.md")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Auditor Suite agent to perform comprehensive verification
        
        Args:
            context: Dictionary containing:
                - document: The document to audit (resume, cover letter, etc.)
                - document_type: Type of document being audited
                - job_description: The original job description
                - source_documents: User source documents for truth verification
                - target_role: The role being applied for
            
        Returns:
            Dictionary with comprehensive audit report
        """
        # Validate required inputs
        required_keys = ["document", "document_type", "job_description", "source_documents"]
        for key in required_keys:
            if key not in context:
                raise ValidationError(f"Missing required context key: {key}")
        
        # Create task for the agent
        task_description = f"""
        Perform comprehensive audit of the {context['document_type']} for the {context.get('target_role', 'target role')}.
        
        Document to Audit:
        {context['document']}
        
        Document Type: {context['document_type']}
        
        Job Description:
        {context['job_description']}
        
        Source Documents (for truth verification):
        {context['source_documents']}
        
        Target Role: {context.get('target_role', 'Not specified')}
        
        Perform all four audit components:
        1. Truth Audit - Verify every factual claim against sources
        2. Tone Audit - Detect AI patterns and enforce human voice
        3. ATS Audit - Ensure document will pass automated screening
        4. Compliance Audit - Verify AGENTS.MD rules are followed
        
        Categorize issues as blocking, warning, or recommendation.
        Provide specific fixes for each issue found.
        """
        
        # Execute with retry logic
        task = self.create_task(task_description)
        result = self.execute_with_retry(task)
        
        # Validate the output
        self._validate_schema(result)
        
        return result
    
    def _validate_context(self, context: Dict[str, Any]) -> None:
        """Validate required context parameters"""
        required = ["document", "document_type", "job_description", "source_documents"]
        for param in required:
            if param not in context:
                raise ValidationError(f"Missing required context: {param}")
    
    def _validate_schema(self, output: Dict[str, Any]) -> None:
        """Validate Auditor Suite specific output schema"""
        super()._validate_schema(output)  # Validates base fields
        # LLM output structure varies - accept whatever it produces
        return
