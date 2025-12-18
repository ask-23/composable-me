"""
Unit tests for BaseHydraAgent.

Tests JSON validation, prompt loading, and error handling.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from runtime.crewai.base_agent import BaseHydraAgent, ValidationError
from crewai import LLM

# Test constants
DEFAULT_CONFIDENCE = 0.8
VALID_CONFIDENCE_RANGE = (0.0, 1.0)
TEST_TIMESTAMP = "2024-01-01T00:00:00Z"


class _TestAgent(BaseHydraAgent):
    """Test implementation of BaseHydraAgent (prefixed with _ to avoid pytest collection)"""
    role = "Test Agent"
    goal = "Test goal"
    expected_output = "Test output"
    
    def execute(self, context):
        return {"result": "test"}


class TestBaseHydraAgent:
    """Test suite for BaseHydraAgent - Core functionality"""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM instance"""
        from crewai import LLM
        # Create a real LLM instance with minimal config for testing
        # This avoids validation errors when creating agents
        return LLM(model="gpt-4", api_key="test-key")
    
    @pytest.fixture
    def test_agent(self, mock_llm):
        """Create a test agent instance"""
        return _TestAgent(mock_llm)
    
    @pytest.fixture
    def valid_json_output(self):
        """Standard valid JSON output for testing"""
        return """{
    "agent": "Test Agent",
    "timestamp": "2024-01-01T00:00:00Z",
    "confidence": 0.95,
    "result": "success"
}"""
    
    @pytest.fixture
    def minimal_json_output(self):
        """Minimal JSON output without base fields"""
        return '{"result": "success"}'
    
    def test_agent_initialization(self, mock_llm):
        """Test agent initializes correctly"""
        agent = _TestAgent(mock_llm)
        
        assert agent.llm == mock_llm
        assert agent.role == "Test Agent"
        assert agent.goal == "Test goal"
        assert agent.expected_output == "Test output"
    
    def test_validate_output_valid_json(self, test_agent, valid_json_output):
        """Test validation of valid JSON output"""
        result = test_agent.validate_output(valid_json_output)
        
        assert result["agent"] == "Test Agent"
        assert result["confidence"] == 0.95
        assert result["result"] == "success"
    
    def test_validate_output_invalid_json(self, test_agent):
        """Test validation fails on invalid JSON"""
        invalid_output = """{
    "agent": "Test Agent",
    "invalid": "missing comma"
    "more": "problems"
}"""
        
        with pytest.raises(ValidationError, match="Invalid JSON output"):
            test_agent.validate_output(invalid_output)
    
    def test_validate_output_missing_required_fields(self, test_agent):
        """Test validation handles missing required fields by adding defaults"""
        # Missing 'confidence' field - should be added as default
        incomplete_output = """{
    "agent": "Test Agent",
    "timestamp": "2024-01-01T00:00:00"
}"""
        
        result = test_agent.validate_output(incomplete_output)
        
        # Should add default confidence
        assert result["agent"] == "Test Agent"
        assert result["confidence"] == DEFAULT_CONFIDENCE
    
    def test_validate_output_invalid_confidence(self, test_agent):
        """Test validation clamps confidence when out of range"""
        # Confidence > 1.0 - should be clamped to 1.0
        invalid_output = """{
    "agent": "Test Agent",
    "timestamp": "2024-01-01T00:00:00",
    "confidence": 1.5
}"""
        
        result = test_agent.validate_output(invalid_output)
        
        # Should clamp to 1.0
        assert result["confidence"] == 1.0
    
    def test_validate_output_confidence_not_number(self, test_agent):
        """Test validation handles non-numeric confidence by using default"""
        invalid_output = """{
    "agent": "Test Agent",
    "timestamp": "2024-01-01T00:00:00",
    "confidence": "high"
}"""
        
        result = test_agent.validate_output(invalid_output)
        
        # Should use default confidence when conversion fails
        assert result["confidence"] == DEFAULT_CONFIDENCE
    
    def test_validate_output_not_dict(self, test_agent):
        """Test validation fails when output is not a dictionary"""
        invalid_output = """[
    "item1",
    "item2", 
    "item3"
]"""
        
        with pytest.raises(ValidationError, match="Output must be a JSON object"):
            test_agent.validate_output(invalid_output)
    
    def test_validate_output_with_markdown_fences(self, test_agent):
        """Test validation handles JSON wrapped in markdown code fences"""
        output_with_fences = """```json
{
    "agent": "Test Agent",
    "timestamp": "2024-01-01T00:00:00",
    "confidence": 0.95,
    "result": "success"
}
```"""
        
        result = test_agent.validate_output(output_with_fences)
        
        assert result["agent"] == "Test Agent"
        assert result["confidence"] == 0.95
        assert result["result"] == "success"
    
    def test_validate_output_with_surrounding_text(self, test_agent):
        """Test validation extracts JSON from surrounding text"""
        output_with_text = """Here is my analysis:

{
    "agent": "Test Agent",
    "timestamp": "2024-01-01T00:00:00",
    "confidence": 0.95,
    "result": "success"
}

That completes the analysis."""
        
        result = test_agent.validate_output(output_with_text)
        
        assert result["agent"] == "Test Agent"
        assert result["confidence"] == 0.95
        assert result["result"] == "success"
    
    def test_validate_output_nested_structure_promotion(self, test_agent):
        """Test validation promotes base fields from nested structure"""
        nested_output = """{
    "analysis": {
        "agent": "Test Agent",
        "timestamp": "2024-01-01T00:00:00",
        "confidence": 0.95,
        "findings": ["item1", "item2"]
    }
}"""
        
        result = test_agent.validate_output(nested_output)
        
        # Base fields should be promoted to top level
        assert result["agent"] == "Test Agent"
        assert result["confidence"] == 0.95
        assert result["analysis"]["findings"] == ["item1", "item2"]
    
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
        
        # Description should be enhanced with JSON format instructions
        assert description in task.description
        assert "valid JSON" in task.description
        assert "agent" in task.description
        assert "timestamp" in task.description
        assert "confidence" in task.description
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
        
        # Description should be enhanced with JSON format instructions
        assert description in task.description
        assert "valid JSON" in task.description
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
        mock_crew_instance.kickoff.return_value = """{
    "agent": "Test Agent",
    "timestamp": "2024-01-01T00:00:00",
    "confidence": 0.95
}"""
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
            """{
    "agent": "Test Agent",
    "timestamp": "2024-01-01T00:00:00",
    "confidence": 0.95
}"""
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
    
    # Additional tests for comprehensive base field handling
    
    def test_validate_output_missing_all_base_fields(self, test_agent, minimal_json_output):
        """Test validation adds all missing base fields with defaults"""
        result = test_agent.validate_output(minimal_json_output)
        
        # Should add all base fields with defaults
        assert result["agent"] == "Test Agent"  # From agent role
        assert "timestamp" in result  # Should be added
        assert result["confidence"] == DEFAULT_CONFIDENCE
        assert result["result"] == "success"  # Original data preserved
    
    def test_validate_output_missing_agent_field(self, test_agent):
        """Test validation adds missing agent field from role"""
        output_missing_agent = """{
    "timestamp": "2024-01-01T00:00:00Z",
    "confidence": 0.95,
    "result": "success"
}"""
        
        result = test_agent.validate_output(output_missing_agent)
        
        # Should add agent field from role
        assert result["agent"] == "Test Agent"
        assert result["timestamp"] == "2024-01-01T00:00:00Z"
        assert result["confidence"] == 0.95
        assert result["result"] == "success"
    
    def test_validate_output_missing_timestamp_field(self, test_agent):
        """Test validation adds missing timestamp field"""
        output_missing_timestamp = """{
    "agent": "Test Agent",
    "confidence": 0.95,
    "result": "success"
}"""
        
        result = test_agent.validate_output(output_missing_timestamp)
        
        # Should add timestamp field
        assert result["agent"] == "Test Agent"
        assert "timestamp" in result  # Should be added with current time
        assert result["timestamp"].endswith("Z")  # Should be ISO format with Z
        assert result["confidence"] == 0.95
        assert result["result"] == "success"
    
    def test_validate_output_confidence_string_conversion(self, test_agent):
        """Test validation converts string confidence to float"""
        output_string_confidence = """{
    "agent": "Test Agent",
    "timestamp": "2024-01-01T00:00:00Z",
    "confidence": "0.75",
    "result": "success"
}"""
        
        result = test_agent.validate_output(output_string_confidence)
        
        # Should convert string to float
        assert result["confidence"] == 0.75
        assert isinstance(result["confidence"], float)
    
    @pytest.mark.parametrize("input_confidence,expected_confidence,description", [
        (-0.5, 0.0, "negative confidence should be clamped to 0.0"),
        (0.0, 0.0, "zero confidence should be accepted"),
        (1.0, 1.0, "one confidence should be accepted"),
        (1.5, 1.0, "confidence > 1.0 should be clamped to 1.0"),
        (0.75, 0.75, "valid confidence should be preserved"),
    ])
    def test_validate_output_confidence_clamping(self, test_agent, input_confidence, expected_confidence, description):
        """Test validation clamps confidence values to valid range [0.0, 1.0]"""
        output = f"""{{
    "agent": "Test Agent",
    "timestamp": "2024-01-01T00:00:00Z",
    "confidence": {input_confidence},
    "result": "success"
}}"""
        
        result = test_agent.validate_output(output)
        assert result["confidence"] == expected_confidence, description
    
    def test_validate_output_confidence_invalid_string(self, test_agent):
        """Test validation handles invalid confidence string with default"""
        output_invalid_confidence = """{
    "agent": "Test Agent",
    "timestamp": "2024-01-01T00:00:00Z",
    "confidence": "not_a_number",
    "result": "success"
}"""
        
        result = test_agent.validate_output(output_invalid_confidence)
        
        # Should use default confidence when conversion fails
        assert result["confidence"] == DEFAULT_CONFIDENCE
    
    def test_validate_output_base_fields_preserved_with_additional_data(self, test_agent):
        """Test validation preserves base fields when additional data is present"""
        complex_output = """{
    "agent": "Test Agent",
    "timestamp": "2024-01-01T00:00:00Z",
    "confidence": 0.92,
    "analysis": {
        "findings": ["item1", "item2"],
        "score": 85
    },
    "recommendations": ["rec1", "rec2"],
    "metadata": {
        "version": "1.0",
        "source": "test"
    }
}"""
        
        result = test_agent.validate_output(complex_output)
        
        # Base fields should be preserved
        assert result["agent"] == "Test Agent"
        assert result["timestamp"] == "2024-01-01T00:00:00Z"
        assert result["confidence"] == 0.92
        
        # Additional data should be preserved
        assert result["analysis"]["findings"] == ["item1", "item2"]
        assert result["analysis"]["score"] == 85
        assert result["recommendations"] == ["rec1", "rec2"]
        assert result["metadata"]["version"] == "1.0"
    
    def test_validate_output_nested_base_fields_multiple_keys(self, test_agent):
        """Test validation handles nested base fields when multiple top-level keys exist"""
        # When there are multiple top-level keys, base fields should not be promoted
        multi_key_output = """{
    "analysis": {
        "agent": "Nested Agent",
        "timestamp": "2024-01-01T00:00:00Z",
        "confidence": 0.95,
        "findings": ["item1"]
    },
    "summary": {
        "total": 1
    }
}"""
        
        result = test_agent.validate_output(multi_key_output)
        
        # Base fields should be added at top level with defaults (not promoted from nested)
        assert result["agent"] == "Test Agent"  # From agent role, not nested
        assert "timestamp" in result  # Added as default
        assert result["confidence"] == DEFAULT_CONFIDENCE
        
        # Nested data should be preserved
        assert result["analysis"]["agent"] == "Nested Agent"
        assert result["analysis"]["findings"] == ["item1"]
        assert result["summary"]["total"] == 1


