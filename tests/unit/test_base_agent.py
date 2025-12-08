"""
Unit tests for BaseHydraAgent.

Tests YAML validation, prompt loading, and error handling.
"""

import pytest
import yaml
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from runtime.crewai.base_agent import BaseHydraAgent, ValidationError
from crewai import LLM


class TestAgent(BaseHydraAgent):
    """Test implementation of BaseHydraAgent"""
    role = "Test Agent"
    goal = "Test goal"
    expected_output = "Test output"
    
    def execute(self, context):
        return {"result": "test"}


class TestBaseHydraAgent:
    """Test suite for BaseHydraAgent"""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM instance"""
        return Mock(spec=LLM)
    
    @pytest.fixture
    def test_agent(self, mock_llm):
        """Create a test agent instance"""
        return TestAgent(mock_llm)
    
    def test_agent_initialization(self, mock_llm):
        """Test agent initializes correctly"""
        agent = TestAgent(mock_llm)
        
        assert agent.llm == mock_llm
        assert agent.role == "Test Agent"
        assert agent.goal == "Test goal"
        assert agent.expected_output == "Test output"
    
    def test_validate_output_valid_yaml(self, test_agent):
        """Test validation of valid YAML output"""
        valid_output = """
agent: Test Agent
timestamp: 2024-01-01T00:00:00
confidence: 0.95
result: success
"""
        
        result = test_agent.validate_output(valid_output)
        
        assert result["agent"] == "Test Agent"
        assert result["confidence"] == 0.95
        assert result["result"] == "success"
    
    def test_validate_output_invalid_yaml(self, test_agent):
        """Test validation fails on invalid YAML"""
        invalid_output = """
agent: Test Agent
  invalid: indentation
    more: problems
"""
        
        with pytest.raises(ValidationError, match="Invalid YAML output"):
            test_agent.validate_output(invalid_output)
    
    def test_validate_output_missing_required_fields(self, test_agent):
        """Test validation fails when required fields are missing"""
        # Missing 'confidence' field
        incomplete_output = """
agent: Test Agent
timestamp: 2024-01-01T00:00:00
"""
        
        with pytest.raises(ValidationError, match="Missing required field: confidence"):
            test_agent.validate_output(incomplete_output)
    
    def test_validate_output_invalid_confidence(self, test_agent):
        """Test validation fails when confidence is out of range"""
        # Confidence > 1.0
        invalid_output = """
agent: Test Agent
timestamp: 2024-01-01T00:00:00
confidence: 1.5
"""
        
        with pytest.raises(ValidationError, match="Confidence must be between 0.0 and 1.0"):
            test_agent.validate_output(invalid_output)
    
    def test_validate_output_confidence_not_number(self, test_agent):
        """Test validation fails when confidence is not a number"""
        invalid_output = """
agent: Test Agent
timestamp: 2024-01-01T00:00:00
confidence: "high"
"""
        
        with pytest.raises(ValidationError, match="Confidence must be a number"):
            test_agent.validate_output(invalid_output)
    
    def test_validate_output_not_dict(self, test_agent):
        """Test validation fails when output is not a dictionary"""
        invalid_output = """
- item1
- item2
- item3
"""
        
        with pytest.raises(ValidationError, match="Output must be a YAML dictionary"):
            test_agent.validate_output(invalid_output)
    
    def test_create_agent(self, test_agent):
        """Test agent creation"""
        agent = test_agent.create_agent()
        
        assert agent.role == "Test Agent"
        assert agent.goal == "Test goal"
        assert agent.llm == test_agent.llm
    
    def test_create_task(self, test_agent):
        """Test task creation"""
        description = "Test task description"
        task = test_agent.create_task(description)
        
        assert task.description == description
        assert task.expected_output == "Test output"
        assert task.agent.role == "Test Agent"
    
    def test_create_task_with_context(self, test_agent):
        """Test task creation with context"""
        from crewai import Task
        
        description = "Test task description"
        # Create a real Task object for context instead of Mock
        context_agent = test_agent.create_agent()
        mock_context_task = Task(
            description="Context task",
            expected_output="Context output",
            agent=context_agent
        )
        
        task = test_agent.create_task(description, context=[mock_context_task])
        
        assert task.description == description
        assert len(task.context) == 1
        assert task.context[0] == mock_context_task
    
    def test_needs_style_guide_for_tailoring_agent(self, mock_llm):
        """Test that Tailoring Agent needs style guide"""
        class TailoringTestAgent(BaseHydraAgent):
            role = "Tailoring Agent"
            goal = "Test"
            expected_output = "Test"
            def execute(self, context):
                return {}
        
        agent = TailoringTestAgent(mock_llm)
        assert agent._needs_style_guide() is True
    
    def test_needs_style_guide_for_other_agent(self, mock_llm):
        """Test that other agents don't need style guide"""
        class OtherTestAgent(BaseHydraAgent):
            role = "Other Agent"
            goal = "Test"
            expected_output = "Test"
            def execute(self, context):
                return {}
        
        agent = OtherTestAgent(mock_llm)
        assert agent._needs_style_guide() is False
    
    @patch('runtime.crewai.base_agent.Crew')
    def test_execute_with_retry_success_first_attempt(self, mock_crew_class, test_agent):
        """Test execute_with_retry succeeds on first attempt"""
        # Mock the Crew instance and its kickoff method
        mock_crew_instance = Mock()
        mock_crew_instance.kickoff.return_value = """
agent: Test Agent
timestamp: 2024-01-01T00:00:00
confidence: 0.95
"""
        mock_crew_class.return_value = mock_crew_instance
        
        mock_task = Mock()
        mock_task.agent = Mock()
        
        result = test_agent.execute_with_retry(mock_task, max_retries=2)
        
        assert result["agent"] == "Test Agent"
        assert mock_crew_instance.kickoff.call_count == 1
    
    @patch('runtime.crewai.base_agent.Crew')
    def test_execute_with_retry_success_after_retry(self, mock_crew_class, test_agent):
        """Test execute_with_retry succeeds after retry"""
        # Mock the Crew instance and its kickoff method
        mock_crew_instance = Mock()
        # First call fails, second succeeds
        mock_crew_instance.kickoff.side_effect = [
            Exception("First attempt failed"),
            """
agent: Test Agent
timestamp: 2024-01-01T00:00:00
confidence: 0.95
"""
        ]
        mock_crew_class.return_value = mock_crew_instance
        
        mock_task = Mock()
        mock_task.agent = Mock()
        
        result = test_agent.execute_with_retry(mock_task, max_retries=2)
        
        assert result["agent"] == "Test Agent"
        assert mock_crew_instance.kickoff.call_count == 2
    
    @patch('runtime.crewai.base_agent.Crew')
    def test_execute_with_retry_fails_after_max_retries(self, mock_crew_class, test_agent):
        """Test execute_with_retry fails after max retries"""
        # Mock the Crew instance and its kickoff method
        mock_crew_instance = Mock()
        mock_crew_instance.kickoff.side_effect = Exception("Always fails")
        mock_crew_class.return_value = mock_crew_instance
        
        mock_task = Mock()
        mock_task.agent = Mock()
        
        with pytest.raises(ValidationError, match="failed after 3 attempts"):
            test_agent.execute_with_retry(mock_task, max_retries=2)
        
        assert mock_crew_instance.kickoff.call_count == 3
