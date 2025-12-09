"""
Unit tests for Differentiator Agent.

Tests unique value identification, relevance scoring, and source material traceability.
"""

import pytest
import yaml
from unittest.mock import Mock, patch, MagicMock
from crewai import LLM

from runtime.crewai.agents.differentiator import DifferentiatorAgent
from runtime.crewai.base_agent import ValidationError


class TestDifferentiatorAgent:
    """Test cases for Differentiator Agent"""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing"""
        return Mock(spec=LLM)
    
    @pytest.fixture
    def differentiator(self, mock_llm):
        """Create Differentiator agent for testing"""
        with patch('runtime.crewai.base_agent.Path'), \
             patch.object(DifferentiatorAgent, '_load_prompt', return_value="Differentiator prompt"), \
             patch.object(DifferentiatorAgent, '_load_truth_rules', return_value="Truth rules"), \
             patch.object(DifferentiatorAgent, '_load_style_guide', return_value="Style guide"):
            return DifferentiatorAgent(mock_llm)
    
    @pytest.fixture
    def sample_context(self):
        """Sample context for testing"""
        return {
            "job_description": "Senior Platform Engineer - build developer tools and infrastructure",
            "resume": "Platform Engineer with AWS, Terraform, and team leadership experience",
            "interview_notes": {
                "themes": [
                    {
                        "theme": "leadership",
                        "details": "Led team of 5 engineers, reduced deploy time by 80%"
                    }
                ]
            },
            "gap_analysis": {
                "requirements": [
                    {"requirement": "AWS", "classification": "direct_match"},
                    {"requirement": "Team leadership", "classification": "direct_match"}
                ]
            }
        }
    
    @pytest.fixture
    def valid_output(self):
        """Valid Differentiator output for testing"""
        return {
            "agent": "differentiator",
            "timestamp": "2025-12-06T01:00:00Z",
            "confidence": 0.85,
            "differentiators": [
                {
                    "differentiator": "Builds systems that eliminate bottlenecks, including himself",
                    "evidence": [
                        "Reduced deploy time by 80% through automation",
                        "Created self-service infrastructure platform"
                    ],
                    "framing_suggestion": "Lead with bottleneck elimination in cover letter opening",
                    "relevance_to_jd": "JD emphasizes developer velocity and autonomous teams",
                    "uniqueness_score": 0.9
                },
                {
                    "differentiator": "Enterprise scale with startup speed",
                    "evidence": [
                        "AWS multi-account architecture experience",
                        "Startup experience with rapid iteration"
                    ],
                    "framing_suggestion": "Highlight ability to operate at both scales",
                    "relevance_to_jd": "Company is scaling startup needing enterprise practices",
                    "uniqueness_score": 0.7
                }
            ],
            "positioning_angles": [
                "The Platform Engineer who makes teams autonomous",
                "Enterprise expertise with startup agility",
                "Technical depth with business communication skills"
            ]
        }
    
    def test_initialization(self, mock_llm):
        """Test agent initialization"""
        with patch('runtime.crewai.base_agent.Path'), \
             patch.object(DifferentiatorAgent, '_load_prompt', return_value="Differentiator prompt"), \
             patch.object(DifferentiatorAgent, '_load_truth_rules', return_value="Truth rules"), \
             patch.object(DifferentiatorAgent, '_load_style_guide', return_value="Style guide"):
            agent = DifferentiatorAgent(mock_llm)
            assert agent.role == "Differentiator"
            assert "unique value propositions" in agent.goal
            assert "YAML" in agent.expected_output
    
    def test_execute_missing_interview_notes(self, differentiator):
        """Test execute with missing interview notes"""
        context = {
            "job_description": "test",
            "resume": "test",
            "gap_analysis": {}
        }
        
        with pytest.raises(ValidationError, match="Missing required context key: interview_notes"):
            differentiator.execute(context)
    
    @patch('runtime.crewai.agents.differentiator.DifferentiatorAgent.execute_with_retry')
    def test_execute_success(self, mock_execute, differentiator, sample_context, valid_output):
        """Test successful execution"""
        mock_execute.return_value = valid_output

        result = differentiator.execute(sample_context)

        assert result == valid_output
        mock_execute.assert_called_once()
    
    def test_validate_schema_valid_output(self, differentiator, valid_output):
        """Test schema validation with valid output"""
        # Should not raise any exception
        differentiator._validate_schema(valid_output)
    
    def test_validate_schema_missing_differentiators(self, differentiator):
        """Test schema validation with missing differentiators field"""
        invalid_output = {
            "agent": "differentiator",
            "timestamp": "2025-12-06T01:00:00Z",
            "confidence": 0.85,
            "positioning_angles": []
        }
        
        with pytest.raises(ValidationError, match="Missing required field: differentiators"):
            differentiator._validate_schema(invalid_output)
    
    def test_validate_schema_invalid_uniqueness_score(self, differentiator, valid_output):
        """Test schema validation with invalid uniqueness score"""
        invalid_output = valid_output.copy()
        invalid_output["differentiators"][0]["uniqueness_score"] = 1.5  # > 1.0
        
        with pytest.raises(ValidationError, match="uniqueness_score must be between 0.0 and 1.0"):
            differentiator._validate_schema(invalid_output)
    
    def test_validate_schema_evidence_not_list(self, differentiator, valid_output):
        """Test schema validation with evidence not being a list"""
        invalid_output = valid_output.copy()
        invalid_output["differentiators"][0]["evidence"] = "not a list"
        
        with pytest.raises(ValidationError, match="evidence must be a list"):
            differentiator._validate_schema(invalid_output)
