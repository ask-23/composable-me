"""
Unit tests for HydraWorkflow
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from runtime.crewai.hydra_workflow import HydraWorkflow, WorkflowState, WorkflowResult, ValidationError


class TestHydraWorkflow:
    """Test suite for HydraWorkflow"""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM for testing"""
        return Mock()
    
    @pytest.fixture
    def workflow(self, mock_llm):
        """Create HydraWorkflow for testing"""
        with patch('runtime.crewai.hydra_workflow.GapAnalyzerAgent'), \
             patch('runtime.crewai.hydra_workflow.InterrogatorPrepperAgent'), \
             patch('runtime.crewai.hydra_workflow.DifferentiatorAgent'), \
             patch('runtime.crewai.hydra_workflow.TailoringAgent'), \
             patch('runtime.crewai.hydra_workflow.ATSOptimizerAgent'), \
             patch('runtime.crewai.hydra_workflow.AuditorSuiteAgent'):
            return HydraWorkflow(mock_llm)
    
    @pytest.fixture
    def sample_context(self):
        """Sample context for testing"""
        return {
            "job_description": "Senior Platform Engineer role requiring AWS, Python, Terraform",
            "resume": "Sample resume content with AWS and Python experience",
            "source_documents": "Original resume with verified AWS and Python experience",
            "target_role": "Senior Platform Engineer"
        }
    
    @pytest.fixture
    def mock_agent_results(self):
        """Mock results from all agents"""
        return {
            "gap_analysis": {
                "agent": "Gap Analyzer",
                "timestamp": "2025-12-06T18:45:00Z",
                "confidence": 0.95,
                "requirements_analysis": {"direct_matches": 5, "gaps": 2}
            },
            "interrogation": {
                "agent": "Interrogator-Prepper",
                "timestamp": "2025-12-06T18:45:00Z",
                "confidence": 0.90,
                "star_questions": ["Tell me about a time..."]
            },
            "differentiation": {
                "agent": "Differentiator",
                "timestamp": "2025-12-06T18:45:00Z",
                "confidence": 0.88,
                "unique_value_props": ["AWS expertise", "Python automation"]
            },
            "tailoring": {
                "agent": "Tailoring Agent",
                "timestamp": "2025-12-06T18:45:00Z",
                "confidence": 0.92,
                "tailored_resume": "Tailored resume content",
                "tailored_cover_letter": "Tailored cover letter content"
            },
            "ats_optimization": {
                "agent": "ATS Optimizer",
                "timestamp": "2025-12-06T18:45:00Z",
                "confidence": 0.95,
                "optimized_resume": "ATS optimized resume content",
                "optimized_cover_letter": "ATS optimized cover letter content"
            },
            "audit_approved": {
                "agent": "Auditor Suite",
                "timestamp": "2025-12-06T18:45:00Z",
                "confidence": 0.98,
                "approval": {"approved": True, "reason": "All checks passed"}
            },
            "audit_rejected": {
                "agent": "Auditor Suite",
                "timestamp": "2025-12-06T18:45:00Z",
                "confidence": 0.85,
                "approval": {"approved": False, "reason": "Tone issues found"}
            }
        }
    
    def test_initialization(self, mock_llm):
        """Test workflow initialization"""
        with patch('runtime.crewai.hydra_workflow.GapAnalyzerAgent'), \
             patch('runtime.crewai.hydra_workflow.InterrogatorPrepperAgent'), \
             patch('runtime.crewai.hydra_workflow.DifferentiatorAgent'), \
             patch('runtime.crewai.hydra_workflow.TailoringAgent'), \
             patch('runtime.crewai.hydra_workflow.ATSOptimizerAgent'), \
             patch('runtime.crewai.hydra_workflow.AuditorSuiteAgent'):
            workflow = HydraWorkflow(mock_llm, max_audit_retries=3)
            assert workflow.llm == mock_llm
            assert workflow.max_audit_retries == 3
            assert workflow.current_state == WorkflowState.INITIALIZED
            assert workflow.execution_log == []
            assert workflow.intermediate_results == {}
    
    def test_execute_missing_job_description(self, workflow):
        """Test execution with missing job_description"""
        context = {
            "resume": "Sample resume",
            "source_documents": "Sample sources"
        }
        
        result = workflow.execute(context)
        
        assert result.success is False
        assert result.state == WorkflowState.FAILED
        assert "Missing required context key: job_description" in result.error_message
    
    def test_execute_missing_resume(self, workflow):
        """Test execution with missing resume"""
        context = {
            "job_description": "Sample JD",
            "source_documents": "Sample sources"
        }
        
        result = workflow.execute(context)
        
        assert result.success is False
        assert result.state == WorkflowState.FAILED
        assert "Missing required context key: resume" in result.error_message
    
    def test_execute_missing_source_documents(self, workflow):
        """Test execution with missing source_documents"""
        context = {
            "job_description": "Sample JD",
            "resume": "Sample resume"
        }
        
        result = workflow.execute(context)
        
        assert result.success is False
        assert result.state == WorkflowState.FAILED
        assert "Missing required context key: source_documents" in result.error_message
    
    def test_execute_success_first_audit_pass(self, workflow, sample_context, mock_agent_results):
        """Test successful execution with audit passing on first attempt"""
        # Mock all agent executions
        workflow.gap_analyzer.execute.return_value = mock_agent_results["gap_analysis"]
        workflow.interrogator_prepper.execute.return_value = mock_agent_results["interrogation"]
        workflow.differentiator.execute.return_value = mock_agent_results["differentiation"]
        workflow.tailoring_agent.execute.return_value = mock_agent_results["tailoring"]
        workflow.ats_optimizer.execute.return_value = mock_agent_results["ats_optimization"]
        workflow.auditor_suite.execute.return_value = mock_agent_results["audit_approved"]
        
        result = workflow.execute(sample_context)
        
        assert result.success is True
        assert result.state == WorkflowState.COMPLETED
        assert result.final_documents is not None
        assert result.audit_report is not None
        assert result.audit_report["final_status"] == "APPROVED"
        assert result.audit_report["retry_count"] == 0
    
    def test_execute_audit_retry_then_pass(self, workflow, sample_context, mock_agent_results):
        """Test execution with audit failing once then passing"""
        # Mock all agent executions
        workflow.gap_analyzer.execute.return_value = mock_agent_results["gap_analysis"]
        workflow.interrogator_prepper.execute.return_value = mock_agent_results["interrogation"]
        workflow.differentiator.execute.return_value = mock_agent_results["differentiation"]
        workflow.tailoring_agent.execute.return_value = mock_agent_results["tailoring"]
        workflow.ats_optimizer.execute.return_value = mock_agent_results["ats_optimization"]

        # First audit fails, second passes (both resume and cover letter audits)
        workflow.auditor_suite.execute.side_effect = [
            mock_agent_results["audit_rejected"],  # First resume audit fails
            mock_agent_results["audit_rejected"],  # First cover letter audit fails
            mock_agent_results["audit_approved"],  # Second resume audit passes
            mock_agent_results["audit_approved"]   # Second cover letter audit passes
        ]

        result = workflow.execute(sample_context)

        assert result.success is True
        assert result.state == WorkflowState.COMPLETED
        assert result.audit_report["retry_count"] == 1
        assert workflow.auditor_suite.execute.call_count == 4  # 2 docs x 2 attempts

    def test_execute_audit_max_retries_exceeded(self, workflow, sample_context, mock_agent_results):
        """Test execution with audit failing maximum retries - now returns success with audit_failed=True"""
        # Mock all agent executions
        workflow.gap_analyzer.execute.return_value = mock_agent_results["gap_analysis"]
        workflow.interrogator_prepper.execute.return_value = mock_agent_results["interrogation"]
        workflow.differentiator.execute.return_value = mock_agent_results["differentiation"]
        workflow.tailoring_agent.execute.return_value = mock_agent_results["tailoring"]
        workflow.ats_optimizer.execute.return_value = mock_agent_results["ats_optimization"]

        # All audit attempts fail
        workflow.auditor_suite.execute.return_value = mock_agent_results["audit_rejected"]

        result = workflow.execute(sample_context)

        # STABILITY FIX: Audit failures are now non-fatal - documents are still produced
        assert result.success is True  # Documents were generated
        assert result.state == WorkflowState.COMPLETED
        assert result.audit_failed is True  # But audit failed
        assert result.audit_error == "Document failed audit after maximum retries"
        assert result.audit_report["final_status"] == "REJECTED"
        assert result.final_documents is not None  # Documents still available
        assert workflow.auditor_suite.execute.call_count == 6  # 2 docs x 3 attempts (initial + 2 retries)

    def test_execute_audit_crash(self, workflow, sample_context, mock_agent_results):
        """Test execution with auditor crashing - returns success with audit_failed=True"""
        # Mock all agent executions up to auditor
        workflow.gap_analyzer.execute.return_value = mock_agent_results["gap_analysis"]
        workflow.interrogator_prepper.execute.return_value = mock_agent_results["interrogation"]
        workflow.differentiator.execute.return_value = mock_agent_results["differentiation"]
        workflow.tailoring_agent.execute.return_value = mock_agent_results["tailoring"]
        workflow.ats_optimizer.execute.return_value = mock_agent_results["ats_optimization"]

        # Auditor crashes on all attempts
        workflow.auditor_suite.execute.side_effect = Exception("LLM API timeout")

        result = workflow.execute(sample_context)

        # STABILITY FIX: Audit crashes are now non-fatal - documents are still produced
        assert result.success is True  # Documents were generated
        assert result.state == WorkflowState.COMPLETED
        assert result.audit_failed is True
        assert "Audit crashed" in result.audit_error
        assert result.audit_report["final_status"] == "AUDIT_CRASHED"
        assert result.final_documents is not None  # Documents still available
        assert result.intermediate_results is not None  # Intermediate results preserved

    def test_execute_agent_failure(self, workflow, sample_context):
        """Test execution with agent failure (pre-audit stages still crash workflow)"""
        # Mock gap analyzer to raise exception
        workflow.gap_analyzer.execute.side_effect = Exception("Gap analysis failed")

        result = workflow.execute(sample_context)

        assert result.success is False
        assert result.state == WorkflowState.FAILED
        assert "Gap analysis failed" in result.error_message

    def test_get_current_state(self, workflow):
        """Test getting current workflow state"""
        assert workflow.get_current_state() == WorkflowState.INITIALIZED

    def test_get_execution_log(self, workflow):
        """Test getting execution log"""
        workflow._log("Test message")
        log = workflow.get_execution_log()
        assert len(log) == 1
        assert "Test message" in log[0]

    def test_get_intermediate_results(self, workflow):
        """Test getting intermediate results"""
        workflow.intermediate_results["test"] = {"data": "value"}
        results = workflow.get_intermediate_results()
        assert results["test"]["data"] == "value"
        # Ensure it's a copy
        results["test"]["data"] = "modified"
        assert workflow.intermediate_results["test"]["data"] == "value"

    def test_validate_input_context_valid(self, workflow, sample_context):
        """Test input context validation with valid context"""
        # Should not raise any exception
        workflow._validate_input_context(sample_context)

    def test_validate_input_context_missing_key(self, workflow):
        """Test input context validation with missing key"""
        context = {"job_description": "Sample JD"}

        with pytest.raises(ValidationError, match="Missing required context key: resume"):
            workflow._validate_input_context(context)

    def test_log_functionality(self, workflow):
        """Test logging functionality"""
        from datetime import datetime
        
        workflow._log("Test log message")

        assert len(workflow.execution_log) == 1
        assert "Test log message" in workflow.execution_log[0]
        # Check for current date in ISO format (YYYY-MM-DD)
        current_date = datetime.now().strftime("%Y-%m-%d")
        assert current_date in workflow.execution_log[0]  # Should contain timestamp

    def test_workflow_state_transitions(self, workflow, sample_context, mock_agent_results):
        """Test that workflow states transition correctly"""
        # Mock all agent executions
        workflow.gap_analyzer.execute.return_value = mock_agent_results["gap_analysis"]
        workflow.interrogator_prepper.execute.return_value = mock_agent_results["interrogation"]
        workflow.differentiator.execute.return_value = mock_agent_results["differentiation"]
        workflow.tailoring_agent.execute.return_value = mock_agent_results["tailoring"]
        workflow.ats_optimizer.execute.return_value = mock_agent_results["ats_optimization"]
        workflow.auditor_suite.execute.return_value = mock_agent_results["audit_approved"]

        # Track state changes by patching the state setter
        states_seen = []
        original_setter = type(workflow).__dict__.get('current_state', None)

        def track_state_change(self, value):
            states_seen.append(value)
            self._current_state = value

        # Monkey patch to track state changes
        workflow._current_state = WorkflowState.INITIALIZED
        type(workflow).current_state = property(
            lambda self: self._current_state,
            track_state_change
        )

        result = workflow.execute(sample_context)

        # Verify state transitions occurred
        expected_states = [
            WorkflowState.GAP_ANALYSIS,
            WorkflowState.INTERROGATION,
            WorkflowState.DIFFERENTIATION,
            WorkflowState.TAILORING,
            WorkflowState.ATS_OPTIMIZATION,
            WorkflowState.AUDITING,
            WorkflowState.COMPLETED
        ]

        for expected_state in expected_states:
            assert expected_state in states_seen
