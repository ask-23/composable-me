"""
Unit tests for ATS Optimizer Agent
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from runtime.crewai.agents.ats_optimizer import ATSOptimizerAgent, ValidationError


class TestATSOptimizerAgent:
    """Test suite for ATS Optimizer Agent"""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM for testing"""
        return Mock()
    
    @pytest.fixture
    def ats_optimizer(self, mock_llm):
        """Create ATS Optimizer agent for testing"""
        with patch('runtime.crewai.base_agent.Path'), \
             patch.object(ATSOptimizerAgent, '_load_prompt', return_value="ATS Optimizer prompt"), \
             patch.object(ATSOptimizerAgent, '_load_truth_rules', return_value="Truth rules"), \
             patch.object(ATSOptimizerAgent, '_load_style_guide', return_value="Style guide"):
            return ATSOptimizerAgent(mock_llm)
    
    @pytest.fixture
    def sample_context(self):
        """Sample context for testing"""
        return {
            "tailored_resume": "Sample tailored resume content with AWS and Python experience",
            "job_description": "Senior Platform Engineer role requiring AWS, Python, Terraform",
            "source_documents": "Original resume with verified AWS and Python experience"
        }
    
    @pytest.fixture
    def valid_output(self):
        """Valid ATS Optimizer output for testing"""
        return {
            "agent": "ATS Optimizer",
            "timestamp": "2025-12-06T18:45:00Z",
            "confidence": 0.95,
            "ats_report": {
                "meta": {
                    "role": "Senior Platform Engineer",
                    "company": "TechCorp",
                    "analyzed": "2025-12-06"
                },
                "summary": {
                    "keyword_coverage": "85%",
                    "format_score": "90%",
                    "ats_ready": True,
                    "human_readable": True
                },
                "keyword_analysis": {
                    "hard_requirements": [
                        {
                            "keyword": "AWS",
                            "status": "present",
                            "count": 8
                        }
                    ],
                    "soft_requirements": [],
                    "added_truthfully": ["IaC", "Linux"],
                    "not_added": []
                },
                "format_analysis": {
                    "issues_found": 2,
                    "issues_fixed": 2,
                    "remaining_issues": 0
                }
            },
            "summary": {
                "keyword_coverage": "85%",
                "format_score": "90%", 
                "ats_ready": True,
                "human_readable": True
            },
            "keyword_analysis": {
                "hard_requirements": [],
                "soft_requirements": [],
                "added_truthfully": [],
                "not_added": []
            },
            "format_analysis": {
                "issues_found": 0,
                "issues_fixed": 0,
                "remaining_issues": 0
            },
            "optimized_resume": "Optimized resume content with improved ATS compatibility",
            "changes_made": [
                "Added 'CI/CD' to deployment bullet",
                "Added 'IaC' near Terraform mention"
            ],
            "verification": {
                "all_additions_truthful": True,
                "human_readable": True,
                "source_mapping": [
                    {
                        "addition": "Linux",
                        "justification": "AWS experience implies Linux; user confirmed"
                    }
                ]
            }
        }
    
    def test_initialization(self, mock_llm):
        """Test agent initialization"""
        with patch('runtime.crewai.base_agent.Path'), \
             patch.object(ATSOptimizerAgent, '_load_prompt', return_value="ATS Optimizer prompt"), \
             patch.object(ATSOptimizerAgent, '_load_truth_rules', return_value="Truth rules"), \
             patch.object(ATSOptimizerAgent, '_load_style_guide', return_value="Style guide"):
            agent = ATSOptimizerAgent(mock_llm)
            assert agent.role == "ATS Optimizer"
            assert "automated screening systems" in agent.goal
            assert "YAML" in agent.expected_output
    
    def test_execute_missing_tailored_resume(self, ats_optimizer):
        """Test execution with missing tailored_resume"""
        context = {"job_description": "Sample JD"}
        
        with pytest.raises(ValidationError, match="Missing required context key: tailored_resume"):
            ats_optimizer.execute(context)
    
    def test_execute_missing_job_description(self, ats_optimizer):
        """Test execution with missing job_description"""
        context = {"tailored_resume": "Sample resume"}
        
        with pytest.raises(ValidationError, match="Missing required context key: job_description"):
            ats_optimizer.execute(context)
    
    @patch('runtime.crewai.agents.ats_optimizer.ATSOptimizerAgent.execute_with_retry')
    def test_execute_success(self, mock_execute, ats_optimizer, sample_context, valid_output):
        """Test successful execution"""
        mock_execute.return_value = valid_output
        
        result = ats_optimizer.execute(sample_context)
        
        assert result == valid_output
        mock_execute.assert_called_once()
    
    def test_validate_schema_valid_output(self, ats_optimizer, valid_output):
        """Test schema validation with valid output"""
        # Should not raise any exception
        ats_optimizer._validate_schema(valid_output)
    
    def test_validate_schema_missing_ats_report(self, ats_optimizer, valid_output):
        """Test schema validation with missing ats_report"""
        del valid_output["ats_report"]

        with pytest.raises(ValidationError, match="Missing required field: ats_report"):
            ats_optimizer._validate_schema(valid_output)

    def test_validate_schema_invalid_keyword_coverage(self, ats_optimizer, valid_output):
        """Test schema validation with invalid keyword_coverage format"""
        valid_output["summary"]["keyword_coverage"] = 85  # Should be string with %

        with pytest.raises(ValidationError, match="keyword_coverage must be a percentage string"):
            ats_optimizer._validate_schema(valid_output)

    def test_validate_schema_invalid_format_score(self, ats_optimizer, valid_output):
        """Test schema validation with invalid format_score format"""
        valid_output["summary"]["format_score"] = "high"  # Should be percentage string

        with pytest.raises(ValidationError, match="format_score must be a percentage string"):
            ats_optimizer._validate_schema(valid_output)

    def test_validate_schema_invalid_ats_ready(self, ats_optimizer, valid_output):
        """Test schema validation with invalid ats_ready type"""
        valid_output["summary"]["ats_ready"] = "yes"  # Should be boolean

        with pytest.raises(ValidationError, match="ats_ready must be a boolean"):
            ats_optimizer._validate_schema(valid_output)

    def test_validate_schema_invalid_changes_made(self, ats_optimizer, valid_output):
        """Test schema validation with invalid changes_made type"""
        valid_output["changes_made"] = "Some changes"  # Should be list

        with pytest.raises(ValidationError, match="changes_made must be a list"):
            ats_optimizer._validate_schema(valid_output)

    def test_validate_schema_invalid_optimized_resume(self, ats_optimizer, valid_output):
        """Test schema validation with invalid optimized_resume type"""
        valid_output["optimized_resume"] = ["resume", "content"]  # Should be string

        with pytest.raises(ValidationError, match="optimized_resume must be a string"):
            ats_optimizer._validate_schema(valid_output)