class TestJSONValidation:
    """Test suite focused on JSON validation edge cases"""
    
    @pytest.fixture
    def test_agent(self):
        """Create a test agent instance for validation tests"""
        from crewai import LLM
        mock_llm = LLM(model="gpt-4", api_key="test-key")
        return _TestAgent(mock_llm)
    
    @pytest.mark.parametrize("invalid_json,expected_error", [
        ('{"missing": "comma" "invalid": true}', "Invalid JSON output"),
        ('["not", "an", "object"]', "Output must be a JSON object"),
        ('not json at all', "Invalid JSON output"),
        ('{"unclosed": "brace"', "Invalid JSON output"),
    ])
    def test_invalid_json_formats(self, test_agent, invalid_json, expected_error):
        """Test various invalid JSON formats raise appropriate errors"""
        with pytest.raises(ValidationError, match=expected_error):
            test_agent.validate_output(invalid_json)
    
    @pytest.mark.parametrize("wrapped_json", [
        '```json\n{"agent": "Test", "confidence": 0.9}\n```',
        '```\n{"agent": "Test", "confidence": 0.9}\n```',
        'Here is the result:\n{"agent": "Test", "confidence": 0.9}\nDone.',
    ])
    def test_json_extraction_from_text(self, test_agent, wrapped_json):
        """Test JSON extraction from various text wrappers"""
        result = test_agent.validate_output(wrapped_json)
        assert result["agent"] == "Test"
        assert result["confidence"] == 0.9
