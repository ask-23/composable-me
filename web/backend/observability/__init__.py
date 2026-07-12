"""Observability modules for Composable Me backend.

Central hub for Sentry, OpenTelemetry, PII redaction, and structured SSE errors.
"""

from web.backend.observability.pii import (
    is_content_key,
    redact_pii,
    sanitize_dict,
    truncate_content,
)
from web.backend.observability.sentry import (
    add_breadcrumb,
    before_send,
    capture_error,
    set_job_context,
    set_llm_context,
    setup_sentry,
)
from web.backend.observability.sse_errors import (
    ERROR_TYPES,
    build_error_payload,
    build_error_payload_from_exception,
    classify_error,
)

__all__ = [
    # PII
    "redact_pii",
    "sanitize_dict",
    "truncate_content",
    "is_content_key",
    # Sentry
    "setup_sentry",
    "capture_error",
    "set_job_context",
    "set_llm_context",
    "add_breadcrumb",
    "before_send",
    # SSE Errors
    "build_error_payload",
    "build_error_payload_from_exception",
    "classify_error",
    "ERROR_TYPES",
]
