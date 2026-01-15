"""
Model configuration for Composable Me Hydra agents.
Strategic assignment: cost, quality, privacy (TEE where available).

Design Principles:
1. Right-size the model to the task — Don't use frontier models for mechanical work
2. TEE for privacy — Use Trusted Execution Environments when processing PII (resumes)
3. Human voice where it matters — Claude for candidate-facing content
4. Deep reasoning for verification — R1 for audit tasks
5. Frontier for synthesis — Opus for executive-level cross-document reasoning
"""

import os
from typing import Dict, Any, Optional
from crewai import LLM


AGENT_MODELS: Dict[str, Dict[str, Any]] = {
    # ═══════════════════════════════════════════════════════════════════════
    # COST-EFFECTIVE TIER — Structured analysis, classification, templates
    # Provider: Chutes.ai (TEE) or Together.ai
    # ═══════════════════════════════════════════════════════════════════════
    
    "gap_analyzer": {
        "provider": "chutes",
        "model": "deepseek-ai/DeepSeek-V3",
        "base_url": "https://llm.chutes.ai/v1",  # Correct endpoint
        "temperature": 0.3,  # Lower for consistent classification
        "rationale": """
            Task: Extract requirements from JD, map to resume, classify fit.
            Why V3: Structured analysis doesn't need frontier reasoning.
            Why TEE: Processing resume PII — hardware-protected privacy.
        """
    },
    
    "ats_optimizer": {
        "provider": "together",
        "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "temperature": 0.2,
        "rationale": """
            Task: Keyword extraction, format verification, ATS compatibility.
            Why Llama 4 Maverick: MoE efficiency, strong instruction following.
        """
    },
    
    "interrogator_prepper": {
        "provider": "together",
        "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "temperature": 0.5,
        "rationale": """
            Task: Generate STAR+ interview questions based on gaps.
            Why Llama 4 Maverick: Better reasoning for interview prep.
        """
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # CREATIVE/WRITING TIER — Human voice, narrative, candidate-facing
    # Provider: Anthropic (Claude) or fallback to Together
    # ═══════════════════════════════════════════════════════════════════════
    
    "differentiator": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "fallback_provider": "together",
        "fallback_model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "temperature": 0.7,
        "rationale": """
            Task: Find narrative threads, rare skill combos, positioning angles.
            Why Sonnet: Creative synthesis requires genuine insight.
        """
    },
    
    "tailoring_agent": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "fallback_provider": "together",
        "fallback_model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "temperature": 0.6,
        "rationale": """
            Task: Generate tailored resume and cover letter.
            Why Sonnet: CRITICAL — This is what hiring managers see.
                - Best natural sentence variation (anti-AI detection)
                - Authentic senior engineer voice
        """
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # REASONING TIER — Verification, compliance, deep analysis
    # Provider: OpenAI (GPT-5 mini) for reliable verification
    # ═══════════════════════════════════════════════════════════════════════
    
    "auditor_suite": {
        "provider": "openai",
        "model": "gpt-4o-mini",  # Compatible with LiteLLM, reliable verification
        "fallback_provider": "together",
        "fallback_model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "temperature": 0.2,  # Low for consistent verification
        "rationale": """
            Task: 4-part audit — truth, tone, ATS, compliance verification.
            Why GPT-5 mini: Reliable instruction following, less prone to hallucinating violations.
        """
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # FRONTIER TIER — Executive synthesis, strategic intelligence
    # Provider: Anthropic (Claude Opus) or fallback
    # ═══════════════════════════════════════════════════════════════════════
    
    "executive_synthesizer": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",  # Using Sonnet as Opus may not be available
        "fallback_provider": "together",
        "fallback_model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "temperature": 0.5,
        "rationale": """
            Task: Synthesize ALL agent outputs into strategic executive brief.
            Why frontier: Cross-document reasoning across 6+ agent outputs.
        """
    },
}


class LLMClientError(Exception):
    """Raised when LLM client initialization fails"""
    pass


