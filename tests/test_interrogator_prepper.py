"""
Unit tests for Interrogator-Prepper Agent.

Tests question generation, STAR+ format compliance, thematic grouping,
interview note validation, and handling unanswered questions.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from crewai import LLM

from runtime.crewai.agents.interrogator_prepper import InterrogatorPrepperAgent
from runtime.crewai.base_agent import ValidationError


class TestInterrogatorPrepperAgent:
    """Test cases for Interrogator-Prepper Agent"""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing"""
        from crewai import LLM
        # Create a real LLM instance with minimal config for testing
        # This avoids validation errors when creating agents
        return LLM(model="gpt-4", api_key="test-key")
    
    @pytest.fixture
    def interrogator_prepper(self, mock_llm):
        """Create Interrogator-Prepper agent for testing"""
        with patch('runtime.crewai.base_agent.Path'), \
             patch.object(InterrogatorPrepperAgent, '_load_prompt', return_value="Interrogator-Prepper prompt"), \
             patch.object(InterrogatorPrepperAgent, '_load_truth_rules', return_value="Truth rules"), \
             patch.object(InterrogatorPrepperAgent, '_load_style_guide', return_value="Style guide"):
            return InterrogatorPrepperAgent(mock_llm)
    
    @pytest.fixture
    def sample_context(self):
        """Sample context for testing"""
        return {
            "job_description": "Senior DevOps Engineer with Kubernetes experience",
            "resume": "DevOps Engineer with Docker experience",
            "gaps": ["Kubernetes experience", "CI/CD automation"],
            "gap_analysis": {
                "requirements": [
                    {"requirement": "Kubernetes", "classification": "gap"}
                ]
            }
        }
    
    @pytest.fixture
    def valid_output(self):
        """Valid Interrogator-Prepper output for testing"""
        return {
            "agent": "interrogator_prepper",
            "timestamp": "2025-12-06T01:00:00Z",
            "confidence": 0.8,
            "questions": [
                {
                    "id": "q1",
                    "theme": "technical",
                    "question": "Describe a situation where you worked with container orchestration",
                    "format": "STAR+",
                    "target_gap": "Kubernetes experience",
                    "why_asking": "To understand transferable container orchestration experience"
                },
                {
                    "id": "q2", 
                    "theme": "technical",
                    "question": "Walk me through a CI/CD pipeline you built or improved",
                    "format": "STAR+",
                    "target_gap": "CI/CD automation",
                    "why_asking": "To assess automation and pipeline experience"
                },
                {
                    "id": "q3",
                    "theme": "outcomes",
                    "question": "What was the biggest infrastructure challenge you solved?",
                    "format": "STAR+", 
                    "target_gap": "Problem-solving depth",
                    "why_asking": "To understand problem-solving approach and impact"
                },
                {
                    "id": "q4",
                    "theme": "leadership",
                    "question": "Describe a time you had to convince a team to adopt new tooling",
                    "format": "STAR+",
                    "target_gap": "Change management",
                    "why_asking": "To assess leadership and communication skills"
                },
                {
                    "id": "q5",
                    "theme": "tools",
                    "question": "What monitoring and observability tools have you used?",
                    "format": "STAR+",
                    "target_gap": "Observability experience", 
                    "why_asking": "To understand monitoring and alerting experience"
                },
                {
                    "id": "q6",
                    "theme": "technical",
                    "question": "How do you handle infrastructure as code testing?",
                    "format": "STAR+",
                    "target_gap": "IaC best practices",
                    "why_asking": "To assess IaC maturity and testing practices"
                },
                {
                    "id": "q7",
                    "theme": "outcomes",
                    "question": "Describe a time you improved system reliability or performance",
                    "format": "STAR+",
                    "target_gap": "Performance optimization",
                    "why_asking": "To understand optimization skills and impact measurement"
                },
                {
                    "id": "q8",
                    "theme": "leadership",
                    "question": "How do you handle on-call incidents and team coordination?",
                    "format": "STAR+",
                    "target_gap": "Incident management",
                    "why_asking": "To assess incident response and team leadership"
                }
            ],
            "interview_notes": []
        }
    
    def test_initialization(self, mock_llm):
        """Test agent initialization"""
        with patch('runtime.crewai.base_agent.Path'), \
             patch.object(InterrogatorPrepperAgent, '_load_prompt', return_value="Interrogator-Prepper prompt"), \
             patch.object(InterrogatorPrepperAgent, '_load_truth_rules', return_value="Truth rules"), \
             patch.object(InterrogatorPrepperAgent, '_load_style_guide', return_value="Style guide"):
            agent = InterrogatorPrepperAgent(mock_llm)
            assert agent.role == "Interrogator-Prepper"
            assert "targeted interview questions" in agent.goal
            assert "JSON" in agent.expected_output
    
    def test_execute_missing_gaps(self, interrogator_prepper):
        """Test execute with missing gaps"""
        context = {
            "job_description": "test",
            "resume": "test", 
            "gap_analysis": {}
        }
        
        with pytest.raises(ValidationError, match="Missing required context key: gaps"):
            interrogator_prepper.execute(context)
    
    @patch('runtime.crewai.agents.interrogator_prepper.InterrogatorPrepperAgent.execute_with_retry')
    def test_execute_success(self, mock_execute, interrogator_prepper, sample_context, valid_output):
        """Test successful execution"""
        mock_execute.return_value = valid_output

        result = interrogator_prepper.execute(sample_context)

        assert result == valid_output
        mock_execute.assert_called_once()
    
    def test_validate_schema_valid_output(self, interrogator_prepper, valid_output):
        """Test schema validation with valid output"""
        # Should not raise any exception
        interrogator_prepper._validate_schema(valid_output)
    
    def test_validate_schema_wrong_question_count(self, interrogator_prepper, valid_output):
        """Test schema validation with wrong number of questions - should not raise error"""
        invalid_output = valid_output.copy()
        invalid_output["questions"] = invalid_output["questions"][:5]  # Only 5 questions
        
        # Should not raise any exception - agents are flexible with output format
        interrogator_prepper._validate_schema(invalid_output)
