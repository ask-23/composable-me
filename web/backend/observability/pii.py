"""Central PII redaction policy for observability.

Single source of truth for PII patterns and redaction logic, used by:
- Sentry before_send
- OTel span attribute filtering
- Structured SSE error payloads
- Structured JSON log formatter
"""

import re
from typing import Any


# --- PII Detection Patterns ---

PII_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL_REDACTED]'),
    (re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'), '[PHONE_REDACTED]'),
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[SSN_REDACTED]'),
]

# Keys whose values may contain full resume/JD/document text
_CONTENT_KEYS = frozenset({
    'resume', 'cover_letter', 'job_description', 'source_documents',
    'document', 'jd_text', 'resume_text', 'content',
})

# Maximum length for document content in observability outputs
MAX_CONTENT_LENGTH = 200


def redact_pii(text: str) -> str:
    """Redact PII patterns (email, phone, SSN) from text.

    This is the single entry point for all PII redaction across Sentry,
    OTel, SSE error payloads, and structured logs.
    """
    if not isinstance(text, str):
        return text
    for pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def truncate_content(text: str, max_length: int = MAX_CONTENT_LENGTH) -> str:
    """Truncate long document content for observability outputs.

    Resume, cover letter, and JD text must never appear in full in
    Sentry extras, OTel attributes, or SSE error payloads.
    """
    if not isinstance(text, str):
        return text
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"... [TRUNCATED, {len(text)} chars total]"


def sanitize_value(key: str, value: Any) -> Any:
    """Sanitize a single key-value pair: redact PII, truncate content fields."""
    if isinstance(value, str):
        if key.lower() in _CONTENT_KEYS or 'resume' in key.lower() or 'content' in key.lower():
            value = truncate_content(value)
        value = redact_pii(value)
    elif isinstance(value, dict):
        value = sanitize_dict(value)
    elif isinstance(value, list):
        value = [
            sanitize_dict(item) if isinstance(item, dict)
            else redact_pii(item) if isinstance(item, str)
            else item
            for item in value
        ]
    return value


def sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively sanitize a dictionary: redact PII, truncate content fields.

    Safe to call on Sentry event extras, OTel attribute dicts, SSE payloads, etc.
    """
    if not isinstance(data, dict):
        return data
    return {k: sanitize_value(k, v) for k, v in data.items()}


def is_content_key(key: str) -> bool:
    """Check if a key represents document content that should be excluded."""
    lower = key.lower()
    return lower in _CONTENT_KEYS or 'resume' in lower or 'content' in lower