def get_llm_for_agent(agent_type: str, fallback_only: bool = False) -> LLM:
    """
    Get appropriately configured LLM for a specific agent type.
    
    Args:
        agent_type: One of the keys in AGENT_MODELS
        fallback_only: If True, skip primary provider and use fallback
        
    Returns:
        Configured CrewAI LLM instance
        
    Raises:
        LLMClientError: If no valid API key is available
    """
    config = AGENT_MODELS.get(agent_type)
    if not config:
        # Fallback to Llama for unknown agents
        config = {
            "provider": "together",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            "temperature": 0.5,
        }
    
    provider = config["provider"]
    model = config["model"]
    temperature = config.get("temperature", 0.5)
    
    # Try primary provider first (unless fallback_only)
    if not fallback_only:
        try:
            llm = _create_llm(provider, model, temperature, config)
            return llm
        except LLMClientError:
            pass  # Try fallback
    
    # Try fallback if specified
    fallback_provider = config.get("fallback_provider")
    fallback_model = config.get("fallback_model")
    
    if fallback_provider and fallback_model:
        try:
            return _create_llm(fallback_provider, fallback_model, temperature, config)
        except LLMClientError:
            pass
    
    # Last resort: Together with Llama
    together_key = os.environ.get("TOGETHER_API_KEY")
    if together_key:
        return LLM(
            model="together_ai/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            api_key=together_key,
            temperature=temperature,
        )
    
    raise LLMClientError(
        f"No valid API key found for agent '{agent_type}'.\n"
        "Set one of: TOGETHER_API_KEY, ANTHROPIC_API_KEY, CHUTES_API_KEY"
    )


def _create_llm(provider: str, model: str, temperature: float, config: dict) -> LLM:
    """Create LLM instance for a specific provider."""
    
    if provider == "chutes":
        api_key = os.environ.get("CHUTES_API_KEY")
        if not api_key:
            raise LLMClientError("CHUTES_API_KEY not set")
        
        return LLM(
            model=f"openai/{model}",  # LiteLLM OpenAI-compatible prefix
            api_key=api_key,
            base_url=config.get("base_url", "https://api.chutes.ai/v1"),
            temperature=temperature,
        )
    
    elif provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            return LLM(
                model=f"anthropic/{model}",  # LiteLLM needs provider prefix
                api_key=api_key,
                temperature=temperature,
            )
        
        # Fallback to OpenRouter for Anthropic models
        openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        if openrouter_key:
            return LLM(
                model=f"openrouter/anthropic/{model}",
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
                temperature=temperature,
            )
        
        raise LLMClientError("ANTHROPIC_API_KEY or OPENROUTER_API_KEY not set")
    
    elif provider == "together":
        api_key = os.environ.get("TOGETHER_API_KEY")
        if not api_key:
            raise LLMClientError("TOGETHER_API_KEY not set")
        
        return LLM(
            model=f"together_ai/{model}",
            api_key=api_key,
            temperature=temperature,
        )
    
    elif provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise LLMClientError("OPENAI_API_KEY not set")
        
        return LLM(
            model=f"openai/{model}",  # LiteLLM prefix for OpenAI
            api_key=api_key,
            temperature=temperature,
        )
    
    else:
        raise LLMClientError(f"Unknown provider: {provider}")


def get_agent_model_info(agent_type: str) -> Dict[str, str]:
    """Get model info for an agent (for display in UI)."""
    config = AGENT_MODELS.get(agent_type, {})
    return {
        "provider": config.get("provider", "unknown"),
        "model": config.get("model", "unknown"),
        "rationale": config.get("rationale", "").strip(),
    }


def get_all_required_env_vars() -> list[str]:
    """Return list of all environment variables needed for full pipeline."""
    return [
        "CHUTES_API_KEY",      # For DeepSeek TEE models
        "TOGETHER_API_KEY",    # For Llama 3.3
        "ANTHROPIC_API_KEY",   # For Claude Sonnet/Opus
    ]
