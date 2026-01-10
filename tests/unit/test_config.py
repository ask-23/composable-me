"""
Unit tests for configuration management.

Tests configuration loading from environment and validation.
"""

import pytest
import os
from unittest.mock import patch

from runtime.crewai.config import HydraConfig


class TestHydraConfig:
    """Test suite for HydraConfig"""
    
    def test_config_from_env_with_api_key(self):
        """Test loading config from environment with API key"""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test-key"}):
            config = HydraConfig.from_env()
            
            assert config.openrouter_api_key == "sk-or-test-key"
            assert config.openrouter_model == "anthropic/claude-sonnet-4.5"
    
    def test_config_from_env_missing_api_key(self):
        """Test config fails without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY environment variable required"):
                HydraConfig.from_env()
    
    def test_config_from_env_custom_model(self):
        """Test loading config with custom model"""
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "sk-or-test-key",
            "OPENROUTER_MODEL": "anthropic/claude-3-opus"
        }):
            config = HydraConfig.from_env()
            
            assert config.openrouter_model == "anthropic/claude-3-opus"
    
    def test_config_from_env_custom_settings(self):
        """Test loading config with custom settings"""
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "sk-or-test-key",
            "ENABLE_RESEARCH": "false",
            "AUTO_GREENLIGHT_THRESHOLD": "0.75",
            "MAX_AGENT_RETRIES": "2",
            "MAX_AUDIT_RETRIES": "3"
        }):
            config = HydraConfig.from_env()
            
            assert config.enable_research_agent is False
            assert config.auto_greenlight_threshold == 0.75
            assert config.max_agent_retries == 2
            assert config.max_audit_retries == 3
    
    def test_config_validate_success(self):
        """Test config validation succeeds with valid values"""
        config = HydraConfig(
            openrouter_api_key="sk-or-test-key",
            openrouter_model="anthropic/claude-3.5-sonnet",
            auto_greenlight_threshold=0.6,
            max_agent_retries=1,
            max_audit_retries=2
        )
        
        # Should not raise
        config.validate()
    
    def test_config_validate_missing_api_key(self):
        """Test config validation fails without API key"""
        config = HydraConfig(
            openrouter_api_key="",
            openrouter_model="anthropic/claude-3.5-sonnet"
        )
        
        with pytest.raises(ValueError, match="OpenRouter API key is required"):
            config.validate()
    
    def test_config_validate_invalid_threshold(self):
        """Test config validation fails with invalid threshold"""
        config = HydraConfig(
            openrouter_api_key="sk-or-test-key",
            auto_greenlight_threshold=1.5
        )
        
        with pytest.raises(ValueError, match="Auto greenlight threshold must be between 0.0 and 1.0"):
            config.validate()
    
    def test_config_validate_negative_retries(self):
        """Test config validation fails with negative retries"""
        config = HydraConfig(
            openrouter_api_key="sk-or-test-key",
            max_agent_retries=-1
        )
        
        with pytest.raises(ValueError, match="Max agent retries must be non-negative"):
            config.validate()
    
    def test_config_validate_invalid_timeout(self):
        """Test config validation fails with invalid timeout"""
        config = HydraConfig(
            openrouter_api_key="sk-or-test-key",
            fit_analysis_timeout=0
        )
        
        with pytest.raises(ValueError, match="Fit analysis timeout must be positive"):
            config.validate()
    
    def test_config_validate_invalid_output_format(self):
        """Test config validation fails with invalid output format"""
        config = HydraConfig(
            openrouter_api_key="sk-or-test-key",
            output_format="invalid"
        )
        
        with pytest.raises(ValueError, match="Output format must be one of"):
            config.validate()
    
    def test_config_default_values(self):
        """Test config has correct default values"""
        config = HydraConfig(openrouter_api_key="sk-or-test-key")
        
        assert config.openrouter_model == "anthropic/claude-sonnet-4.5"
        assert config.enable_research_agent is True
        assert config.auto_greenlight_threshold == 0.60
        assert config.max_agent_retries == 1
        assert config.max_audit_retries == 2
        assert config.fit_analysis_timeout == 60
        assert config.document_generation_timeout == 180
        assert config.output_format == "markdown"
        assert config.include_audit_trail is True
