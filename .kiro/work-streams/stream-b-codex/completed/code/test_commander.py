"""
Unit tests for the Commander Agent
"""

import unittest
from unittest.mock import Mock, patch
from runtime.crewai.agents.commander import CommanderAgent
from runtime.crewai.base_agent import ValidationError


class TestCommanderAgent(unittest.TestCase):
    """Test cases for the CommanderAgent class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_llm = Mock()
        self.agent = CommanderAgent(self.mock_llm)
    
    def test_validate_schema_valid_output(self):
        """Test that valid output passes schema validation"""
        valid_output = {
            "agent": "Commander",
            "timestamp": "2024-12-06T00:00:00Z",
            "confidence": 0.95,
            "action": "proceed",
            "fit_analysis": {
                "fit_percentage": 85,
                "auto_reject_triggered": False,
                "red_flags": []
            },
            "next_step": "Send to Interrogator for detailed analysis"
        }
        
        # Should not raise an exception
        self.agent._validate_schema(valid_output)
    
    def test_validate_schema_invalid_action(self):
        """Test that invalid action raises ValidationError"""
        invalid_output = {
            "action": "invalid_action",
            "fit_analysis": {
                "fit_percentage": 85,
                "auto_reject_triggered": False,
                "red_flags": []
            },
            "next_step": "Send to Interrogator for detailed analysis"
        }
        
        with self.assertRaises(ValidationError):
            self.agent._validate_schema(invalid_output)
    
    def test_validate_schema_missing_fields(self):
        """Test that missing required fields raise ValidationError"""
        invalid_output = {
            "action": "proceed",
            # Missing fit_analysis
            "next_step": "Send to Interrogator for detailed analysis"
        }
        
        with self.assertRaises(ValidationError):
            self.agent._validate_schema(invalid_output)
    
    def test_validate_schema_invalid_fit_percentage(self):
        """Test that invalid fit_percentage raises ValidationError"""
        invalid_output = {
            "action": "proceed",
            "fit_analysis": {
                "fit_percentage": 150,  # Invalid value
                "auto_reject_triggered": False,
                "red_flags": []
            },
            "next_step": "Send to Interrogator for detailed analysis"
        }
        
        with self.assertRaises(ValidationError):
            self.agent._validate_schema(invalid_output)
    
    def test_validate_schema_invalid_auto_reject_type(self):
        """Test that invalid auto_reject_triggered type raises ValidationError"""
        invalid_output = {
            "action": "proceed",
            "fit_analysis": {
                "fit_percentage": 85,
                "auto_reject_triggered": "false",  # Should be boolean
                "red_flags": []
            },
            "next_step": "Send to Interrogator for detailed analysis"
        }
        
        with self.assertRaises(ValidationError):
            self.agent._validate_schema(invalid_output)
    
    def test_compute_fit_percentage_all_direct_matches(self):
        """Test fit percentage calculation with all direct matches"""
        gap_output = {
            "requirements": [
                {"classification": "direct_match"},
                {"classification": "direct_match"},
                {"classification": "direct_match"}
            ]
        }
        
        percentage = self.agent._compute_fit_percentage(gap_output)
        self.assertEqual(percentage, 100.0)
    
    def test_compute_fit_percentage_mixed_classifications(self):
        """Test fit percentage calculation with mixed classifications"""
        gap_output = {
            "requirements": [
                {"classification": "direct_match"},      # +1.0
                {"classification": "adjacent_experience"}, # +0.7
                {"classification": "gap"},               # -0.5
                {"classification": "blocker"}            # -1.0
            ]
        }
        
        # Expected: (1.0 + 0.7 - 0.5 - 1.0) / (4 * 1.0) * 100 = 0.2/4 * 100 = 5.0
        percentage = self.agent._compute_fit_percentage(gap_output)
        self.assertAlmostEqual(percentage, 5.0, places=1)
    
    def test_check_auto_reject_contract_to_hire(self):
        """Test auto-reject detection for contract-to-hire positions"""
        job_description = "This is a contract-to-hire position with potential for permanent employment."
        
        reasons = self.agent._check_auto_reject(job_description)
        self.assertIn("Contract-to-hire position detected", reasons)
    
    def test_check_auto_reject_missing_compensation(self):
        """Test auto-reject detection for missing compensation info"""
        job_description = "We are looking for a software engineer to join our team."
        
        reasons = self.agent._check_auto_reject(job_description)
        self.assertIn("No compensation information provided", reasons)
    
    def test_generate_red_flags_vague_description(self):
        """Test red flag generation for vague job descriptions"""
        job_description = "Assorted projects and general duties as assigned."
        research_data = {}
        
        red_flags = self.agent._generate_red_flags(job_description, research_data)
        self.assertIn("Vague job description with unclear responsibilities", red_flags)
    
    def test_execute_missing_context(self):
        """Test that execute raises ValidationError for missing context"""
        incomplete_context = {
            "job_description": "Some job",
            # Missing resume and gap_analysis
        }
        
        with self.assertRaises(ValidationError):
            self.agent.execute(incomplete_context)
    
    def test_validate_schema_invalid_red_flags_type(self):
        """Test that invalid red_flags type raises ValidationError"""
        invalid_output = {
            "action": "proceed",
            "fit_analysis": {
                "fit_percentage": 85,
                "auto_reject_triggered": False,
                "red_flags": "not a list"  # Should be list
            },
            "next_step": "Send to Interrogator for detailed analysis"
        }
        
        with self.assertRaises(ValidationError):
            self.agent._validate_schema(invalid_output)
    
    def test_validate_schema_invalid_next_step_type(self):
        """Test that invalid next_step type raises ValidationError"""
        invalid_output = {
            "action": "proceed",
            "fit_analysis": {
                "fit_percentage": 85,
                "auto_reject_triggered": False,
                "red_flags": []
            },
            "next_step": 123  # Should be string
        }
        
        with self.assertRaises(ValidationError):
            self.agent._validate_schema(invalid_output)


if __name__ == '__main__':
    unittest.main()