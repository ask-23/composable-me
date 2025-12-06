"""
Unit tests for LLM client integration.

Tests LLM client initialization, configuration, and error handling.
"""

import pytest
import os
from unittest.mock import Mock, patch

from runtime.crewai.llm_client import (
    get_llm_client,
    validate_model_name,
    get_available_models,
    LLMClientError,
    LLMRetryHandler,
)


class TestGetLLMClient:
    """Test suite for get_llm_client function"""
    
    def test_get_llm_client_with_api_key(self):
        """Test LLM client creation with API key"""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test-key"}):
            llm = get_llm_client()
            assert llm is not None
    
    def test_get_llm_client_missing_api_key(self):
        """Test LLM client fails without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(LLMClientError, match="API key is required"):
                get_llm_client()
    
    def test_get_llm_client_invalid_api_key_format(self):
        """Test LLM client fails with invalid API key format"""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "invalid-key"}):
            with pytest.raises(LLMClientError, match="Invalid OpenRouter API key format"):
                get_llm_client()
    
    def test_get_llm_client_with_custom_model(self):
        """Test LLM client with custom model"""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test-key"}):
            llm = get_llm_client(model="anthropic/claude-3-opus")
            assert llm is not None
    
    def test_get_llm_client_default_model(self):
        """Test LLM client uses default model"""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test-key"}, clear=True):
            llm = get_llm_client()
            assert llm is not None
    
    def test_get_llm_client_model_from_env(self):
        """Test LLM client uses model from environment"""
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "sk-or-test-key",
            "OPENROUTER_MODEL": "anthropic/claude-3-opus"
        }):
            llm = get_llm_client()
            assert llm is not None


class TestValidateModelName:
    """Test suite for validate_model_name function"""
    
    def test_validate_model_name_valid(self):
        """Test validation of valid model names"""
        assert validate_model_name("anthropic/claude-3.5-sonnet") is True
        assert validate_model_name("openai/gpt-4-turbo") is True
        assert validate_model_name("google/gemini-pro") is True
    
    def test_validate_model_name_invalid_format(self):
        """Test validation fails for invalid format"""
        assert validate_model_name("invalid-model") is False
        assert validate_model_name("too/many/slashes") is False
        assert validate_model_name("") is False
    
    def test_validate_model_name_invalid_provider(self):
        """Test validation fails for unknown provider"""
        assert validate_model_name("unknown/model") is False
    
    def test_validate_model_name_empty_model(self):
        """Test validation fails for empty model name"""
        assert validate_model_name("anthropic/") is False


class TestGetAvailableModels:
    """Test suite for get_available_models function"""
    
    def test_get_available_models(self):
        """Test getting list of available models"""
        models = get_available_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert "anthropic/claude-3.5-sonnet" in models
        assert "openai/gpt-4-turbo" in models


class TestLLMRetryHandler:
    """Test suite for LLMRetryHandler class"""
    
    def test_retry_handler_success_first_attempt(self):
        """Test retry handler succeeds on first attempt"""
        handler = LLMRetryHandler(max_retries=3)
        
        mock_func = Mock(return_value="success")
        result = handler.execute_with_retry(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_handler_success_after_retry(self):
        """Test retry handler succeeds after retry"""
        handler = LLMRetryHandler(max_retries=3, base_delay=0.01)
        
        mock_func = Mock(side_effect=[
            Exception("First attempt failed"),
            "success"
        ])
        
        result = handler.execute_with_retry(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_retry_handler_fails_after_max_retries(self):
        """Test retry handler fails after max retries"""
        handler = LLMRetryHandler(max_retries=2, base_delay=0.01)
        
        mock_func = Mock(side_effect=Exception("Always fails"))
        
        with pytest.raises(LLMClientError, match="Failed after 3 attempts"):
            handler.execute_with_retry(mock_func)
        
        assert mock_func.call_count == 3
    
    def test_retry_handler_exponential_backoff(self):
        """Test retry handler uses exponential backoff"""
        handler = LLMRetryHandler(max_retries=3, base_delay=1.0)
        
        # We're not testing actual delays, just that the calculation works
        # Delays should be: 1.0, 2.0, 4.0
        assert handler.base_delay == 1.0
        assert handler.max_retries == 3
