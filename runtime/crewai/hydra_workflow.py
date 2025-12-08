"""
HydraWorkflow - Orchestrates the complete Composable Me pipeline

This workflow coordinates all agents in the proper sequence:
1. Gap Analyzer - Maps requirements to experience
2. Interrogator-Prepper - Generates STAR+ questions  
3. Differentiator - Identifies unique value propositions
4. Tailoring Agent - Creates tailored resume and cover letter
5. ATS Optimizer - Optimizes for automated screening
6. Auditor Suite - Comprehensive verification (with retry loop)

Includes state machine transitions, error recovery, and audit retry logic.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import logging
from crewai import LLM

from runtime.crewai.agents.gap_analyzer import GapAnalyzerAgent
from runtime.crewai.agents.interrogator_prepper import InterrogatorPrepperAgent
from runtime.crewai.agents.differentiator import DifferentiatorAgent
from runtime.crewai.agents.tailoring_agent import TailoringAgent
from runtime.crewai.agents.ats_optimizer import ATSOptimizerAgent
from runtime.crewai.agents.auditor import AuditorSuiteAgent
from runtime.crewai.base_agent import ValidationError


class WorkflowState(Enum):
    """Workflow execution states"""
    INITIALIZED = "initialized"
    GAP_ANALYSIS = "gap_analysis"
    INTERROGATION = "interrogation"
    DIFFERENTIATION = "differentiation"
    TAILORING = "tailoring"
    ATS_OPTIMIZATION = "ats_optimization"
    AUDITING = "auditing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowResult:
    """Result of workflow execution"""
    state: WorkflowState
    success: bool
    final_documents: Optional[Dict[str, Any]] = None
    audit_report: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_log: List[str] = None


class HydraWorkflow:
    """Orchestrates the complete Composable Me agent pipeline"""
    
    def __init__(self, llm: LLM, max_audit_retries: int = 2):
        """
        Initialize the workflow with all agents
        
        Args:
            llm: The LLM instance to use for all agents
            max_audit_retries: Maximum number of audit retry attempts
        """
        self.llm = llm
        self.max_audit_retries = max_audit_retries
        self.logger = logging.getLogger(__name__)
        
        # Initialize all agents
        self.gap_analyzer = GapAnalyzerAgent(llm)
        self.interrogator_prepper = InterrogatorPrepperAgent(llm)
        self.differentiator = DifferentiatorAgent(llm)
        self.tailoring_agent = TailoringAgent(llm)
        self.ats_optimizer = ATSOptimizerAgent(llm)
        self.auditor_suite = AuditorSuiteAgent(llm)
        
        # Workflow state
        self.current_state = WorkflowState.INITIALIZED
        self.execution_log = []
        self.intermediate_results = {}
    
    def execute(self, context: Dict[str, Any]) -> WorkflowResult:
        """
        Execute the complete workflow pipeline
        
        Args:
            context: Dictionary containing:
                - job_description: The job description text
                - resume: The candidate's resume text
                - source_documents: User source documents for verification
                - target_role: The role being applied for
                - research_data: Optional research data
            
        Returns:
            WorkflowResult with final documents and audit report
        """
        try:
            self._log("Starting HydraWorkflow execution")
            self._validate_input_context(context)
            
            # Execute pipeline stages
            gap_result = self._execute_gap_analysis(context)
            interrogation_result = self._execute_interrogation(context, gap_result)
            differentiation_result = self._execute_differentiation(context, gap_result)
            tailoring_result = self._execute_tailoring(context, gap_result, interrogation_result, differentiation_result)
            ats_result = self._execute_ats_optimization(context, tailoring_result)
            
            # Execute audit with retry loop
            final_result = self._execute_audit_with_retry(context, ats_result)
            
            self.current_state = WorkflowState.COMPLETED
            self._log("HydraWorkflow execution completed successfully")
            
            return WorkflowResult(
                state=self.current_state,
                success=True,
                final_documents=final_result.get("final_documents"),
                audit_report=final_result.get("audit_report"),
                execution_log=self.execution_log.copy()
            )
            
        except Exception as e:
            self.current_state = WorkflowState.FAILED
            error_msg = f"Workflow execution failed: {str(e)}"
            self._log(error_msg)
            
            return WorkflowResult(
                state=self.current_state,
                success=False,
                error_message=error_msg,
                execution_log=self.execution_log.copy()
            )
    
    def _validate_input_context(self, context: Dict[str, Any]) -> None:
        """Validate required input context"""
        required_keys = ["job_description", "resume", "source_documents"]
        for key in required_keys:
            if key not in context:
                raise ValidationError(f"Missing required context key: {key}")
    
    def _execute_gap_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute gap analysis stage"""
        self.current_state = WorkflowState.GAP_ANALYSIS
        self._log("Executing Gap Analysis")
        
        result = self.gap_analyzer.execute(context)
        self.intermediate_results["gap_analysis"] = result
        return result
    
    def _execute_interrogation(self, context: Dict[str, Any], gap_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute interrogation preparation stage"""
        self.current_state = WorkflowState.INTERROGATION
        self._log("Executing Interrogation Preparation")

        # Extract gaps from gap_result for interrogation context
        # Handle both flat and nested structures
        gaps = []
        if "gaps" in gap_result:
            gaps = gap_result["gaps"]
        elif "gap_analysis" in gap_result:
            analysis = gap_result["gap_analysis"]
            if "gaps" in analysis:
                gaps = analysis["gaps"]
            # Also extract requirements classified as gaps
            if "requirements" in analysis:
                for req in analysis["requirements"]:
                    if isinstance(req, dict) and req.get("classification") == "gap":
                        gaps.append(req)
        
        interrogation_context = {
            **context,
            "gap_analysis": gap_result,
            "gaps": gaps if gaps else []  # Provide empty list if no gaps found
        }
        result = self.interrogator_prepper.execute(interrogation_context)
        self.intermediate_results["interrogation"] = result
        return result

    def _execute_differentiation(self, context: Dict[str, Any], gap_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute differentiation stage"""
        self.current_state = WorkflowState.DIFFERENTIATION
        self._log("Executing Differentiation")

        differentiation_context = {**context, "gap_analysis": gap_result}
        result = self.differentiator.execute(differentiation_context)
        self.intermediate_results["differentiation"] = result
        return result

    def _execute_tailoring(self, context: Dict[str, Any], gap_result: Dict[str, Any],
                          interrogation_result: Dict[str, Any], differentiation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tailoring stage"""
        self.current_state = WorkflowState.TAILORING
        self._log("Executing Tailoring")

        tailoring_context = {
            **context,
            "gap_analysis": gap_result,
            "interrogation_prep": interrogation_result,
            "differentiation": differentiation_result
        }
        result = self.tailoring_agent.execute(tailoring_context)
        self.intermediate_results["tailoring"] = result
        return result

    def _execute_ats_optimization(self, context: Dict[str, Any], tailoring_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ATS optimization stage"""
        self.current_state = WorkflowState.ATS_OPTIMIZATION
        self._log("Executing ATS Optimization")

        ats_context = {
            **context,
            "tailored_resume": tailoring_result.get("tailored_resume", ""),
            "tailored_cover_letter": tailoring_result.get("tailored_cover_letter", "")
        }
        result = self.ats_optimizer.execute(ats_context)
        self.intermediate_results["ats_optimization"] = result
        return result

    def _execute_audit_with_retry(self, context: Dict[str, Any], ats_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute audit with retry logic (maximum 2 retries)"""
        self.current_state = WorkflowState.AUDITING
        self._log("Executing Audit with Retry Logic")

        retry_count = 0
        current_documents = {
            "resume": ats_result.get("optimized_resume", ""),
            "cover_letter": ats_result.get("optimized_cover_letter", "")
        }

        while retry_count <= self.max_audit_retries:
            try:
                # Audit the resume
                resume_audit_context = {
                    **context,
                    "document": current_documents["resume"],
                    "document_type": "resume"
                }
                resume_audit = self.auditor_suite.execute(resume_audit_context)

                # Audit the cover letter if present
                cover_letter_audit = None
                if current_documents["cover_letter"]:
                    cover_letter_audit_context = {
                        **context,
                        "document": current_documents["cover_letter"],
                        "document_type": "cover_letter"
                    }
                    cover_letter_audit = self.auditor_suite.execute(cover_letter_audit_context)

                # Check if audit passed
                resume_approved = resume_audit.get("approval", {}).get("approved", False)
                cover_letter_approved = True  # Default to true if no cover letter
                if cover_letter_audit:
                    cover_letter_approved = cover_letter_audit.get("approval", {}).get("approved", False)

                if resume_approved and cover_letter_approved:
                    self._log(f"Audit passed on attempt {retry_count + 1}")
                    return {
                        "final_documents": current_documents,
                        "audit_report": {
                            "resume_audit": resume_audit,
                            "cover_letter_audit": cover_letter_audit,
                            "final_status": "APPROVED",
                            "retry_count": retry_count
                        }
                    }

                # If audit failed and we have retries left
                if retry_count < self.max_audit_retries:
                    retry_count += 1
                    self._log(f"Audit failed, attempting retry {retry_count}/{self.max_audit_retries}")

                    # Apply fixes from audit recommendations
                    current_documents = self._apply_audit_fixes(current_documents, resume_audit, cover_letter_audit)
                else:
                    # Max retries reached
                    self._log("Max audit retries reached, workflow failed")
                    raise ValidationError("Document failed audit after maximum retries")

            except Exception as e:
                if retry_count < self.max_audit_retries:
                    retry_count += 1
                    self._log(f"Audit error: {str(e)}, attempting retry {retry_count}/{self.max_audit_retries}")
                else:
                    raise e

        # Should not reach here, but safety fallback
        raise ValidationError("Audit retry loop exceeded maximum attempts")

    def _apply_audit_fixes(self, documents: Dict[str, str], resume_audit: Dict[str, Any],
                          cover_letter_audit: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Apply audit fixes to documents (simplified implementation)"""
        self._log("Applying audit fixes to documents")

        # In a real implementation, this would parse the audit recommendations
        # and apply specific fixes. For now, we'll return the documents unchanged
        # as the actual fix application would require more complex logic.

        return documents

    def _log(self, message: str) -> None:
        """Log message to both logger and execution log"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}"
        self.logger.info(log_entry)
        self.execution_log.append(log_entry)

    def get_current_state(self) -> WorkflowState:
        """Get current workflow state"""
        return self.current_state

    def get_execution_log(self) -> List[str]:
        """Get execution log"""
        return self.execution_log.copy()

    def get_intermediate_results(self) -> Dict[str, Any]:
        """Get intermediate results from all stages"""
        import copy
        return copy.deepcopy(self.intermediate_results)
