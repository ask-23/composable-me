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

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from crewai import LLM

from runtime.crewai.agents.ats_optimizer import ATSOptimizerAgent
from runtime.crewai.agents.auditor import AuditorSuiteAgent
from runtime.crewai.agents.differentiator import DifferentiatorAgent
from runtime.crewai.agents.executive_synthesizer import ExecutiveSynthesizerAgent
from runtime.crewai.agents.gap_analyzer import GapAnalyzerAgent
from runtime.crewai.agents.interrogator_prepper import InterrogatorPrepperAgent
from runtime.crewai.agents.tailoring_agent import TailoringAgent
from runtime.crewai.base_agent import BaseHydraAgent, ValidationError
from runtime.crewai.contracts import (
    ATSResult,
    AuditVerdict,
    ExecutiveDecision,
    GapAnalysis,
    TailoredDocuments,
)
from runtime.crewai.model_config import LLMClientError, get_agent_model_info, get_llm_for_agent
from runtime.crewai.telemetry import trace_workflow_stage


class WorkflowState(Enum):
    """Workflow execution states"""

    INITIALIZED = "initialized"
    GAP_ANALYSIS = "gap_analysis"
    GAP_ANALYSIS_REVIEW = "gap_analysis_review"  # Pause state
    INTERROGATION = "interrogation"
    INTERROGATION_REVIEW = "interrogation_review"  # Pause state
    DIFFERENTIATION = "differentiation"
    TAILORING = "tailoring"
    ATS_OPTIMIZATION = "ats_optimization"
    AUDITING = "auditing"
    EXECUTIVE_SYNTHESIS = "executive_synthesis"
    COMPLETED = "completed"
    FAILED = "failed"


class RunStatus(str, Enum):
    """Explicit outcome of a run.

    ``success`` (below) only means "documents were produced". ``RunStatus`` carries
    the real outcome so callers (CLI exit codes, the web UI) don't have to re-derive
    it from a scatter of boolean fields.
    """

    COMPLETED = "completed"  # documents produced and audit passed
    COMPLETED_WITH_AUDIT_CONCERNS = "completed_with_audit_concerns"  # produced, audit rejected
    AUDIT_ERROR = "audit_error"  # produced, but the audit stage errored
    PAUSED = "paused"  # waiting for human input (HITL)
    FAILED = "failed"  # a pre-audit stage failed; no documents


@dataclass
class WorkflowResult:
    """Result of workflow execution"""

    state: WorkflowState
    success: bool
    status: RunStatus = RunStatus.COMPLETED
    final_documents: Optional[Dict[str, Any]] = None
    audit_report: Optional[Dict[str, Any]] = None
    executive_brief: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_log: List[str] = None
    intermediate_results: Optional[Dict[str, Any]] = None
    audit_failed: bool = False
    audit_error: Optional[str] = None
    agent_models: Optional[Dict[str, str]] = None


