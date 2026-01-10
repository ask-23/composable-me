"""
Configuration management for Composable Me Hydra.

Handles environment variables and system configuration.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class HydraConfig:
    """Configuration for Hydra system"""
    
    # LLM Configuration
    openrouter_api_key: str
    openrouter_model: str = "anthropic/claude-sonnet-4.5"
    
    # Workflow Configuration
    enable_research_agent: bool = True
    auto_greenlight_threshold: float = 0.60
    max_agent_retries: int = 1
    max_audit_retries: int = 2
    
    # Performance Configuration
    fit_analysis_timeout: int = 60  # seconds
    document_generation_timeout: int = 180  # seconds
    
    # Output Configuration
    output_format: str = "markdown"
    include_audit_trail: bool = True
    
    @classmethod
    def from_env(cls) -> "HydraConfig":
        """Load configuration from environment variables"""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable required. "
                "Get your key from https://openrouter.ai/keys and set it:\n"
                "  export OPENROUTER_API_KEY='sk-or-...'"
            )
        
        return cls(
            openrouter_api_key=api_key,
            openrouter_model=os.environ.get(
                "OPENROUTER_MODEL", 
                "anthropic/claude-sonnet-4.5"
            ),
            enable_research_agent=os.environ.get(
                "ENABLE_RESEARCH", "true"
            ).lower() == "true",
            auto_greenlight_threshold=float(
                os.environ.get("AUTO_GREENLIGHT_THRESHOLD", "0.60")
            ),
            max_agent_retries=int(
                os.environ.get("MAX_AGENT_RETRIES", "1")
            ),
            max_audit_retries=int(
                os.environ.get("MAX_AUDIT_RETRIES", "2")
            ),
            fit_analysis_timeout=int(
                os.environ.get("FIT_ANALYSIS_TIMEOUT", "60")
            ),
            document_generation_timeout=int(
                os.environ.get("DOCUMENT_GENERATION_TIMEOUT", "180")
            ),
            output_format=os.environ.get("OUTPUT_FORMAT", "markdown"),
            include_audit_trail=os.environ.get(
                "INCLUDE_AUDIT_TRAIL", "true"
            ).lower() == "true"
        )
    
    def validate(self) -> None:
        """Validate configuration values"""
        if not self.openrouter_api_key:
            raise ValueError("OpenRouter API key is required")
        
        if not 0.0 <= self.auto_greenlight_threshold <= 1.0:
            raise ValueError("Auto greenlight threshold must be between 0.0 and 1.0")
        
        if self.max_agent_retries < 0:
            raise ValueError("Max agent retries must be non-negative")
        
        if self.max_audit_retries < 0:
            raise ValueError("Max audit retries must be non-negative")
        
        if self.fit_analysis_timeout <= 0:
            raise ValueError("Fit analysis timeout must be positive")
        
        if self.document_generation_timeout <= 0:
            raise ValueError("Document generation timeout must be positive")
        
        valid_formats = {"markdown", "json", "yaml"}
        if self.output_format not in valid_formats:
            raise ValueError(f"Output format must be one of {valid_formats}")
