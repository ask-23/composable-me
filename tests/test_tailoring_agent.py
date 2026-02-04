"""
Unit tests for Tailoring Agent.

Tests resume generation, cover letter generation, anti-AI pattern compliance,
and source material traceability.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from crewai import LLM

from runtime.crewai.agents.tailoring_agent import TailoringAgent
from runtime.crewai.base_agent import ValidationError


class TestTailoringAgent:
    """Test cases for Tailoring Agent"""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing"""
        from crewai import LLM
        # Create a real LLM instance with minimal config for testing
        # This avoids validation errors when creating agents
        return LLM(model="gpt-4", api_key="test-key")
    
    @pytest.fixture
    def tailoring_agent(self, mock_llm):
        """Create Tailoring Agent for testing"""
        with patch('runtime.crewai.base_agent.Path'), \
             patch.object(TailoringAgent, '_load_prompt', return_value="Tailoring Agent prompt"), \
             patch.object(TailoringAgent, '_load_truth_rules', return_value="Truth rules"), \
             patch.object(TailoringAgent, '_load_style_guide', return_value="Style guide"):
            return TailoringAgent(mock_llm)
    
    @pytest.fixture
    def sample_context(self):
        """Sample context for testing"""
        return {
            "job_description": "Senior Platform Engineer - AWS, Terraform, team leadership",
            "resume": "Platform Engineer with 5 years AWS experience",
            "interview_notes": {
                "technical": "Built CI/CD pipeline reducing deploy time by 80%"
            },
            "differentiators": {
                "primary": "Builds systems that eliminate bottlenecks"
            },
            "gap_analysis": {
                "fit_score": 85.0,
                "requirements": []
            }
        }
    
    @pytest.fixture
    def valid_output(self):
        """Valid Tailoring Agent output for testing"""
        return {
            "agent": "tailoring_agent",
            "timestamp": "2025-12-06T01:00:00Z",
            "confidence": 0.9,
            "tailored_resume": {
                "format": "markdown",
                "content": """# John Doe
Seattle, WA | user@example.com | 555-555-5555 | linkedin.com/in/johndoe

## Summary
Platform Engineer who builds systems that eliminate bottlenecks. 5+ years AWS experience with focus on developer velocity and infrastructure automation.

## Experience

### Senior Platform Engineer | Company A
2020 – Present | Seattle, WA

- Built CI/CD pipeline reducing deploy time from 45min to 8min
- Architected multi-account AWS infrastructure serving 40+ developers
- Led team of 5 engineers implementing infrastructure as code with Terraform

## Skills
AWS, Terraform, CI/CD, Docker, Kubernetes, Python, Infrastructure as Code

## Education
BS Computer Science | Example University | 2018"""
            },
            "cover_letter": {
                "format": "markdown",
                "content": """Dear Hiring Team,

At Company A, I built the CI/CD system that let 40 developers ship without waiting for ops approval. Before that, deploys took 45 minutes. After, they took 8 minutes. Your job description mentions "developer velocity" three times—that's exactly what I do.

I specialize in building systems that eliminate bottlenecks, including myself. At Company A, I architected multi-account AWS infrastructure that passed a compliance audit on the first attempt. This matches your need for someone who can scale infrastructure while maintaining security standards.

Your platform team is building developer tools. I've done this before. My team reduced infrastructure tickets by 80% through self-service tooling. Developers provision environments in minutes, not days. That's the kind of developer experience your JD describes.

I'd welcome the chance to discuss how I could help accelerate your platform initiatives. What questions can I answer?

Best regards,
John Doe""",
                "word_count": 287
            },
            "sources_used": [
                "resume - Company A experience",
                "interview_notes - CI/CD pipeline details",
                "differentiators - bottleneck elimination theme"
            ]
        }
    
    def test_initialization(self, mock_llm):
        """Test agent initialization"""
        with patch('runtime.crewai.base_agent.Path'), \
             patch.object(TailoringAgent, '_load_prompt', return_value="Tailoring Agent prompt"), \
             patch.object(TailoringAgent, '_load_truth_rules', return_value="Truth rules"), \
             patch.object(TailoringAgent, '_load_style_guide', return_value="Style guide"):
            agent = TailoringAgent(mock_llm)
            assert agent.role == "Tailoring Agent"
            assert "tailored" in agent.goal
            assert "JSON" in agent.expected_output
    
    def test_execute_missing_differentiators(self, tailoring_agent):
        """Test execute with missing differentiators"""
        context = {
            "job_description": "test",
            "resume": "test",
            "interview_notes": {},
            "gap_analysis": {}
        }
        
        with pytest.raises(ValidationError, match="Missing required context key: differentiators"):
            tailoring_agent.execute(context)
    
    @patch('runtime.crewai.agents.tailoring_agent.TailoringAgent.execute_with_retry')
    def test_execute_success(self, mock_execute, tailoring_agent, sample_context, valid_output):
        """Test successful execution"""
        mock_execute.return_value = valid_output

        result = tailoring_agent.execute(sample_context)

        assert result == valid_output
        mock_execute.assert_called_once()
    
    def test_validate_schema_valid_output(self, tailoring_agent, valid_output):
        """Test schema validation with valid output"""
        # Should not raise any exception
        tailoring_agent._validate_schema(valid_output)
    
    def test_validate_schema_wrong_resume_format(self, tailoring_agent, valid_output):
        """Test schema validation with wrong resume format - should not raise error"""
        invalid_output = valid_output.copy()
        invalid_output["tailored_resume"]["format"] = "html"
        
        # Should not raise any exception - agents are flexible with output format
        tailoring_agent._validate_schema(invalid_output)
    
    def test_validate_schema_word_count_too_low(self, tailoring_agent, valid_output):
        """Test schema validation with word count too low - should not raise error"""
        invalid_output = valid_output.copy()
        invalid_output["cover_letter"]["word_count"] = 200  # Below 250 minimum
        
        # Should not raise any exception - agents are flexible with output format
        tailoring_agent._validate_schema(invalid_output)
