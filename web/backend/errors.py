"""Structured error handling for backend.

Provides:
- HydraError base class with structured error attributes
- Error categories for classification
- JSON logging formatter with correlation IDs
- PII sanitization filter for logs
"""

from __future__ import annotations

import json
import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from web.backend.observability.pii import (
    redact_pii as _central_redact_pii,
    sanitize_dict as _central_sanitize_dict,
    truncate_content as _central_truncate_content,
    PII_PATTERNS,
    MAX_CONTENT_LENGTH,
)


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    LLM_ERROR = "LLM_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AGENT_ERROR = "AGENT_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    WORKFLOW_ERROR = "WORKFLOW_ERROR"


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


def sanitize_pii(text: str) -> str:
    """Redact PII patterns from text (delegates to central pii module)."""
    return _central_redact_pii(text)


def truncate_content(text: str, max_length: int = MAX_CONTENT_LENGTH) -> str:
    """Truncate long content for logging (delegates to central pii module)."""
    return _central_truncate_content(text, max_length)


def sanitize_context(context: dict[str, Any]) -> dict[str, Any]:
    """Sanitize a context dictionary (delegates to central pii module)."""
    return _central_sanitize_dict(context)


@dataclass
class HydraError:
    """Structured error for workflow operations.

    Captures full context for debugging while ensuring PII is never logged.

    Attributes:
        code: Error category code (e.g., LLM_ERROR, VALIDATION_ERROR)
        message: User-friendly error message (no stack traces)
        severity: Error severity level
        agent: Agent name where error occurred (if applicable)
        stage: Workflow stage where error occurred
        context: Additional context (sanitized before storage)
        stack_trace: Full stack trace for debugging
        timestamp: ISO format timestamp when error occurred
        run_id: Correlation ID linking to workflow run
        job_id: Job ID for correlation
    """
    code: ErrorCategory
    message: str
    severity: ErrorSeverity = ErrorSeverity.ERROR
    agent: Optional[str] = None
    stage: Optional[str] = None
    context: dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    run_id: Optional[str] = None
    job_id: Optional[str] = None

    def __post_init__(self):
        """Sanitize context on creation."""
        self.context = sanitize_context(self.context)
        self.message = sanitize_pii(self.message)

    @classmethod
    def from_exception(
        cls,
        exc: Exception,
        code: ErrorCategory,
        *,
        agent: Optional[str] = None,
        stage: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        run_id: Optional[str] = None,
        job_id: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ) -> HydraError:
        """Create HydraError from an exception."""
        user_message = sanitize_pii(str(exc))

        return cls(
            code=code,
            message=user_message,
            severity=severity,
            agent=agent,
            stage=stage,
            context=context or {},
            stack_trace=traceback.format_exc(),
            run_id=run_id,
            job_id=job_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "code": self.code.value if isinstance(self.code, Enum) else self.code,
            "message": self.message,
            "severity": self.severity.value if isinstance(self.severity, Enum) else self.severity,
            "agent": self.agent,
            "stage": self.stage,
            "context": self.context,
            "stack_trace": self.stack_trace,
            "timestamp": self.timestamp,
            "run_id": self.run_id,
            "job_id": self.job_id,
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    def to_user_message(self) -> str:
        """Get user-friendly error message without technical details."""
        return self.message


class PIISanitizingFilter(logging.Filter):
    """Logging filter that sanitizes PII from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and sanitize log record."""
        if isinstance(record.msg, str):
            record.msg = sanitize_pii(record.msg)

        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: sanitize_pii(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    sanitize_pii(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )

        return True


class StructuredJSONFormatter(logging.Formatter):
    """JSON formatter for structured logging with correlation IDs."""

    def __init__(self, correlation_id: Optional[str] = None):
        super().__init__()
        self.correlation_id = correlation_id

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        correlation_id = getattr(record, 'correlation_id', None) or self.correlation_id
        if correlation_id:
            log_entry["correlation_id"] = correlation_id

        if hasattr(record, 'run_id'):
            log_entry["run_id"] = record.run_id
        if hasattr(record, 'job_id'):
            log_entry["job_id"] = record.job_id

        if hasattr(record, 'hydra_error') and record.hydra_error:
            error = record.hydra_error
            if isinstance(error, HydraError):
                log_entry["error"] = error.to_dict()
            elif isinstance(error, dict):
                log_entry["error"] = error

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        log_entry["message"] = sanitize_pii(log_entry["message"])

        return json.dumps(log_entry, default=str)


def configure_structured_logging(
    logger_name: Optional[str] = None,
    level: int = logging.INFO,
    correlation_id: Optional[str] = None,
) -> logging.Logger:
    """Configure a logger with structured JSON formatting and PII sanitization."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(StructuredJSONFormatter(correlation_id=correlation_id))

    handler.addFilter(PIISanitizingFilter())

    logger.addHandler(handler)

    return logger


class CorrelatedLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that automatically includes correlation IDs."""

    def __init__(
        self,
        logger: logging.Logger,
        run_id: Optional[str] = None,
        job_id: Optional[str] = None,
    ):
        super().__init__(logger, {})
        self.run_id = run_id
        self.job_id = job_id

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        """Process log message, adding correlation IDs."""
        extra = kwargs.get('extra', {})
        extra['run_id'] = self.run_id
        extra['job_id'] = self.job_id
        extra['correlation_id'] = self.run_id or self.job_id
        kwargs['extra'] = extra
        return msg, kwargs

    def log_error(self, error: HydraError) -> None:
        """Log a HydraError with full context."""
        level_map = {
            ErrorSeverity.DEBUG: logging.DEBUG,
            ErrorSeverity.INFO: logging.INFO,
            ErrorSeverity.WARNING: logging.WARNING,
            ErrorSeverity.ERROR: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }
        level = level_map.get(error.severity, logging.ERROR)

        self.log(
            level,
            error.message,
            extra={
                'hydra_error': error,
                'run_id': error.run_id or self.run_id,
                'job_id': error.job_id or self.job_id,
                'correlation_id': error.run_id or error.job_id or self.run_id or self.job_id,
            }
        )
