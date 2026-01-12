"""
LLM client integration for Composable Me Hydra.

Handles OpenRouter LLM client configuration with error handling and retry logic.
"""

import os
import time
from typing import Optional
from crewai import LLM


class LLMClientError(Exception):
    """Raised when LLM client initialization or API calls fail"""
    pass


def get_llm_client(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_retries: int = 3,
    timeout: int = 60
) -> LLM:
    """
    Configure and return LLM client for CrewAI.
    
    Supports multiple providers:
    - Chutes.ai (CHUTES_API_KEY) - OpenAI-compatible gateway
    - OpenRouter (OPENROUTER_API_KEY) - Multi-model router
    
    Args:
        api_key: API key (checks CHUTES_API_KEY, then OPENROUTER_API_KEY)
        model: Model to use (defaults to env var or claude-sonnet-4.5)
        max_retries: Maximum number of retries for API failures
        timeout: Request timeout in seconds
        
    Returns:
        Configured LLM instance
        
    Raises:
        LLMClientError: If API key is missing or configuration fails
    """
    # Check for Together AI first (preferred)
    together_key = api_key or os.environ.get("TOGETHER_API_KEY")
    chutes_key = os.environ.get("CHUTES_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    
    if together_key:
        # Use Together AI (via LiteLLM)
        model = model or os.environ.get("TOGETHER_MODEL") or os.environ.get("OPENROUTER_MODEL", "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8")
        
        try:
            # LiteLLM requires together_ai/ prefix for Together AI models
            llm = LLM(
                model=f"together_ai/{model}",
                api_key=together_key,
                timeout=timeout,
                max_retries=max_retries,
            )
            return llm
        except Exception as e:
            raise LLMClientError(f"Failed to initialize Together AI LLM client: {e}")
    
    elif chutes_key:
        # Use Chutes.ai (OpenAI-compatible)
        model = model or os.environ.get("CHUTES_MODEL") or os.environ.get("OPENROUTER_MODEL", "deepseek-ai/DeepSeek-V3.1")
        
        try:
            # Chutes uses OpenAI-compatible API - prefix with openai/ for LiteLLM
            llm = LLM(
                model=f"openai/{model}",  # LiteLLM needs provider prefix
                api_key=chutes_key,
                base_url="https://api.chutes.ai/v1",
                timeout=timeout,
                max_retries=max_retries,
            )
            return llm
        except Exception as e:
            raise LLMClientError(f"Failed to initialize Chutes LLM client: {e}")
    
    elif openrouter_key:
        # Use OpenRouter
        if not openrouter_key.startswith("sk-or-"):
            raise LLMClientError(
                "Invalid OpenRouter API key format. "
                "Key should start with 'sk-or-'"
            )
        
        model = model or os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4.5")
        
        try:
            llm = LLM(
                model=f"openrouter/{model}",
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
                timeout=timeout,
                max_retries=max_retries,
            )
            return llm
        except Exception as e:
            raise LLMClientError(f"Failed to initialize OpenRouter LLM client: {e}")
    
    else:
        raise LLMClientError(
            "API key is required. Set one of:\n"
            "  export TOGETHER_API_KEY='tgp_v1_...'  (recommended)\n"
            "  export CHUTES_API_KEY='your-key'\n"
            "  export OPENROUTER_API_KEY='sk-or-...'\n"
            "Get Together AI key from: https://api.together.xyz/settings/api-keys\n"
            "Get Chutes key from: https://chutes.ai\n"
            "Get OpenRouter key from: https://openrouter.ai/keys"
        )


def test_llm_connection(llm: LLM) -> bool:
    """
    Test LLM connection with a simple prompt.
    
    Args:
        llm: LLM instance to test
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        # Simple test prompt
        from crewai import Agent, Task
        
        test_agent = Agent(
            role="Test Agent",
            goal="Test connection",
            backstory="Testing LLM connection",
            llm=llm,
            verbose=False
        )
        
        test_task = Task(
            description="Say 'Hello'",
            expected_output="A greeting",
            agent=test_agent
        )
        
        # Try to execute
        result = test_task.execute()
        
        return result is not None
        
    except Exception as e:
        print(f"LLM connection test failed: {e}")
        return False


def get_available_models() -> list[str]:
    """
    Get list of recommended models for Hydra.
    
    Returns:
        List of model identifiers
    """
    return [
        "anthropic/claude-sonnet-4.5",  # Default, latest and best
        "anthropic/claude-sonnet-4",  # Sonnet 4
        "anthropic/claude-3.7-sonnet",  # Claude 3.7 Sonnet
        "anthropic/claude-3.5-sonnet",  # Claude 3.5 Sonnet
        "anthropic/claude-3-opus",  # Highest quality, slower
        "openai/gpt-4o",  # Latest GPT-4
        "openai/gpt-4-turbo",  # Alternative provider
    ]


def validate_model_name(model: str) -> bool:
    """
    Validate model name format.
    
    Args:
        model: Model identifier to validate
        
    Returns:
        True if valid format, False otherwise
    """
    # Model should be in format: provider/model-name
    parts = model.split("/")
    
    if len(parts) != 2:
        return False
    
    provider, model_name = parts
    
    # Check provider is known
    valid_providers = {"anthropic", "openai", "google", "meta"}
    if provider not in valid_providers:
        return False
    
    # Check model name is not empty
    if not model_name:
        return False
    
    return True


class LLMRetryHandler:
    """Handle retries for LLM API failures with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """
        Initialize retry handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    def execute_with_retry(self, func, *args, **kwargs):
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                last_error = e
                
                if attempt < self.max_retries:
                    # Calculate backoff delay
                    delay = self.base_delay * (2 ** attempt)
                    delay = min(delay, 30.0)  # Cap at 30 seconds
                    
                    print(f"Retry {attempt + 1}/{self.max_retries} after {delay}s: {e}")
                    time.sleep(delay)
                    continue
                else:
                    break
        
        # All retries failed
        raise LLMClientError(
            f"Failed after {self.max_retries + 1} attempts: {last_error}"
        )