class UserInteraction:
    """Helper for Human-in-the-Loop interactions"""

    @staticmethod
    def ask_yes_no(question: str) -> bool:
        """Ask a yes/no question via console"""
        try:
            while True:
                response = input(f"\n❓ {question} (y/n): ").lower().strip()
                if response in ["y", "yes"]:
                    return True
                if response in ["n", "no"]:
                    return False
        except EOFError:
            return True  # Default to yes in non-interactive environments

    @staticmethod
    def conduct_interview(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Conduct an interactive interview based on generated questions"""
        print("\n🎤 STARTING INTERVIEW SESSION")
        print("=" * 50)
        print("The agent has identified some gaps or areas needing detail.")
        print("Please answer the following questions to help tailor your resume.")
        print("=" * 50)

        answers = []
        try:
            for i, q in enumerate(questions):
                q_text = q.get("question", "Unknown Question")
                print(f"\n[{i + 1}/{len(questions)}] {q_text}")
                answer = input("   Your Answer > ").strip()
                if answer:
                    answers.append(
                        {
                            "question_id": q.get("id"),
                            "question_text": q_text,
                            "answer": answer,
                            "verified": True,
                            "source_material": True,
                        }
                    )
        except EOFError:
            print("\n⚠️ Input stream closed, skipping remaining questions.")

        print("\n✅ Interview complete! Proceeding with these details...")
        return answers


class WorkflowPaused(Exception):
    """Raised when workflow needs to pause for user input"""

    def __init__(self, state: WorkflowState, message: str):
        self.state = state
        self.message = message
        super().__init__(message)


class HydraWorkflow:
    """Orchestrates the complete Composable Me agent pipeline"""

    def __init__(
        self,
        llm: LLM = None,
        max_audit_retries: int = 2,
        use_per_agent_models: bool = True,
        interactive: bool = False,
        auto_approve: bool = False,
    ):
        """
        Initialize the workflow with all agents

        Args:
            llm: Optional fallback LLM instance (used if per-agent models fail)
            max_audit_retries: Maximum number of audit retry attempts
            use_per_agent_models: If True, use optimized models per agent
            interactive: If True, enables Human-in-the-Loop features
            auto_approve: If True, proceed past the human gates without pausing
                (used by the non-interactive CLI, which has no way to resume a pause).
                The async web flow leaves this False so it can pause for real HITL.
        """
        self.fallback_llm = llm
        self.max_audit_retries = max_audit_retries
        self.use_per_agent_models = use_per_agent_models
        self.interactive = interactive
        self.auto_approve = auto_approve
        self.logger = logging.getLogger(__name__)

        # Initialize agents with per-agent model assignments
        self.agent_models = {}

        # Gap Analyzer - DeepSeek V3 TEE (Chutes) or fallback
        gap_llm = self._get_agent_llm("gap_analyzer")
        self.gap_analyzer = GapAnalyzerAgent(gap_llm)

        # Interrogator - Llama 3.3 (Together)
        interrogator_llm = self._get_agent_llm("interrogator_prepper")
        self.interrogator_prepper = InterrogatorPrepperAgent(interrogator_llm)

        # Differentiator - Claude Sonnet 4 (Anthropic)
        differentiator_llm = self._get_agent_llm("differentiator")
        self.differentiator = DifferentiatorAgent(differentiator_llm)

        # Tailoring Agent - Claude Sonnet 4 (Anthropic)
        tailoring_llm = self._get_agent_llm("tailoring_agent")
        self.tailoring_agent = TailoringAgent(tailoring_llm)

        # ATS Optimizer - Llama 3.3 (Together)
        ats_llm = self._get_agent_llm("ats_optimizer")
        self.ats_optimizer = ATSOptimizerAgent(ats_llm)

        # Auditor Suite - DeepSeek R1 TEE (Chutes) or fallback
        auditor_llm = self._get_agent_llm("auditor_suite")
        self.auditor_suite = AuditorSuiteAgent(auditor_llm)

        # Executive Synthesizer - Claude Sonnet/Opus (Anthropic)
        exec_llm = self._get_agent_llm("executive_synthesizer")
        self.executive_synthesizer = ExecutiveSynthesizerAgent(exec_llm)

        # Workflow state
        self.current_state = WorkflowState.INITIALIZED
        self.execution_log = []
        self.intermediate_results = {}

    def _get_agent_llm(self, agent_type: str) -> Optional[LLM]:
        """Resolve the LLM for an agent, or None if no provider key is available.

        Returning None (rather than raising) lets the workflow be *constructed*
        without any API keys — useful for tests, tooling, and input validation that
        never reaches a model call. A run that actually invokes an agent with no LLM
        fails at that stage via ``_execute_with_fallback`` and is reported as FAILED.
        """
        if self.use_per_agent_models:
            try:
                llm = get_llm_for_agent(agent_type)
                model_info = get_agent_model_info(agent_type)
                self.agent_models[agent_type] = model_info.get("model", "unknown")
                self.logger.info(f"Agent '{agent_type}' using model: {model_info.get('model')}")
                return llm
            except LLMClientError as e:
                self.logger.warning(f"Per-agent model failed for '{agent_type}': {e}")

        # Use fallback
        if self.fallback_llm:
            self.agent_models[agent_type] = getattr(self.fallback_llm, "model", "fallback")
            return self.fallback_llm

        # Try to get any working model
        try:
            llm = get_llm_for_agent(agent_type, fallback_only=True)
            self.agent_models[agent_type] = "fallback"
            return llm
        except LLMClientError:
            self.logger.warning(f"No LLM available for agent '{agent_type}' (deferred to run time)")
            self.agent_models[agent_type] = "unavailable"
            return None

    def _execute_with_fallback(
        self, agent: BaseHydraAgent, context: Dict[str, Any], stage_name: str
    ) -> Dict[str, Any]:
        """Execute agent with automatic fallback to secondary model on failure."""
        # An agent constructed without a resolvable LLM (no provider key) must not
        # silently run on CrewAI's default OpenAI model: use the fallback if we have
        # one, otherwise fail loudly.
        if agent.llm is None:
            if self.fallback_llm is None:
                raise ValueError(
                    f"No LLM available for stage '{stage_name}': set a provider API key "
                    "(see .env.example) or pass a fallback LLM."
                )
            agent.llm = self.fallback_llm
            self.agent_models[stage_name] = getattr(self.fallback_llm, "model", "fallback")

        try:
            return agent.execute(context)
        except Exception as e:
            self.logger.warning(f"Stage '{stage_name}' failed with primary model: {e}")
            self._log(f"Primary model failed for {stage_name}, attempting fallback...")

            try:
                # Get fallback LLM
                if self.fallback_llm:
                    fallback = self.fallback_llm
                    model_name = getattr(fallback, "model", "fallback")
                else:
                    # Create a specific fallback for this agent
                    fallback = get_llm_for_agent(stage_name, fallback_only=True)
                    model_name = "fallback"

                # Update agent with fallback LLM
                agent.llm = fallback
                self.agent_models[stage_name] = model_name
                self._log(f"Switched {stage_name} to fallback model: {model_name}")

                # Retry execution
                return agent.execute(context)

            except Exception as fallback_error:
                self.logger.error(f"Fallback failed for {stage_name}: {fallback_error}")
                # Surface the original error; it is usually the more informative one.
                raise e from fallback_error

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
                - previous_results: Optional dict of results from previous run (for resuming)
                - resume_stage: Optional string indicating stage to resume from
                - gap_analysis_approved: Boolean (for resuming after gap analysis)
                - interview_answers: List (for resuming after interrogation)

        Returns:
            WorkflowResult. If paused, state will reflect the pause point.
        """
        try:
            self._log("Starting HydraWorkflow execution")
            self._validate_input_context(context)

            # Load previous results if resuming
            if "previous_results" in context:
                self.intermediate_results = context["previous_results"]
                self._log("Loaded intermediate results from previous run")

            # Execute pipeline stages

            # 1. GAP ANALYSIS
            if "gap_analysis" in self.intermediate_results:
                gap_result = self.intermediate_results["gap_analysis"]
                self._log("Skipping Gap Analysis (already complete)")
            else:
                gap_result = self._execute_gap_analysis(context)

            # 2. INTERROGATION
            if "interrogation" in self.intermediate_results:
                interrogation_result = self.intermediate_results["interrogation"]
                self._log("Skipping Interrogation (already complete)")
                # Check if we have answers now
                if "interview_answers" in context and context["interview_answers"]:
                    interrogation_result["interview_notes"] = context["interview_answers"]
            else:
                interrogation_result = self._execute_interrogation(context, gap_result)

            # 3. DIFFERENTIATION
            differentiation_result = self._execute_differentiation(
                context, gap_result, interrogation_result
            )

            # 4. TAILORING
            tailoring_result = self._execute_tailoring(
                context, gap_result, interrogation_result, differentiation_result
            )

            # 5. ATS OPTIMIZATION
            ats_result = self._execute_ats_optimization(context, tailoring_result)

            # 6. AUDIT
            # Execute audit with retry loop (no longer throws exceptions)
            final_result = self._execute_audit(context, ats_result)

            # 7. EXECUTIVE SYNTHESIS
            # Execute executive synthesis to create strategic brief
            executive_brief = self._execute_executive_synthesis(
                context,
                gap_result,
                interrogation_result,
                differentiation_result,
                tailoring_result,
                ats_result,
                final_result,
            )

            # Documents were produced; classify the outcome explicitly.
            audit_failed = final_result.get("audit_failed", False)
            audit_status = final_result.get("audit_report", {}).get("final_status", "UNKNOWN")
            if audit_status == "AUDIT_ERROR":
                status = RunStatus.AUDIT_ERROR
            elif audit_failed:
                status = RunStatus.COMPLETED_WITH_AUDIT_CONCERNS
            else:
                status = RunStatus.COMPLETED

            self.current_state = WorkflowState.COMPLETED
            self._log(f"HydraWorkflow finished: {status.value} (audit: {audit_status})")

            return WorkflowResult(
                state=self.current_state,
                success=True,  # Documents were generated, even if audit failed
                status=status,
                final_documents=final_result.get("final_documents"),
                audit_report=final_result.get("audit_report"),
                executive_brief=executive_brief,
                execution_log=self.execution_log.copy(),
                intermediate_results=self.get_intermediate_results(),
                audit_failed=audit_failed,
                audit_error=final_result.get("audit_error"),
                agent_models=self.agent_models,
            )

        except WorkflowPaused as e:
            self.current_state = e.state
            self._log(f"Workflow PAUSED: {e.message}")
            return WorkflowResult(
                state=self.current_state,
                success=True,  # It's a successful "pause"
                status=RunStatus.PAUSED,
                execution_log=self.execution_log.copy(),
                intermediate_results=self.get_intermediate_results(),
                error_message=e.message,  # Use error message field for pause reason
                agent_models=self.agent_models,
            )

        except Exception as e:
            self.current_state = WorkflowState.FAILED
            error_msg = f"Workflow execution failed: {str(e)}"
            self._log(error_msg)

            return WorkflowResult(
                state=self.current_state,
                success=False,
                status=RunStatus.FAILED,
                error_message=error_msg,
                execution_log=self.execution_log.copy(),
                intermediate_results=self.get_intermediate_results(),  # Include partial results on failure
                agent_models=self.agent_models,
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

        with trace_workflow_stage("gap_analysis") as span:
            result = self._execute_with_fallback(self.gap_analyzer, context, "gap_analysis")
            self.intermediate_results["gap_analysis"] = result

            # Record metrics
            gaps_count = len(result.get("gaps", []))
            span.set_attribute("stage.gaps_found", gaps_count)
            span.set_attribute("stage.confidence", result.get("confidence", 0))

            if self.interactive:
                print("\n📊 GAP ANALYSIS COMPLETE")
                # Ideally print specific gaps here, but for now just pause
                if not UserInteraction.ask_yes_no("Proceed with these findings?"):
                    self._log("User aborted after Gap Analysis")
                    raise Exception("User aborted workflow")
            elif not context.get("gap_analysis_approved", False) and not self.auto_approve:
                # Async web mode: pause for real human approval.
                span.set_attribute("stage.paused", True)
                raise WorkflowPaused(
                    WorkflowState.GAP_ANALYSIS_REVIEW, "Waiting for Gap Analysis approval"
                )

        return result

    def _execute_interrogation(
        self, context: Dict[str, Any], gap_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute interrogation preparation stage"""
        self.current_state = WorkflowState.INTERROGATION
        self._log("Executing Interrogation Preparation")

        with trace_workflow_stage("interrogation") as span:
            # Extract gaps via the typed contract (handles flat/nested shapes).
            gaps = GapAnalysis.from_raw(gap_result).gaps

            span.set_attribute("stage.input_gaps_count", len(gaps))

            interrogation_context = {
                **context,
                "gap_analysis": gap_result,
                "gaps": gaps if gaps else [],  # Provide empty list if no gaps found
            }
            result = self._execute_with_fallback(
                self.interrogator_prepper, interrogation_context, "interrogation"
            )
            self.intermediate_results["interrogation"] = result

            questions = result.get("questions", [])
            span.set_attribute("stage.questions_generated", len(questions))

            if not questions:
                self._log("No interview questions needed (no skill gaps to address)")
                return result

            if self.interactive:
                answers = UserInteraction.conduct_interview(questions)
                # Merge answers into result
                result["interview_notes"] = answers
                self._log("User completed interactive interview")
            elif context.get("interview_answers"):
                result["interview_notes"] = context["interview_answers"]
            elif self.auto_approve:
                # Non-interactive CLI: the interview is optional gap-filling; proceed
                # with no additional answers rather than pausing with no way to resume.
                self._log("Auto-approve: proceeding without interview answers")
                result["interview_notes"] = []
            else:
                # Async web mode: pause for real human answers.
                span.set_attribute("stage.paused", True)
                raise WorkflowPaused(
                    WorkflowState.INTERROGATION_REVIEW, "Waiting for interview answers"
                )

        return result

    def _execute_differentiation(
        self,
        context: Dict[str, Any],
        gap_result: Dict[str, Any],
        interrogation_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute differentiation stage"""
        self.current_state = WorkflowState.DIFFERENTIATION
        self._log("Executing Differentiation")

        with trace_workflow_stage("differentiation") as span:
            differentiation_context = {
                **context,
                "gap_analysis": gap_result,
                "interview_notes": interrogation_result.get(
                    "interview_notes", ""
                ),  # Provide empty string if missing
            }
            result = self._execute_with_fallback(
                self.differentiator, differentiation_context, "differentiation"
            )
            self.intermediate_results["differentiation"] = result

            # Record metrics
            differentiators_count = len(result.get("differentiators", []))
            span.set_attribute("stage.differentiators_found", differentiators_count)
            span.set_attribute("stage.confidence", result.get("confidence", 0))

        return result

    def _execute_tailoring(
        self,
        context: Dict[str, Any],
        gap_result: Dict[str, Any],
        interrogation_result: Dict[str, Any],
        differentiation_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute tailoring stage"""
        self.current_state = WorkflowState.TAILORING
        self._log("Executing Tailoring")

        with trace_workflow_stage("tailoring") as span:
            # Add all required context
            tailoring_context = {
                **context,
                "gap_analysis": gap_result,
                "interview_notes": interrogation_result.get("interview_notes", ""),
                "interrogation_prep": interrogation_result,
                "differentiation": differentiation_result,
                "differentiators": differentiation_result.get("differentiators", []),
            }
            result = self._execute_with_fallback(
                self.tailoring_agent, tailoring_context, "tailoring"
            )
            self.intermediate_results["tailoring"] = result

            docs = TailoredDocuments.from_raw(result)
            span.set_attribute("stage.confidence", result.get("confidence", 0))
            span.set_attribute("stage.has_resume", bool(docs.resume))
            span.set_attribute("stage.has_cover_letter", bool(docs.cover_letter))

        return result

    def _execute_ats_optimization(
        self, context: Dict[str, Any], tailoring_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute ATS optimization stage"""
        self.current_state = WorkflowState.ATS_OPTIMIZATION
        self._log("Executing ATS Optimization")

        with trace_workflow_stage("ats_optimization") as span:
            # Extract tailored content via the typed contract.
            docs = TailoredDocuments.from_raw(tailoring_result)

            ats_context = {
                **context,
                "tailored_resume": docs.resume,
                "tailored_cover_letter": docs.cover_letter,
                "differentiators": self.intermediate_results.get("differentiation", {}).get(
                    "differentiators", []
                ),
            }
            result = self._execute_with_fallback(
                self.ats_optimizer, ats_context, "ats_optimization"
            )
            self.intermediate_results["ats_optimization"] = result

            # Record ATS score if available
            ats_report = result.get("ats_report", {})
            if "ats_score" in ats_report:
                span.set_attribute("stage.ats_score", ats_report["ats_score"])
            span.set_attribute("stage.confidence", result.get("confidence", 0))

        return result

    def _execute_audit(self, context: Dict[str, Any], ats_result: Dict[str, Any]) -> Dict[str, Any]:
        """Audit the generated documents once and report the verdict.

        The audit is a *verification* gate, not a correction loop: it judges the
        documents and records whether they pass. There is no automatic re-write, so
        re-auditing identical text would only burn model calls — the previous
        implementation's retry loop did exactly that (its "apply fixes" step was a
        no-op). Transient audit-call errors are retried (see ``max_audit_retries``);
        a rejection is a valid verdict and is not retried.

        Audit failure is non-fatal by design: the documents and all prior work are
        preserved and returned regardless of the verdict.
        """
        self.current_state = WorkflowState.AUDITING
        self._log("Executing Audit")

        with trace_workflow_stage("auditing", {"max_retries": self.max_audit_retries}) as span:
            # Prefer the ATS-optimized documents; fall back to the tailored ones.
            ats = ATSResult.from_raw(ats_result)
            tailored = TailoredDocuments.from_raw(self.intermediate_results.get("tailoring", {}))
            documents = {
                "resume": ats.optimized_resume or tailored.resume,
                "cover_letter": ats.optimized_cover_letter or tailored.cover_letter,
            }

            try:
                resume_audit = self._audit_document(context, documents["resume"], "resume")
                cover_letter_audit = (
                    self._audit_document(context, documents["cover_letter"], "cover_letter")
                    if documents["cover_letter"]
                    else None
                )
            except Exception as e:
                self._log(f"Audit crashed: {e}")
                span.set_attribute("stage.final_status", "AUDIT_ERROR")
                span.set_attribute("stage.error", str(e))
                return {
                    "final_documents": documents,
                    "audit_report": {
                        "resume_audit": None,
                        "cover_letter_audit": None,
                        "final_status": "AUDIT_ERROR",
                        "retry_count": 0,
                        "error": str(e),
                    },
                    "audit_failed": True,
                    "audit_error": f"Audit crashed: {e}",
                }

            resume_ok = AuditVerdict.from_raw(resume_audit).approved
            cover_letter_ok = (
                AuditVerdict.from_raw(cover_letter_audit).approved
                if cover_letter_audit
                else True  # No cover letter -> nothing to reject.
            )
            approved = resume_ok and cover_letter_ok
            final_status = "APPROVED" if approved else "REJECTED"
            self._log(f"Audit complete: {final_status}")
            span.set_attribute("stage.final_status", final_status)

            return {
                "final_documents": documents,
                "audit_report": {
                    "resume_audit": resume_audit,
                    "cover_letter_audit": cover_letter_audit,
                    "final_status": final_status,
                    "retry_count": 0,
                    "rejection_reason": None if approved else "Document did not pass audit",
                },
                "audit_failed": not approved,
                "audit_error": None if approved else "Document did not pass audit",
            }

    def _audit_document(
        self, context: Dict[str, Any], document: str, document_type: str
    ) -> Dict[str, Any]:
        """Audit a single document, retrying only on transient audit-call errors."""
        attempts = max(1, self.max_audit_retries + 1)  # always attempt at least once
        last_error: Optional[Exception] = None
        for attempt in range(attempts):
            try:
                return self._execute_with_fallback(
                    self.auditor_suite,
                    {**context, "document": document, "document_type": document_type},
                    "auditor_suite",
                )
            except Exception as e:  # transient (e.g. LLM API error) -> retry
                last_error = e
                self._log(f"Audit attempt {attempt + 1}/{attempts} for {document_type} failed: {e}")
        raise last_error  # exhausted retries; surfaced to the non-fatal handler above

    def _execute_executive_synthesis(
        self,
        context: Dict[str, Any],
        gap_result: Dict[str, Any],
        interrogation_result: Dict[str, Any],
        differentiation_result: Dict[str, Any],
        tailoring_result: Dict[str, Any],
        ats_result: Dict[str, Any],
        audit_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute executive synthesis to create strategic brief"""
        self.current_state = WorkflowState.EXECUTIVE_SYNTHESIS
        self._log("Executing Executive Synthesis")

        with trace_workflow_stage("executive_synthesis") as span:
            try:
                # Pass the real tailored documents (previously read the wrong keys,
                # so synthesis always received empty resume/cover-letter text).
                docs = TailoredDocuments.from_raw(tailoring_result)
                synthesis_context = {
                    "job_description": context.get("job_description", ""),
                    "resume": context.get("resume", ""),
                    "gap_analysis": gap_result,
                    "interview_notes": interrogation_result,
                    "differentiation": differentiation_result,
                    "tailored_resume": docs.resume,
                    "tailored_cover_letter": docs.cover_letter,
                    "ats_optimization": ats_result,
                    "audit_report": audit_result.get("audit_report", {}),
                }

                result = self._execute_with_fallback(
                    self.executive_synthesizer, synthesis_context, "executive_synthesis"
                )

                # Deterministic gate: the model reports a fit_score; Python owns the
                # recommendation it maps to (see contracts.recommendation_for_fit_score).
                canonical = ExecutiveDecision.from_raw(result)
                if isinstance(result.get("decision"), dict):
                    result["decision"]["fit_score"] = canonical.fit_score
                    result["decision"]["recommendation"] = canonical.recommendation
                else:
                    result["decision"] = canonical.model_dump()

                self.intermediate_results["executive_synthesis"] = result

                span.set_attribute("stage.recommendation", canonical.recommendation)
                span.set_attribute("stage.fit_score", canonical.fit_score)
                self._log(f"Executive synthesis complete: {canonical.recommendation}")
                return result

            except Exception as e:
                self._log(f"Executive synthesis failed: {str(e)}")
                span.set_attribute("stage.error", str(e))
                span.set_attribute("stage.fallback_used", True)

                # Return a minimal brief on failure with user-friendly message
                # Don't expose internal schema validation errors to the user
                user_message = "Executive summary could not be generated. Your documents are still ready for review."
                return {
                    "decision": {
                        "recommendation": "PROCEED",
                        "fit_score": 70,  # Default to reasonable score, not 0
                        "rationale": user_message,
                        "deal_makers": ["Your tailored documents have been generated successfully"],
                        "deal_breakers": [],
                    },
                    "action_items": {
                        "immediate": [
                            "Review your tailored resume and cover letter",
                            "Make any personal adjustments before submitting",
                        ]
                    },
                    "synthesis_error": str(e),  # Keep technical error for debug tab
                }

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
