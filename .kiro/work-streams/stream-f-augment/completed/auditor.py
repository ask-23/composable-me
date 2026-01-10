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
        result = self.execute_with_retry(task_description, context)
        
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
        
        # Required top-level fields
        required_fields = [
            "audit_report",
            "summary",
            "truth_audit",
            "tone_audit", 
            "ats_audit",
            "compliance_audit",
            "action_required",
            "approval"
        ]
        
        for field in required_fields:
            if field not in output:
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate audit_report structure
        audit_report = output["audit_report"]
        required_audit_fields = ["meta", "summary"]
        for field in required_audit_fields:
            if field not in audit_report:
                raise ValidationError(f"Missing required audit_report field: {field}")
        
        # Validate summary fields
        summary = output["summary"]
        required_summary_fields = ["overall_status", "blocking_issues", "warnings", "recommendations"]
        for field in required_summary_fields:
            if field not in summary:
                raise ValidationError(f"Missing required summary field: {field}")
        
        # Validate overall_status is valid
        valid_statuses = ["PASS", "FAIL", "CONDITIONAL"]
        if summary["overall_status"] not in valid_statuses:
            raise ValidationError(f"overall_status must be one of: {valid_statuses}")
        
        # Validate numeric fields
        numeric_fields = ["blocking_issues", "warnings", "recommendations"]
        for field in numeric_fields:
            if not isinstance(summary[field], int) or summary[field] < 0:
                raise ValidationError(f"{field} must be a non-negative integer")
        
        # Validate individual audit sections
        audit_sections = ["truth_audit", "tone_audit", "ats_audit", "compliance_audit"]
        for section in audit_sections:
            audit_section = output[section]
            if "status" not in audit_section:
                raise ValidationError(f"Missing status in {section}")
            if audit_section["status"] not in valid_statuses:
                raise ValidationError(f"{section}.status must be one of: {valid_statuses}")
        
        # Validate action_required structure
        action_required = output["action_required"]
        required_action_fields = ["blocking", "recommended", "optional"]
        for field in required_action_fields:
            if field not in action_required:
                raise ValidationError(f"Missing required action_required field: {field}")
            if not isinstance(action_required[field], list):
                raise ValidationError(f"action_required.{field} must be a list")
        
        # Validate approval structure
        approval = output["approval"]
        required_approval_fields = ["approved", "reason"]
        for field in required_approval_fields:
            if field not in approval:
                raise ValidationError(f"Missing required approval field: {field}")
        
        if not isinstance(approval["approved"], bool):
            raise ValidationError("approval.approved must be a boolean")
        if not isinstance(approval["reason"], str):
            raise ValidationError("approval.reason must be a string")
