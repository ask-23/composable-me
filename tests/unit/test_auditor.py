"""
Unit tests for Auditor Suite Agent
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from runtime.crewai.agents.auditor import AuditorSuiteAgent, ValidationError


class TestAuditorSuiteAgent:
    """Test suite for Auditor Suite Agent"""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM for testing"""
        from crewai import LLM
        # Create a real LLM instance with minimal config for testing
        # This avoids validation errors when creating agents
        return LLM(model="gpt-4", api_key="test-key")
    
    @pytest.fixture
    def auditor_suite(self, mock_llm):
        """Create Auditor Suite agent for testing"""
        with patch('runtime.crewai.base_agent.Path'), \
             patch.object(AuditorSuiteAgent, '_load_prompt', return_value="Auditor Suite prompt"), \
             patch.object(AuditorSuiteAgent, '_load_truth_rules', return_value="Truth rules"), \
             patch.object(AuditorSuiteAgent, '_load_style_guide', return_value="Style guide"):
            return AuditorSuiteAgent(mock_llm)
    
    @pytest.fixture
    def sample_context(self):
        """Sample context for testing"""
        return {
            "document": "Sample resume content with AWS and Python experience",
            "document_type": "resume",
            "job_description": "Senior Platform Engineer role requiring AWS, Python, Terraform",
            "source_documents": "Original resume with verified AWS and Python experience",
            "target_role": "Senior Platform Engineer"
        }
    
    @pytest.fixture
    def valid_output(self):
        """Valid Auditor Suite output for testing"""
        return {
            "agent": "Auditor Suite",
            "timestamp": "2025-12-06T18:45:00Z",
            "confidence": 0.95,
            "audit_report": {
                "meta": {
                    "document_type": "resume",
                    "target_role": "Senior Platform Engineer",
                    "audited": "2025-12-06T18:45:00Z"
                },
                "summary": {
                    "overall_status": "PASS",
                    "blocking_issues": 0,
                    "warnings": 2,
                    "recommendations": 3
                }
            },
            "summary": {
                "overall_status": "PASS",
                "blocking_issues": 0,
                "warnings": 2,
                "recommendations": 3
            },
            "truth_audit": {
                "status": "PASS",
                "verified_claims": 15,
                "approximate_claims": 2,
                "issues": []
            },
            "tone_audit": {
                "status": "CONDITIONAL",
                "score": "borderline",
                "issues": [
                    {
                        "id": "TONE-001",
                        "location": "Summary, line 2",
                        "pattern": "leverage my expertise",
                        "severity": "warning",
                        "fix": "Replace with specific skill mention"
                    }
                ]
            },
            "ats_audit": {
                "status": "PASS",
                "keyword_coverage": "85%",
                "format_issues": [],
                "recommendations": ["Consider adding 'IaC' as explicit keyword"]
            },
            "compliance_audit": {
                "status": "PASS",
                "violations": [],
                "warnings": []
            },
            "action_required": {
                "blocking": [],
                "recommended": ["TONE-001: Replace 'leverage my expertise'"],
                "optional": ["Add 'IaC' keyword"]
            },
            "approval": {
                "approved": False,
                "reason": "2 tone warnings should be addressed",
                "next_steps": "Fix warnings and re-submit for audit"
            }
        }
    
    def test_initialization(self, mock_llm):
        """Test agent initialization"""
        with patch('runtime.crewai.base_agent.Path'), \
             patch.object(AuditorSuiteAgent, '_load_prompt', return_value="Auditor Suite prompt"), \
             patch.object(AuditorSuiteAgent, '_load_truth_rules', return_value="Truth rules"), \
             patch.object(AuditorSuiteAgent, '_load_style_guide', return_value="Style guide"):
            agent = AuditorSuiteAgent(mock_llm)
            assert agent.role == "Auditor Suite"
            assert "truthful" in agent.goal
            assert "YAML" in agent.expected_output
    
    def test_execute_missing_document(self, auditor_suite):
        """Test execution with missing document"""
        context = {
            "document_type": "resume",
            "job_description": "Sample JD",
            "source_documents": "Sample sources"
        }
        
        with pytest.raises(ValidationError, match="Missing required context key: document"):
            auditor_suite.execute(context)
    
    def test_execute_missing_document_type(self, auditor_suite):
        """Test execution with missing document_type"""
        context = {
            "document": "Sample document",
            "job_description": "Sample JD",
            "source_documents": "Sample sources"
        }
        
        with pytest.raises(ValidationError, match="Missing required context key: document_type"):
            auditor_suite.execute(context)
    
    def test_execute_missing_job_description(self, auditor_suite):
        """Test execution with missing job_description"""
        context = {
            "document": "Sample document",
            "document_type": "resume",
            "source_documents": "Sample sources"
        }
        
        with pytest.raises(ValidationError, match="Missing required context key: job_description"):
            auditor_suite.execute(context)
    
    def test_execute_missing_source_documents(self, auditor_suite):
        """Test execution with missing source_documents"""
        context = {
            "document": "Sample document",
            "document_type": "resume",
            "job_description": "Sample JD"
        }
        
        with pytest.raises(ValidationError, match="Missing required context key: source_documents"):
            auditor_suite.execute(context)
    
    @patch('runtime.crewai.base_agent.Crew')
    def test_execute_success(self, mock_crew_class, auditor_suite, sample_context, valid_output):
        """Test successful execution"""
        # Mock the Crew instance and its kickoff method
        mock_crew_instance = Mock()
        mock_crew_instance.kickoff.return_value = """
agent: Auditor Suite
timestamp: 2025-12-06T18:45:00Z
confidence: 0.95
audit_report:
  meta:
    document_type: resume
    target_role: Senior Platform Engineer
    audited: 2025-12-06T18:45:00Z
  summary:
    overall_status: PASS
    blocking_issues: 0
    warnings: 2
    recommendations: 3
summary:
  overall_status: PASS
  blocking_issues: 0
  warnings: 2
  recommendations: 3
truth_audit:
  status: PASS
  verified_claims: 15
  approximate_claims: 2
  issues: []
tone_audit:
  status: CONDITIONAL
  score: borderline
  issues:
    - id: TONE-001
      location: Summary, line 2
      pattern: leverage my expertise
      severity: warning
      fix: Replace with specific skill mention
ats_audit:
  status: PASS
  keyword_coverage: 85%
  format_issues: []
  recommendations:
    - Consider adding 'IaC' as explicit keyword
compliance_audit:
  status: PASS
  violations: []
  warnings: []
action_required:
  blocking: []
  recommended:
    - 'TONE-001: Replace leverage my expertise'
  optional:
    - Add 'IaC' keyword
approval:
  approved: false
  reason: 2 tone warnings should be addressed
  next_steps: Fix warnings and re-submit for audit
"""
        mock_crew_class.return_value = mock_crew_instance
        
        result = auditor_suite.execute(sample_context)
        
        assert result["agent"] == "Auditor Suite"
        assert result["summary"]["overall_status"] == "PASS"
        assert mock_crew_instance.kickoff.call_count == 1
    
    def test_validate_schema_valid_output(self, auditor_suite, valid_output):
        """Test schema validation with valid output"""
        # Should not raise any exception
        auditor_suite._validate_schema(valid_output)

    def test_validate_schema_missing_audit_report(self, auditor_suite, valid_output):
        """Test schema validation with missing audit_report"""
        del valid_output["audit_report"]

        with pytest.raises(ValidationError, match="Missing required field: audit_report"):
            auditor_suite._validate_schema(valid_output)

    def test_validate_schema_invalid_overall_status(self, auditor_suite, valid_output):
        """Test schema validation with invalid overall_status"""
        valid_output["summary"]["overall_status"] = "INVALID"

        with pytest.raises(ValidationError, match="overall_status must be one of"):
            auditor_suite._validate_schema(valid_output)

    def test_validate_schema_invalid_blocking_issues(self, auditor_suite, valid_output):
        """Test schema validation with invalid blocking_issues type"""
        valid_output["summary"]["blocking_issues"] = "none"  # Should be integer

        with pytest.raises(ValidationError, match="blocking_issues must be a non-negative integer"):
            auditor_suite._validate_schema(valid_output)

    def test_validate_schema_negative_warnings(self, auditor_suite, valid_output):
        """Test schema validation with negative warnings"""
        valid_output["summary"]["warnings"] = -1  # Should be non-negative

        with pytest.raises(ValidationError, match="warnings must be a non-negative integer"):
            auditor_suite._validate_schema(valid_output)

    def test_validate_schema_invalid_truth_audit_status(self, auditor_suite, valid_output):
        """Test schema validation with invalid truth_audit status"""
        valid_output["truth_audit"]["status"] = "UNKNOWN"

        with pytest.raises(ValidationError, match="truth_audit.status must be one of"):
            auditor_suite._validate_schema(valid_output)

    def test_validate_schema_invalid_action_required_blocking(self, auditor_suite, valid_output):
        """Test schema validation with invalid action_required.blocking type"""
        valid_output["action_required"]["blocking"] = "none"  # Should be list

        with pytest.raises(ValidationError, match="action_required.blocking must be a list"):
            auditor_suite._validate_schema(valid_output)

    def test_validate_schema_invalid_approval_approved(self, auditor_suite, valid_output):
        """Test schema validation with invalid approval.approved type"""
        valid_output["approval"]["approved"] = "yes"  # Should be boolean

        with pytest.raises(ValidationError, match="approval.approved must be a boolean"):
            auditor_suite._validate_schema(valid_output)

    def test_validate_schema_invalid_approval_reason(self, auditor_suite, valid_output):
        """Test schema validation with invalid approval.reason type"""
        valid_output["approval"]["reason"] = 123  # Should be string

        with pytest.raises(ValidationError, match="approval.reason must be a string"):
            auditor_suite._validate_schema(valid_output)
