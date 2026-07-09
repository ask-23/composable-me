"""Observability modules for Composable Me backend.

Central hub for Sentry, OpenTelemetry, PII redaction, and structured SSE errors.
"""

from web.backend.observability.pii import (
    redact_pii,
    sanitize_dict,
    truncate_content,
    is_content_key,
)
from web.backend.observability.sentry import (
    setup_sentry,
    capture_error,
    set_job_context,
    set_llm_context,
    add_breadcrumb,
    before_send,
)
from web.backend.observability.sse_errors import (
    build_error_payload,
    build_error_payload_from_exception,
    classify_error,
    ERROR_TYPES,
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
