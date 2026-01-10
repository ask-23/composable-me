"""
Unit tests for data models.

Tests data model creation, validation, and state transitions.
"""

import pytest
from datetime import datetime

from runtime.crewai.models import (
    Employment,
    Resume,
    JobDescription,
    Requirement,
    Classification,
    Differentiator,
    AuditIssue,
    WorkflowState,
    WorkflowStatus,
    ClassificationType,
    IssueSeverity,
    RequirementType,
    RequirementPriority,
)


class TestEmployment:
    """Test suite for Employment model"""
    
    def test_employment_creation(self):
        """Test creating a valid employment entry"""
        emp = Employment(
            company="Test Corp",
            title="Senior Engineer",
            start_date="2020-01",
            end_date="2023-12",
            achievements=["Built system", "Led team"],
            technologies=["Python", "AWS"]
        )
        
        assert emp.company == "Test Corp"
        assert emp.title == "Senior Engineer"
        assert len(emp.achievements) == 2
        assert len(emp.technologies) == 2
    
    def test_employment_missing_required_fields(self):
        """Test employment validation fails without required fields"""
        with pytest.raises(ValueError, match="must have company, title, and start_date"):
            Employment(
                company="",
                title="Engineer",
                start_date="2020-01",
                end_date=None
            )


class TestResume:
    """Test suite for Resume model"""
    
    def test_resume_creation(self):
        """Test creating a valid resume"""
        resume = Resume(
            text="Resume content",
            format="markdown",
            employment_history=[],
            skills=["Python", "AWS"]
        )
        
        assert resume.text == "Resume content"
        assert resume.format == "markdown"
        assert len(resume.skills) == 2
    
    def test_resume_empty_text(self):
        """Test resume validation fails with empty text"""
        with pytest.raises(ValueError, match="Resume text cannot be empty"):
            Resume(text="")


class TestJobDescription:
    """Test suite for JobDescription model"""
    
    def test_job_description_creation(self):
        """Test creating a valid job description"""
        jd = JobDescription(
            text="Job description content",
            company="Test Corp",
            role="Senior Engineer",
            requirements=["Python", "AWS"]
        )
        
        assert jd.text == "Job description content"
        assert jd.company == "Test Corp"
        assert jd.role == "Senior Engineer"
        assert len(jd.requirements) == 2
    
    def test_job_description_empty_text(self):
        """Test job description validation fails with empty text"""
        with pytest.raises(ValueError, match="Job description text cannot be empty"):
            JobDescription(text="")


class TestRequirement:
    """Test suite for Requirement model"""
    
    def test_requirement_creation(self):
        """Test creating a valid requirement"""
        req = Requirement(
            text="5+ years Python experience",
            type=RequirementType.EXPLICIT,
            priority=RequirementPriority.MUST_HAVE,
            keywords=["Python", "5 years"]
        )
        
        assert req.text == "5+ years Python experience"
        assert req.type == RequirementType.EXPLICIT
        assert req.priority == RequirementPriority.MUST_HAVE
        assert len(req.keywords) == 2
    
    def test_requirement_empty_text(self):
        """Test requirement validation fails with empty text"""
        with pytest.raises(ValueError, match="Requirement text cannot be empty"):
            Requirement(
                text="",
                type=RequirementType.EXPLICIT,
                priority=RequirementPriority.MUST_HAVE
            )


class TestClassification:
    """Test suite for Classification model"""
    
    def test_classification_creation(self):
        """Test creating a valid classification"""
        req = Requirement(
            text="Python experience",
            type=RequirementType.EXPLICIT,
            priority=RequirementPriority.MUST_HAVE
        )
        
        classification = Classification(
            requirement=req,
            category=ClassificationType.DIRECT_MATCH,
            evidence="5 years Python at Company X",
            confidence=0.95,
            framing="Strong Python background"
        )
        
        assert classification.category == ClassificationType.DIRECT_MATCH
        assert classification.confidence == 0.95
        assert classification.evidence is not None
    
    def test_classification_invalid_confidence(self):
        """Test classification validation fails with invalid confidence"""
        req = Requirement(
            text="Python experience",
            type=RequirementType.EXPLICIT,
            priority=RequirementPriority.MUST_HAVE
        )
        
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            Classification(
                requirement=req,
                category=ClassificationType.DIRECT_MATCH,
                confidence=1.5
            )


