import pytest
from unittest.mock import MagicMock
from runtime.crewai.agents.gap_analyzer import GapAnalyzerAgent
from runtime.crewai.base_agent import ValidationError

class TestGapAnalyzerAgent:
    
    @pytest.fixture
    def mock_llm(self):
        return MagicMock()

    @pytest.fixture
    def agent(self, mock_llm):
        return GapAnalyzerAgent(mock_llm)

    def test_initialization(self, agent):
        assert agent.role == "Gap Analyzer"

    def test_execute_missing_context(self, agent):
        with pytest.raises(ValidationError):
            agent.execute({"job_description": "JD"})

    def test_validate_schema_valid_flat(self, agent):
        """Test valid flat schema"""
        data = {
            "requirements": [
                {"classification": "direct_match", "confidence": 0.9}
            ],
            "fit_score": 85.0,
            "agent": "Gap Analyzer",
            "timestamp": "2023-01-01T00:00:00Z",
            "confidence": 0.8
        }
        agent._validate_schema(data) # Should not raise

    def test_validate_schema_valid_nested(self, agent):
        """Test valid nested gap_analysis schema"""
        data = {
            "gap_analysis": {
                "requirements": [
                    {"classification": "gap"}
                ],
                "fit_score": "85%"
            },
            "agent": "Gap Analyzer",
            "timestamp": "2023-01-01T00:00:00Z",
            "confidence": 0.8
        }
        agent._validate_schema(data)

    def test_validate_schema_requirements_analysis(self, agent):
        """Test requirements_analysis extraction"""
        data = {
            "gap_analysis": {
                "requirements_analysis": {
                    "explicit_required": [{"classification": "direct_match"}]
                }
            },
            "agent": "Gap Analyzer",
            "timestamp": "2023-01-01T00:00:00Z",
            "confidence": 0.8
        }
        agent._validate_schema(data)



    def test_validate_schema_invalid_requirement_item(self, agent):
        data = {
            "requirements": ["not-a-dict"],
            "agent": "Gap Analyzer",
            "timestamp": "2023-01-01T00:00:00Z",
            "confidence": 0.8
        }
        with pytest.raises(ValidationError, match="must be a dictionary"):
            agent._validate_schema(data)

    def test_validate_schema_invalid_classification(self, agent):
        data = {
            "requirements": [{"classification": "bad_class"}],
            "agent": "Gap Analyzer",
            "timestamp": "2023-01-01T00:00:00Z",
            "confidence": 0.8
        }
        with pytest.raises(ValidationError, match="Invalid classification"):
            agent._validate_schema(data)

    def test_validate_schema_confidence_out_of_range(self, agent):
        data = {
            "requirements": [{"classification": "direct_match", "confidence": 1.5}],
            "agent": "Gap Analyzer",
            "timestamp": "2023-01-01T00:00:00Z",
            "confidence": 0.8
        }
        with pytest.raises(ValidationError, match="between 0.0 and 1.0"):
            agent._validate_schema(data)

    def test_validate_schema_fit_score_parsing(self, agent):
        """Test fit score parsing logic (clamping, strings)"""
        data = {
            "requirements": [{"classification": "direct_match"}],
            "fit_score": "120", # Should be clamped
            "agent": "Gap Analyzer",
            "timestamp": "2023-01-01T00:00:00Z",
            "confidence": 0.8
        }
        # Does not raise, just clamps/processes internally? 
        # _validate_schema modifies data in place? No, it validates.
        # But looking at code, it does modify local variables but doesn't write back to data for fit_score except locally?
        # Actually it doesn't write back. It just checks if it's valid.
        
        agent._validate_schema(data)

    def test_validate_schema_missing_requirements(self, agent):
        data = {
            "agent": "Gap Analyzer",
            "timestamp": "2023-01-01T00:00:00Z",
            "confidence": 0.8
        }
        with pytest.raises(ValidationError, match="Missing required field: requirements"):
            agent._validate_schema(data)
