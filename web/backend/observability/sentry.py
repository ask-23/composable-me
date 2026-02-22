"""Sentry error tracking configuration.

Captures exceptions from HTTP routes, workflow execution, SSE streaming,
LLM provider errors, and database failures. Enriched with job-specific
tags, contexts, and fingerprinting.

Noop when SENTRY_DSN is not set.
"""

import os
from typing import Any, Optional

from web.backend.observability.pii import (
    redact_pii,
    sanitize_dict,
    is_content_key,
    truncate_content,
)


def _scrub_event_extras(extras: dict[str, Any]) -> dict[str, Any]:
    """Deep-scrub Sentry event extras: redact PII and strip raw document content."""
    scrubbed = {}
    for key, value in extras.items():
        if is_content_key(key):
            # Never send raw resume/JD/cover letter to Sentry
            scrubbed[key] = truncate_content(redact_pii(str(value))) if value else value
        elif isinstance(value, str):
            scrubbed[key] = redact_pii(value)
        elif isinstance(value, dict):
            scrubbed[key] = _scrub_event_extras(value)
        elif isinstance(value, list):
            scrubbed[key] = [
                _scrub_event_extras(item) if isinstance(item, dict)
                else redact_pii(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            scrubbed[key] = value
    return scrubbed


def before_send(event: dict, hint: dict) -> Optional[dict]:
    """Redact PII from error reports before sending to Sentry.

    Scrubs:
    - Exception values and stack trace local variables
    - Event message
    - All contexts and extras
    - Breadcrumb messages and data
    """
    # Scrub exception values and stack variables
    if 'exception' in event:
        for exc in event['exception'].get('values', []):
            if 'value' in exc:
                exc['value'] = redact_pii(exc['value'])
            if 'stacktrace' in exc:
                for frame in exc['stacktrace'].get('frames', []):
                    if 'vars' in frame:
                        frame['vars'] = {
                            k: redact_pii(str(v)) if isinstance(v, str) else v
                            for k, v in frame['vars'].items()
                        }

    # Scrub top-level message
    if 'message' in event and isinstance(event['message'], str):
        event['message'] = redact_pii(event['message'])

    # Scrub contexts
    if 'contexts' in event:
        for ctx_name, ctx_data in event['contexts'].items():
            if isinstance(ctx_data, dict):
                event['contexts'][ctx_name] = _scrub_event_extras(ctx_data)

    # Scrub extras
    if 'extra' in event and isinstance(event['extra'], dict):
        event['extra'] = _scrub_event_extras(event['extra'])

    # Scrub breadcrumbs
    if 'breadcrumbs' in event:
        for crumb in event.get('breadcrumbs', {}).get('values', []):
            if 'message' in crumb and isinstance(crumb['message'], str):
                crumb['message'] = redact_pii(crumb['message'])
            if 'data' in crumb and isinstance(crumb['data'], dict):
                crumb['data'] = _scrub_event_extras(crumb['data'])

    return event


def setup_sentry() -> None:
    """Initialize Sentry SDK if SENTRY_DSN is set."""
    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        return  # Noop mode - no Sentry configured

    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.litestar import LitestarIntegration

    sentry_sdk.init(
        dsn=dsn,
        environment=os.environ.get("SENTRY_ENVIRONMENT", "development"),
        release=os.environ.get("SENTRY_RELEASE"),
        traces_sample_rate=0.1,  # 10% of transactions
        sample_rate=1.0,  # Capture 100% of errors
        send_default_pii=False,
        before_send=before_send,
        integrations=[
            LoggingIntegration(
                level=None,  # Capture all levels as breadcrumbs
                event_level=None,  # Don't send logs as events
            ),
            LitestarIntegration(),
        ],
    )


def set_job_context(
    job_id: str,
    stage: str = None,
    agent: str = None,
    model: str = None,
    provider: str = None,
    elapsed_seconds: float = None,
    attempt: int = None,
    retry_count: int = None,
) -> None:
    """Set job context on the current Sentry scope.

    Enriches events with job context and tags for filtering.
    """
    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        return
    import sentry_sdk

    # Build job context (only non-None values)
    job_context = {
        k: v for k, v in {
            "job_id": job_id,
            "stage_name": stage,
            "agent_name": agent,
            "model": model,
            "provider": provider,
            "elapsed_seconds": elapsed_seconds,
            "attempt": attempt,
            "retry_count": retry_count,
        }.items() if v is not None
    }
    sentry_sdk.set_context("job", job_context)

    # Set tags for filtering in Sentry UI
    if stage:
        sentry_sdk.set_tag("stage", stage)
    if agent:
        sentry_sdk.set_tag("agent", agent)
    if provider:
        sentry_sdk.set_tag("provider", provider)
    if model:
        sentry_sdk.set_tag("model", model)


def set_llm_context(provider: str, model: str, base_url: str = None) -> None:
    """Set LLM provider context on the current Sentry scope."""
    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        return
    import sentry_sdk

    llm_context = {
        k: v for k, v in {
            "provider": provider,
            "model": model,
            "base_url": base_url,
        }.items() if v is not None
    }
    sentry_sdk.set_context("llm", llm_context)


def add_breadcrumb(message: str, category: str = "workflow", data: dict = None) -> None:
    """Add a breadcrumb to the current Sentry scope."""
    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        return
    import sentry_sdk
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        data=data or {},
    )


def capture_error(
    error: Exception,
    context: Optional[dict] = None,
    error_type: Optional[str] = None,
    fingerprint: Optional[list] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    stage: Optional[str] = None,
    agent: Optional[str] = None,
    attempt: Optional[int] = None,
    retry_count: Optional[int] = None,
) -> Optional[str]:
    """Capture an error with job context. Returns sentry_event_id or None.

    Fingerprinting rules:
    - quota/rate-limit errors group by [provider, error_type]
    - Retry loops emit single event keyed on [provider, stage, error_type]
    """
    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        return None

    import sentry_sdk

    with sentry_sdk.push_scope() as scope:
        # Set tags from explicit params
        if context:
            for key, value in context.items():
                scope.set_tag(key, str(value))
        if error_type:
            scope.set_tag("error_type", error_type)
        if provider:
            scope.set_tag("provider", provider)
        if model:
            scope.set_tag("model", model)
        if stage:
            scope.set_tag("stage", stage)
        if agent:
            scope.set_tag("agent", agent)

        # Fingerprinting: group quota/rate-limit by provider
        if fingerprint:
            scope.fingerprint = fingerprint
        elif error_type in ("quota_exhausted", "rate_limited"):
            scope.fingerprint = [provider or "unknown", error_type]
        elif retry_count and retry_count > 0:
            # Retry loops: single event keyed on provider + stage + error_type
            scope.fingerprint = [
                provider or "unknown",
                stage or "unknown",
                error_type or "unknown",
            ]

        # Set extra context
        if attempt is not None:
            scope.set_extra("attempt", attempt)
        if retry_count is not None:
            scope.set_extra("retry_count", retry_count)

        event_id = sentry_sdk.capture_exception(error)
        return event_id
