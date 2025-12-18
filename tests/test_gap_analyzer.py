"""
Unit tests for Gap Analyzer Agent.

Tests requirement extraction, classification accuracy, blocker detection,
evidence tracking, and truth law compliance.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from crewai import LLM

from runtime.crewai.agents.gap_analyzer import GapAnalyzerAgent
from runtime.crewai.base_agent import ValidationError


class TestGapAnalyzerAgent:
    """Test cases for Gap Analyzer Agent"""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing"""
        from crewai import LLM
        # Create a real LLM instance with minimal config for testing
        # This avoids validation errors when creating agents
        return LLM(model="gpt-4", api_key="test-key")
    
    @pytest.fixture
    def gap_analyzer(self, mock_llm):
        """Create Gap Analyzer agent for testing"""
        with patch('runtime.crewai.base_agent.Path'), \
             patch.object(GapAnalyzerAgent, '_load_prompt', return_value="Gap Analyzer prompt"), \
             patch.object(GapAnalyzerAgent, '_load_truth_rules', return_value="Truth rules"), \
             patch.object(GapAnalyzerAgent, '_load_style_guide', return_value="Style guide"):
            return GapAnalyzerAgent(mock_llm)
    
    @pytest.fixture
    def sample_context(self):
        """Sample context for testing"""
        return {
            "job_description": "Senior DevOps Engineer with 5+ years AWS experience, Terraform, Kubernetes preferred",
            "resume": "DevOps Engineer at TechCorp (2020-2023). AWS infrastructure, Terraform IaC, Docker containers.",
            "research_data": {"company": "TechCorp", "industry": "SaaS"}
        }
    
    @pytest.fixture
    def valid_output(self):
        """Valid Gap Analyzer output for testing"""
        return {
            "agent": "gap_analyzer",
            "timestamp": "2025-12-06T01:00:00Z",
            "confidence": 0.85,
            "requirements": [
                {
                    "requirement": "5+ years AWS experience",
                    "classification": "direct_match",
                    "evidence": "AWS infrastructure at TechCorp (2020-2023)",
                    "source_location": "resume, TechCorp role",
                    "confidence": 0.9
                },
                {
                    "requirement": "Terraform experience",
                    "classification": "direct_match", 
                    "evidence": "Terraform IaC mentioned in resume",
                    "source_location": "resume, TechCorp role",
                    "confidence": 0.8
                },
                {
                    "requirement": "Kubernetes preferred",
                    "classification": "adjacent_experience",
                    "evidence": "Docker containers experience",
                    "source_location": "resume, TechCorp role", 
                    "confidence": 0.6
                }
            ],
            "fit_score": 85.0,
            "gaps": [],
            "blockers": []
        }
    
    def test_initialization(self, mock_llm):
        """Test agent initialization"""
        with patch('runtime.crewai.base_agent.Path'), \
             patch.object(GapAnalyzerAgent, '_load_prompt', return_value="Gap Analyzer prompt"), \
             patch.object(GapAnalyzerAgent, '_load_truth_rules', return_value="Truth rules"), \
             patch.object(GapAnalyzerAgent, '_load_style_guide', return_value="Style guide"):
            agent = GapAnalyzerAgent(mock_llm)
            assert agent.role == "Gap Analyzer"
            assert agent.goal == "Map job requirements to candidate experience and classify fit levels"
            assert "JSON" in agent.expected_output
    
    def test_execute_missing_job_description(self, gap_analyzer):
        """Test execute with missing job description"""
        context = {"resume": "test resume"}
        
        with pytest.raises(ValidationError, match="Missing required context key: job_description"):
            gap_analyzer.execute(context)
    
    def test_execute_missing_resume(self, gap_analyzer):
        """Test execute with missing resume"""
        context = {"job_description": "test job description"}
        
        with pytest.raises(ValidationError, match="Missing required context key: resume"):
            gap_analyzer.execute(context)
    
    @patch('runtime.crewai.agents.gap_analyzer.GapAnalyzerAgent.execute_with_retry')
    def test_execute_success(self, mock_execute, gap_analyzer, sample_context, valid_output):
        """Test successful execution"""
        mock_execute.return_value = valid_output

        result = gap_analyzer.execute(sample_context)

        assert result == valid_output
        mock_execute.assert_called_once()
    
    def test_validate_schema_valid_output(self, gap_analyzer, valid_output):
        """Test schema validation with valid output"""
        # Should not raise any exception
        gap_analyzer._validate_schema(valid_output)
    
    def test_validate_schema_missing_requirements(self, gap_analyzer):
        """Test schema validation with missing requirements field"""
        invalid_output = {
            "agent": "gap_analyzer",
            "timestamp": "2025-12-06T01:00:00Z",
            "confidence": 0.85,
            "fit_score": 85.0,
            "gaps": [],
            "blockers": []
        }
        
        with pytest.raises(ValidationError, match="Missing required field: requirements"):
            gap_analyzer._validate_schema(invalid_output)
    
    def test_validate_schema_invalid_classification(self, gap_analyzer, valid_output):
        """Test schema validation with invalid classification"""
        invalid_output = valid_output.copy()
        invalid_output["requirements"][0]["classification"] = "invalid_classification"
        
        with pytest.raises(ValidationError, match="Invalid classification"):
            gap_analyzer._validate_schema(invalid_output)