class TestDifferentiator:
    """Test suite for Differentiator model"""
    
    def test_differentiator_creation(self):
        """Test creating a valid differentiator"""
        diff = Differentiator(
            hook="Unique combination of AI and infrastructure",
            evidence="Built LLM-powered platform on AWS",
            resonance="Matches role's focus on AI infrastructure",
            relevance_score=0.9
        )
        
        assert diff.hook is not None
        assert diff.evidence is not None
        assert diff.resonance is not None
        assert diff.relevance_score == 0.9
    
    def test_differentiator_missing_fields(self):
        """Test differentiator validation fails with missing fields"""
        with pytest.raises(ValueError, match="must have hook, evidence, and resonance"):
            Differentiator(
                hook="",
                evidence="Some evidence",
                resonance="Some resonance"
            )
    
    def test_differentiator_invalid_relevance_score(self):
        """Test differentiator validation fails with invalid relevance score"""
        with pytest.raises(ValueError, match="Relevance score must be between 0.0 and 1.0"):
            Differentiator(
                hook="Test hook",
                evidence="Test evidence",
                resonance="Test resonance",
                relevance_score=1.5
            )


class TestAuditIssue:
    """Test suite for AuditIssue model"""
    
    def test_audit_issue_creation(self):
        """Test creating a valid audit issue"""
        issue = AuditIssue(
            type="truth",
            severity=IssueSeverity.BLOCKING,
            location="Resume line 10",
            description="Unverified claim",
            fix="Remove or verify claim"
        )
        
        assert issue.type == "truth"
        assert issue.severity == IssueSeverity.BLOCKING
        assert issue.location is not None
    
    def test_audit_issue_invalid_type(self):
        """Test audit issue validation fails with invalid type"""
        with pytest.raises(ValueError, match="Issue type must be one of"):
            AuditIssue(
                type="invalid_type",
                severity=IssueSeverity.BLOCKING,
                location="Test location",
                description="Test description",
                fix="Test fix"
            )


class TestWorkflowState:
    """Test suite for WorkflowState model"""
    
    def test_workflow_state_creation(self):
        """Test creating a valid workflow state"""
        state = WorkflowState(
            id="test-workflow-1",
            status=WorkflowStatus.INITIALIZED,
            current_stage="initialization"
        )
        
        assert state.id == "test-workflow-1"
        assert state.status == WorkflowStatus.INITIALIZED
        assert state.current_stage == "initialization"
        assert len(state.audit_trail) == 0
    
    def test_workflow_state_valid_transition(self):
        """Test valid state transition"""
        state = WorkflowState(
            id="test-workflow-1",
            status=WorkflowStatus.INITIALIZED,
            current_stage="initialization"
        )
        
        # Valid transition: INITIALIZED -> ANALYZING
        state.transition(WorkflowStatus.ANALYZING)
        
        assert state.status == WorkflowStatus.ANALYZING
    
    def test_workflow_state_invalid_transition(self):
        """Test invalid state transition"""
        state = WorkflowState(
            id="test-workflow-1",
            status=WorkflowStatus.INITIALIZED,
            current_stage="initialization"
        )
        
        # Invalid transition: INITIALIZED -> COMPLETE
        with pytest.raises(ValueError, match="Invalid transition"):
            state.transition(WorkflowStatus.COMPLETE)
    
    def test_workflow_state_log_agent_execution(self):
        """Test logging agent execution"""
        state = WorkflowState(
            id="test-workflow-1",
            status=WorkflowStatus.INITIALIZED,
            current_stage="initialization"
        )
        
        state.log_agent_execution(
            agent_name="test_agent",
            inputs={"input": "test"},
            output={"output": "result"},
            success=True
        )
        
        assert len(state.audit_trail) == 1
        assert state.audit_trail[0].agent_name == "test_agent"
        assert state.audit_trail[0].success is True
        assert "test_agent" in state.agent_outputs
    
    def test_workflow_state_log_error(self):
        """Test logging error"""
        state = WorkflowState(
            id="test-workflow-1",
            status=WorkflowStatus.INITIALIZED,
            current_stage="initialization"
        )
        
        error = Exception("Test error")
        state.log_error(error)
        
        assert len(state.errors) == 1
        assert "Test error" in state.errors[0]["error"]
    
    def test_workflow_state_retry_count(self):
        """Test retry count tracking"""
        state = WorkflowState(
            id="test-workflow-1",
            status=WorkflowStatus.INITIALIZED,
            current_stage="initialization"
        )
        
        assert state.get_retry_count("test_agent") == 0
        
        state.increment_retry("test_agent")
        assert state.get_retry_count("test_agent") == 1
        
        state.increment_retry("test_agent")
        assert state.get_retry_count("test_agent") == 2
    
    def test_workflow_state_log_user_interaction(self):
        """Test logging user interaction"""
        state = WorkflowState(
            id="test-workflow-1",
            status=WorkflowStatus.INITIALIZED,
            current_stage="initialization"
        )
        
        state.log_user_interaction(
            interaction_type="greenlight",
            data={"approved": True}
        )
        
        assert len(state.user_interactions) == 1
        assert state.user_interactions[0]["type"] == "greenlight"
        assert state.user_interactions[0]["data"]["approved"] is True
