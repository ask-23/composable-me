"""CrewAI runtime for Composable Me Hydra."""

from . import cli
from .base_agent import BaseHydraAgent, ValidationError
from .contracts import (
    ATSResult,
    AuditVerdict,
    ExecutiveDecision,
    GapAnalysis,
    TailoredDocuments,
    recommendation_for_fit_score,
)
from .llm_client import (
    LLMClientError,
    LLMRetryHandler,
    get_available_models,
    get_llm_client,
    test_llm_connection,
    validate_model_name,
)

__all__ = [
    "BaseHydraAgent",
    "ValidationError",
    "get_llm_client",
    "test_llm_connection",
    "get_available_models",
    "validate_model_name",
    "LLMClientError",
    "LLMRetryHandler",
    "cli",
    "TailoredDocuments",
    "ATSResult",
    "AuditVerdict",
    "GapAnalysis",
    "ExecutiveDecision",
    "recommendation_for_fit_score",
]
