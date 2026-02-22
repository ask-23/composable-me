"""Structured SSE error payloads.

Provides a single factory for building error payloads emitted over SSE.
All payloads are PII-redacted before emission.
"""

from typing import Any, Optional

from web.backend.observability.pii import redact_pii


# Canonical error types for SSE payloads
ERROR_TYPES = frozenset({
    "quota_exhausted",
    "rate_limited",
    "timeout",
    "validation",
    "provider_error",
    "db_error",
    "sse_error",
    "unknown",
})


def classify_error(error: Exception) -> str:
    """Classify an exception into one of the canonical error types."""
    error_str = str(error).lower()
    error_class = type(error).__name__.lower()

    if "quota" in error_str or "quotaexhausted" in error_class:
        return "quota_exhausted"
    if "rate" in error_str and "limit" in error_str:
        return "rate_limited"
    if "timeout" in error_str or "timed out" in error_str or "timedout" in error_class:
        return "timeout"
    if "validation" in error_str or "validationerror" in error_class:
        return "validation"
    if any(kw in error_str for kw in ("database", "postgres", "psycopg", "db")):
        return "db_error"
    if any(kw in error_str for kw in ("connection", "api error", "provider", "openai", "anthropic")):
        return "provider_error"
    if "sse" in error_str:
        return "sse_error"
    return "unknown"


def build_error_payload(
    job_id: str,
    error: str,
    error_type: str = "unknown",
    provider: str = "",
    model: str = "",
    stage: str = "",
    agent: str = "",
    attempt: int = 1,
    retry_count: int = 0,
    billing_url: str = "",
    recoverable: bool = False,
    trace_id: str = "",
    sentry_event_id: str = "",
) -> dict[str, Any]:
    """Build a structured SSE error payload with PII redaction.

    This is the single factory for all SSE error events. The schema is:
    {
        "job_id": "",
        "error": "",
        "error_type": "quota_exhausted|rate_limited|timeout|validation|provider_error|db_error|sse_error|unknown",
        "provider": "",
        "model": "",
        "stage": "",
        "agent": "",
        "attempt": 1,
        "retry_count": 0,
        "billing_url": "",
        "recoverable": false,
        "trace_id": "",
        "sentry_event_id": ""
    }
    """
    # Normalize error_type
    if error_type not in ERROR_TYPES:
        error_type = "unknown"

    payload = {
        "job_id": job_id,
        "error": redact_pii(str(error)),
        "error_type": error_type,
        "provider": provider or "",
        "model": model or "",
        "stage": stage or "",
        "agent": agent or "",
        "attempt": attempt,
        "retry_count": retry_count,
        "billing_url": billing_url or "",
        "recoverable": recoverable,
        "trace_id": trace_id or "",
        "sentry_event_id": sentry_event_id or "",
    }
    return payload


def build_error_payload_from_exception(
    job_id: str,
    error: Exception,
    stage: str = "",
    agent: str = "",
    provider: str = "",
    model: str = "",
    attempt: int = 1,
    retry_count: int = 0,
    billing_url: str = "",
    trace_id: str = "",
    sentry_event_id: str = "",
) -> dict[str, Any]:
    """Build a structured SSE error payload from an exception.

    Automatically classifies the error type and checks for
    QuotaExhaustedError-style to_sse_payload() methods.
    """
    error_type = classify_error(error)

    # Check if error has structured payload (e.g. QuotaExhaustedError)
    if hasattr(error, 'to_sse_payload'):
        extra = error.to_sse_payload()
        provider = extra.get("provider", provider)
        model = extra.get("model", model)
        error_type = extra.get("error_type", error_type)
        billing_url = extra.get("billing_url", billing_url)
        attempt = int(extra.get("attempt", attempt) or attempt)
        retry_count = int(extra.get("retry_count", retry_count) or retry_count)

    # Determine recoverability
    recoverable = error_type in ("rate_limited", "timeout")

    return build_error_payload(
        job_id=job_id,
        error=str(error),
        error_type=error_type,
        provider=provider,
        model=model,
        stage=stage,
        agent=agent,
        attempt=attempt,
        retry_count=retry_count,
        billing_url=billing_url,
        recoverable=recoverable,
        trace_id=trace_id,
        sentry_event_id=sentry_event_id,
    )
