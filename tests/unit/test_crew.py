import pytest
from unittest.mock import MagicMock, patch
from runtime.crewai.crew import HydraCrew

class TestHydraCrew:
    
    @pytest.fixture
    def mock_llm(self):
        return MagicMock()

    @pytest.fixture
    def mock_hydra_setup(self, mock_llm):
        with patch('runtime.crewai.crew.get_llm', return_value=mock_llm), \
             patch('runtime.crewai.crew.load_prompt', return_value="Test Prompt"), \
             patch('runtime.crewai.crew.load_docs', return_value={"AGENTS.MD": "Rules", "STYLE_GUIDE.MD": "Style"}), \
             patch('runtime.crewai.crew.Agent'), \
             patch('runtime.crewai.crew.Task'):
            yield

    def test_hydra_crew_initialization(self, mock_hydra_setup):
        """Test HydraCrew initializes agents correctly"""
        crew = HydraCrew(
            job_description="JD",
            resume_text="Resume",
            interview_notes="Notes"
        )
        
        # Verify agents created
        assert crew.commander is not None
        assert crew.gap_analyzer is not None
        assert crew.interrogator is not None
        assert crew.differentiator is not None
        assert crew.tailor is not None
        assert crew.auditor is not None

    def test_hydra_crew_build_tasks(self, mock_hydra_setup):
        """Test HydraCrew builds tasks correctly"""
        crew = HydraCrew(
            job_description="JD",
            resume_text="Resume",
        )
        
        tasks = crew.build_tasks()
        assert len(tasks) == 6

    def test_hydra_crew_run(self, mock_hydra_setup):
        """Test HydraCrew execution"""
        with patch('runtime.crewai.crew.Crew') as MockCrew:
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = "Result"
            MockCrew.return_value = mock_crew_instance
            
            crew = HydraCrew("JD", "Resume")
            result = crew.run()
            
            assert result["raw_output"] == "Result"
            MockCrew.assert_called_once()
