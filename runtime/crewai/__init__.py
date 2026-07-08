"""CrewAI runtime for Composable Me Hydra."""

from .base_agent import BaseHydraAgent, ValidationError
from .config import HydraConfig
from .llm_client import (
    get_llm_client,
    test_llm_connection,
    get_available_models,
    validate_model_name,
    LLMClientError,
    LLMRetryHandler,
)
from . import cli
from .models import (
    WorkflowState,
    WorkflowStatus,
    JobDescription,
    Resume,
    Employment,
    Requirement,
    Classification,
    Differentiator,
    AuditIssue,
    AgentExecution,
    ClassificationType,
    IssueSeverity,
    RequirementType,
    RequirementPriority,
)

__all__ = [
    "BaseHydraAgent",
    "ValidationError",
    "HydraConfig",
    "get_llm_client",
    "test_llm_connection",
    "get_available_models",
    "validate_model_name",
    "LLMClientError",
    "LLMRetryHandler",
    "cli",
    "WorkflowState",
    "WorkflowStatus",
    "JobDescription",
    "Resume",
    "Employment",
    "Requirement",
    "Classification",
    "Differentiator",
    "AuditIssue",
    "AgentExecution",
    "ClassificationType",
    "IssueSeverity",
    "RequirementType",
    "RequirementPriority",
]
