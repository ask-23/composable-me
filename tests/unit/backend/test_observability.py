"""Tests for the observability stack.

Covers:
- PII redaction (central pii module)
- Sentry error tracking (noop, redaction, enrichment, fingerprinting)
- Structured SSE error payloads (schema, classification, PII redaction)
- Structured error classes (HydraError, logging, formatters)
"""

import json
import logging
import os
import pytest
from unittest.mock import patch, MagicMock


# ============================================================
# Central PII Redaction (pii.py)
# ============================================================

class TestPIIRedaction:
    """Central PII redaction policy tests."""

    def test_redact_email(self):
        from web.backend.observability.pii import redact_pii
        text = "Contact john.doe@example.com for details"
        result = redact_pii(text)
        assert "[EMAIL_REDACTED]" in result
        assert "john.doe@example.com" not in result

    def test_redact_phone(self):
        from web.backend.observability.pii import redact_pii
        text = "Call me at 555-123-4567"
        result = redact_pii(text)
        assert "[PHONE_REDACTED]" in result
        assert "555-123-4567" not in result

    def test_redact_phone_dots(self):
        from web.backend.observability.pii import redact_pii
        text = "Phone: 555.123.4567"
        result = redact_pii(text)
        assert "[PHONE_REDACTED]" in result
        assert "555.123.4567" not in result

    def test_redact_ssn(self):
        from web.backend.observability.pii import redact_pii
        text = "SSN: 123-45-6789"
        result = redact_pii(text)
        assert "[SSN_REDACTED]" in result
        assert "123-45-6789" not in result

    def test_redact_multiple_patterns(self):
        from web.backend.observability.pii import redact_pii
        text = "Email: a@b.com, Phone: 555-111-2222, SSN: 111-22-3333"
        result = redact_pii(text)
        assert "a@b.com" not in result
        assert "555-111-2222" not in result
        assert "111-22-3333" not in result

    def test_redact_preserves_non_pii(self):
        from web.backend.observability.pii import redact_pii
        text = "Job ID: abc-123, Stage: gap_analysis"
        result = redact_pii(text)
        assert result == text

    def test_redact_non_string_passthrough(self):
        from web.backend.observability.pii import redact_pii
        assert redact_pii(42) == 42
        assert redact_pii(None) is None

    def test_truncate_content_short(self):
        from web.backend.observability.pii import truncate_content
        text = "Short text"
        assert truncate_content(text) == text

    def test_truncate_content_long(self):
        from web.backend.observability.pii import truncate_content
        text = "A" * 500
        result = truncate_content(text, max_length=100)
        assert len(result) < 500
        assert "TRUNCATED" in result
        assert "500 chars total" in result

    def test_sanitize_dict_redacts_pii(self):
        from web.backend.observability.pii import sanitize_dict
        data = {"email": "user@test.com", "job_id": "abc-123"}
        result = sanitize_dict(data)
        assert "[EMAIL_REDACTED]" in result["email"]
        assert result["job_id"] == "abc-123"

    def test_sanitize_dict_truncates_content_keys(self):
        from web.backend.observability.pii import sanitize_dict
        data = {"resume": "A" * 500, "stage": "gap_analysis"}
        result = sanitize_dict(data)
        assert "TRUNCATED" in result["resume"]
        assert result["stage"] == "gap_analysis"

    def test_sanitize_dict_recursive(self):
        from web.backend.observability.pii import sanitize_dict
        data = {"outer": {"email": "nested@test.com"}}
        result = sanitize_dict(data)
        assert "[EMAIL_REDACTED]" in result["outer"]["email"]

    def test_sanitize_dict_list_values(self):
        from web.backend.observability.pii import sanitize_dict
        data = {"contacts": ["alice@test.com", "bob@test.com"]}
        result = sanitize_dict(data)
        assert all("[EMAIL_REDACTED]" in item for item in result["contacts"])

    def test_is_content_key(self):
        from web.backend.observability.pii import is_content_key
        assert is_content_key("resume") is True
        assert is_content_key("cover_letter") is True
        assert is_content_key("job_description") is True
        assert is_content_key("source_documents") is True
        assert is_content_key("resume_text") is True
        assert is_content_key("job_id") is False
        assert is_content_key("stage") is False

    def test_redact_resume_text_in_extras(self):
        """Resume text must never appear in observability extras."""
        from web.backend.observability.pii import sanitize_dict
        data = {
            "resume": "John Doe\njohn@example.com\n555-123-4567\nSSN: 123-45-6789\n" + "A" * 500,
            "job_id": "safe-id",
        }
        result = sanitize_dict(data)
        assert "John Doe" not in result["resume"] or "TRUNCATED" in result["resume"]
        assert "john@example.com" not in result["resume"]
        assert "555-123-4567" not in result["resume"]
        assert "123-45-6789" not in result["resume"]
        assert result["job_id"] == "safe-id"


# ============================================================
# Sentry Error Tracking
# ============================================================

class TestSentryNoop:
    """Sentry is noop when SENTRY_DSN is not set."""

    def test_setup_sentry_noop_without_dsn(self):
        with patch.dict(os.environ, {}, clear=True):
            from web.backend.observability.sentry import setup_sentry
            setup_sentry()  # Should not raise

    def test_capture_error_noop_without_dsn(self):
        with patch.dict(os.environ, {}, clear=True):
            from web.backend.observability.sentry import capture_error
            result = capture_error(ValueError("test"))
            assert result is None

    def test_set_job_context_noop_without_dsn(self):
        with patch.dict(os.environ, {}, clear=True):
            from web.backend.observability.sentry import set_job_context
            set_job_context(job_id="test-123", stage="gap_analysis")

    def test_set_llm_context_noop_without_dsn(self):
        with patch.dict(os.environ, {}, clear=True):
            from web.backend.observability.sentry import set_llm_context
            set_llm_context(provider="openai", model="gpt-4o")

    def test_add_breadcrumb_noop_without_dsn(self):
        with patch.dict(os.environ, {}, clear=True):
            from web.backend.observability.sentry import add_breadcrumb
            add_breadcrumb("Test breadcrumb")


class TestSentryRedaction:
    """Sentry before_send PII redaction."""

    def test_before_send_redacts_exception_values(self):
        from web.backend.observability.sentry import before_send
        event = {
            'exception': {
                'values': [{'value': 'Error for user test@example.com'}]
            }
        }
        result = before_send(event, {})
        assert '[EMAIL_REDACTED]' in result['exception']['values'][0]['value']
        assert 'test@example.com' not in result['exception']['values'][0]['value']

    def test_before_send_redacts_stack_variables(self):
        from web.backend.observability.sentry import before_send
        event = {
            'exception': {
                'values': [{
                    'value': 'Some error',
                    'stacktrace': {
                        'frames': [{
                            'vars': {
                                'email': 'user@example.com',
                                'phone': '555-123-4567',
                                'count': 42,
                            }
                        }]
                    }
                }]
            }
        }
        result = before_send(event, {})
        frame_vars = result['exception']['values'][0]['stacktrace']['frames'][0]['vars']
        assert '[EMAIL_REDACTED]' in frame_vars['email']
        assert '[PHONE_REDACTED]' in frame_vars['phone']
        assert frame_vars['count'] == 42

    def test_before_send_redacts_message(self):
        from web.backend.observability.sentry import before_send
        event = {'message': 'User alice@test.com triggered error'}
        result = before_send(event, {})
        assert 'alice@test.com' not in result['message']
        assert '[EMAIL_REDACTED]' in result['message']

    def test_before_send_redacts_contexts(self):
        from web.backend.observability.sentry import before_send
        event = {
            'contexts': {
                'job': {
                    'job_id': 'abc',
                    'resume': 'user@test.com and 555-111-2222 content here...',
                }
            }
        }
        result = before_send(event, {})
        ctx = result['contexts']['job']
        assert 'user@test.com' not in str(ctx)
        assert '555-111-2222' not in str(ctx)

    def test_before_send_redacts_extras(self):
        from web.backend.observability.sentry import before_send
        event = {
            'extra': {
                'email_field': 'admin@company.com',
            }
        }
        result = before_send(event, {})
        assert 'admin@company.com' not in str(result['extra'])

    def test_before_send_redacts_breadcrumbs(self):
        from web.backend.observability.sentry import before_send
        event = {
            'breadcrumbs': {
                'values': [{
                    'message': 'Processing user@example.com',
                    'data': {'phone': '555-999-8888'},
                }]
            }
        }
        result = before_send(event, {})
        crumb = result['breadcrumbs']['values'][0]
        assert 'user@example.com' not in crumb['message']
        assert '555-999-8888' not in str(crumb['data'])

    def test_before_send_strips_resume_content_from_extras(self):
        """Raw resume/JD text must never reach Sentry."""
        from web.backend.observability.sentry import before_send
        long_resume = "Professional experience at ACME Corp..." + "x" * 1000
        event = {
            'extra': {
                'resume': long_resume,
                'job_id': 'safe',
            }
        }
        result = before_send(event, {})
        assert len(result['extra']['resume']) < len(long_resume)
        assert 'TRUNCATED' in result['extra']['resume']
        assert result['extra']['job_id'] == 'safe'


class TestSentryEnrichment:
    """Sentry context enrichment and fingerprinting."""

    def test_capture_error_returns_event_id(self):
        pytest.importorskip("sentry_sdk")
        test_dsn = "https://key@sentry.io/project"
        with patch.dict(os.environ, {"SENTRY_DSN": test_dsn}):
            mock_scope = MagicMock()
            with patch('sentry_sdk.push_scope') as mock_push_scope, \
                 patch('sentry_sdk.capture_exception', return_value="evt-abc123"):
                mock_push_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
                mock_push_scope.return_value.__exit__ = MagicMock(return_value=False)

                from web.backend.observability.sentry import capture_error
                event_id = capture_error(
                    ValueError("test"),
                    error_type="quota_exhausted",
                    provider="openai",
                )
                assert event_id == "evt-abc123"
                mock_scope.set_tag.assert_any_call("error_type", "quota_exhausted")
                mock_scope.set_tag.assert_any_call("provider", "openai")

    def test_capture_error_fingerprints_quota_errors(self):
        pytest.importorskip("sentry_sdk")
        test_dsn = "https://key@sentry.io/project"
        with patch.dict(os.environ, {"SENTRY_DSN": test_dsn}):
            mock_scope = MagicMock()
            with patch('sentry_sdk.push_scope') as mock_push_scope, \
                 patch('sentry_sdk.capture_exception'):
                mock_push_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
                mock_push_scope.return_value.__exit__ = MagicMock(return_value=False)

                from web.backend.observability.sentry import capture_error
                capture_error(
                    ValueError("Quota exhausted"),
                    error_type="quota_exhausted",
                    provider="openai",
                )
                assert mock_scope.fingerprint == ["openai", "quota_exhausted"]

    def test_capture_error_fingerprints_retry_loops(self):
        pytest.importorskip("sentry_sdk")
        test_dsn = "https://key@sentry.io/project"
        with patch.dict(os.environ, {"SENTRY_DSN": test_dsn}):
            mock_scope = MagicMock()
            with patch('sentry_sdk.push_scope') as mock_push_scope, \
                 patch('sentry_sdk.capture_exception'):
                mock_push_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
                mock_push_scope.return_value.__exit__ = MagicMock(return_value=False)

                from web.backend.observability.sentry import capture_error
                capture_error(
                    ValueError("Some error"),
                    error_type="provider_error",
                    provider="together",
                    stage="tailoring",
                    retry_count=3,
                )
                assert mock_scope.fingerprint == ["together", "tailoring", "provider_error"]

    def test_setup_sentry_send_default_pii_false(self):
        pytest.importorskip("sentry_sdk")
        test_dsn = "https://key@sentry.io/project"
        with patch.dict(os.environ, {"SENTRY_DSN": test_dsn}):
            with patch('sentry_sdk.init') as mock_init:
                from web.backend.observability.sentry import setup_sentry
                setup_sentry()
                call_kwargs = mock_init.call_args[1]
                assert call_kwargs.get('send_default_pii') is False


# ============================================================
# Structured SSE Error Payloads
# ============================================================

class TestSSEErrorPayloads:
    """Structured SSE error payload tests."""

    def test_build_error_payload_schema(self):
        from web.backend.observability.sse_errors import build_error_payload
        payload = build_error_payload(
            job_id="j-1",
            error="Something went wrong",
            error_type="provider_error",
            provider="openai",
            model="gpt-4o",
            stage="gap_analysis",
            agent="gap_analyzer",
            attempt=2,
            retry_count=1,
            recoverable=True,
            trace_id="abc123",
            sentry_event_id="evt-456",
        )

        required_fields = [
            "job_id", "error", "error_type", "provider", "model",
            "stage", "agent", "attempt", "retry_count", "recoverable",
            "trace_id", "sentry_event_id",
        ]
        for field in required_fields:
            assert field in payload, f"Missing field: {field}"

        assert payload["job_id"] == "j-1"
        assert payload["error_type"] == "provider_error"
        assert payload["provider"] == "openai"
        assert payload["model"] == "gpt-4o"
        assert payload["attempt"] == 2
        assert payload["retry_count"] == 1
        assert payload["recoverable"] is True

    def test_build_error_payload_defaults(self):
        from web.backend.observability.sse_errors import build_error_payload
        payload = build_error_payload(job_id="j-1", error="fail")
        assert payload["error_type"] == "unknown"
        assert payload["provider"] == ""
        assert payload["model"] == ""
        assert payload["stage"] == ""
        assert payload["agent"] == ""
        assert payload["attempt"] == 1
        assert payload["retry_count"] == 0
        assert payload["recoverable"] is False

    def test_build_error_payload_redacts_pii(self):
        from web.backend.observability.sse_errors import build_error_payload
        payload = build_error_payload(
            job_id="j-1",
            error="Error processing user@test.com at 555-123-4567",
        )
        assert "user@test.com" not in payload["error"]
        assert "555-123-4567" not in payload["error"]
        assert "[EMAIL_REDACTED]" in payload["error"]
        assert "[PHONE_REDACTED]" in payload["error"]

    def test_build_error_payload_normalizes_unknown_type(self):
        from web.backend.observability.sse_errors import build_error_payload
        payload = build_error_payload(
            job_id="j-1", error="fail", error_type="some_random_type",
        )
        assert payload["error_type"] == "unknown"

    def test_build_error_payload_all_valid_types(self):
        from web.backend.observability.sse_errors import build_error_payload, ERROR_TYPES
        for error_type in ERROR_TYPES:
            payload = build_error_payload(
                job_id="j-1", error="fail", error_type=error_type
            )
            assert payload["error_type"] == error_type

    def test_classify_error_quota(self):
        from web.backend.observability.sse_errors import classify_error
        assert classify_error(ValueError("quota exhausted for this model")) == "quota_exhausted"

    def test_classify_error_rate_limit(self):
        from web.backend.observability.sse_errors import classify_error
        assert classify_error(ValueError("rate limit exceeded")) == "rate_limited"

    def test_classify_error_timeout(self):
        from web.backend.observability.sse_errors import classify_error
        assert classify_error(TimeoutError("request timed out")) == "timeout"

    def test_classify_error_validation(self):
        from web.backend.observability.sse_errors import classify_error
        assert classify_error(ValueError("validation error in input")) == "validation"

    def test_classify_error_provider(self):
        from web.backend.observability.sse_errors import classify_error
        assert classify_error(ValueError("OpenAI API error: 500")) == "provider_error"

    def test_classify_error_db(self):
        from web.backend.observability.sse_errors import classify_error
        assert classify_error(ValueError("database connection failed")) == "db_error"

    def test_classify_error_unknown(self):
        from web.backend.observability.sse_errors import classify_error
        assert classify_error(ValueError("some random error")) == "unknown"

    def test_build_error_payload_from_exception(self):
        from web.backend.observability.sse_errors import build_error_payload_from_exception
        payload = build_error_payload_from_exception(
            job_id="j-1",
            error=ValueError("quota exhausted"),
            stage="gap_analysis",
            provider="openai",
            model="gpt-4o",
        )
        assert payload["error_type"] == "quota_exhausted"
        assert payload["provider"] == "openai"
        assert payload["model"] == "gpt-4o"
        assert payload["recoverable"] is False

    def test_build_error_payload_from_exception_rate_limited_is_recoverable(self):
        from web.backend.observability.sse_errors import build_error_payload_from_exception
        payload = build_error_payload_from_exception(
            job_id="j-1",
            error=ValueError("rate limit exceeded"),
        )
        assert payload["error_type"] == "rate_limited"
        assert payload["recoverable"] is True

    def test_build_error_payload_from_exception_timeout_is_recoverable(self):
        from web.backend.observability.sse_errors import build_error_payload_from_exception
        payload = build_error_payload_from_exception(
            job_id="j-1",
            error=TimeoutError("request timed out"),
        )
        assert payload["error_type"] == "timeout"
        assert payload["recoverable"] is True

    def test_build_error_payload_from_exception_with_to_sse_payload(self):
        """Exceptions with to_sse_payload() should have fields merged in."""
        from web.backend.observability.sse_errors import build_error_payload_from_exception

        class QuotaExhaustedError(Exception):
            def to_sse_payload(self):
                return {
                    "provider": "chutes",
                    "model": "deepseek-v3-tee",
                    "error_type": "quota_exhausted",
                }

        payload = build_error_payload_from_exception(
            job_id="j-1",
            error=QuotaExhaustedError("Quota exceeded"),
        )
        assert payload["provider"] == "chutes"
        assert payload["model"] == "deepseek-v3-tee"
        assert payload["error_type"] == "quota_exhausted"


# ============================================================
# Structured Error Classes (errors.py)
# ============================================================

class TestStructuredErrors:
    """HydraError structured error class tests."""

    def test_hydra_error_creation(self):
        from web.backend.errors import HydraError, ErrorCategory, ErrorSeverity
        error = HydraError(
            code=ErrorCategory.LLM_ERROR,
            message="LLM call failed",
            severity=ErrorSeverity.ERROR,
            agent="gap_analyzer",
            stage="gap_analysis",
            job_id="j-1",
        )
        assert error.code == ErrorCategory.LLM_ERROR
        assert error.message == "LLM call failed"
        assert error.agent == "gap_analyzer"

    def test_hydra_error_sanitizes_pii_on_creation(self):
        from web.backend.errors import HydraError, ErrorCategory
        error = HydraError(
            code=ErrorCategory.LLM_ERROR,
            message="Failed for user@test.com",
            context={"email": "admin@corp.com"},
        )
        assert "user@test.com" not in error.message
        assert "[EMAIL_REDACTED]" in error.message
        assert "admin@corp.com" not in str(error.context)

    def test_hydra_error_from_exception(self):
        from web.backend.errors import HydraError, ErrorCategory
        try:
            raise ValueError("Something went wrong for user@test.com")
        except ValueError as exc:
            error = HydraError.from_exception(
                exc,
                ErrorCategory.WORKFLOW_ERROR,
                agent="tailoring_agent",
                stage="tailoring",
                job_id="j-2",
            )
        assert "user@test.com" not in error.message
        assert "[EMAIL_REDACTED]" in error.message
        assert error.agent == "tailoring_agent"
        assert error.stack_trace is not None

    def test_hydra_error_to_dict(self):
        from web.backend.errors import HydraError, ErrorCategory, ErrorSeverity
        error = HydraError(
            code=ErrorCategory.DATABASE_ERROR,
            message="DB connection lost",
            severity=ErrorSeverity.CRITICAL,
            job_id="j-3",
        )
        d = error.to_dict()
        assert d["code"] == "DATABASE_ERROR"
        assert d["severity"] == "critical"
        assert d["message"] == "DB connection lost"
        assert d["job_id"] == "j-3"

    def test_hydra_error_to_json(self):
        from web.backend.errors import HydraError, ErrorCategory
        error = HydraError(
            code=ErrorCategory.VALIDATION_ERROR,
            message="Invalid input",
        )
        j = error.to_json()
        parsed = json.loads(j)
        assert parsed["code"] == "VALIDATION_ERROR"
        assert parsed["message"] == "Invalid input"

    def test_hydra_error_to_user_message(self):
        from web.backend.errors import HydraError, ErrorCategory
        error = HydraError(
            code=ErrorCategory.AGENT_ERROR,
            message="Agent failed to produce output",
        )
        assert error.to_user_message() == "Agent failed to produce output"


class TestPIISanitizingFilter:
    """Logging filter that sanitizes PII from log records."""

    def test_filter_sanitizes_message(self):
        from web.backend.errors import PIISanitizingFilter
        f = PIISanitizingFilter()
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="",
            lineno=0, msg="Error for user@test.com",
            args=None, exc_info=None,
        )
        f.filter(record)
        assert "user@test.com" not in record.msg
        assert "[EMAIL_REDACTED]" in record.msg

    def test_filter_sanitizes_dict_args(self):
        from web.backend.errors import PIISanitizingFilter
        f = PIISanitizingFilter()
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="",
            lineno=0, msg="Error: %s",
            args=None, exc_info=None,
        )
        # Set dict args after construction to avoid Python 3.13 LogRecord validation
        record.args = {"email": "admin@corp.com"}
        f.filter(record)
        assert "admin@corp.com" not in str(record.args)

    def test_filter_sanitizes_tuple_args(self):
        from web.backend.errors import PIISanitizingFilter
        f = PIISanitizingFilter()
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="",
            lineno=0, msg="Error: %s",
            args=("admin@corp.com",),
            exc_info=None,
        )
        f.filter(record)
        assert "admin@corp.com" not in str(record.args)


class TestStructuredJSONFormatter:
    """JSON formatter with correlation IDs."""

    def test_format_produces_valid_json(self):
        from web.backend.errors import StructuredJSONFormatter
        formatter = StructuredJSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="test.py",
            lineno=42, msg="Something failed",
            args=None, exc_info=None,
        )
        result = formatter.format(record)
        parsed = json.loads(result)
        assert parsed["level"] == "ERROR"
        assert parsed["message"] == "Something failed"
        assert parsed["line"] == 42

    def test_format_includes_correlation_id(self):
        from web.backend.errors import StructuredJSONFormatter
        formatter = StructuredJSONFormatter(correlation_id="run-abc")
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Processing",
            args=None, exc_info=None,
        )
        result = formatter.format(record)
        parsed = json.loads(result)
        assert parsed["correlation_id"] == "run-abc"

    def test_format_sanitizes_pii_in_message(self):
        from web.backend.errors import StructuredJSONFormatter
        formatter = StructuredJSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="test.py",
            lineno=1, msg="Failed for user@test.com",
            args=None, exc_info=None,
        )
        result = formatter.format(record)
        parsed = json.loads(result)
        assert "user@test.com" not in parsed["message"]
        assert "[EMAIL_REDACTED]" in parsed["message"]


# ============================================================
# Cross-Layer PII Guardrails
# ============================================================

class TestPIICrossLayer:
    """PII must be redacted consistently across all observability layers."""

    SYNTHETIC_PII_TEXT = (
        "Resume for Alice Smith (alice.smith@bigcorp.com). "
        "Phone: 555-867-5309. SSN: 123-45-6789. "
        "10 years experience in Python."
    )

    def test_pii_redacted_in_sentry_before_send(self):
        from web.backend.observability.sentry import before_send
        event = {
            'exception': {
                'values': [{'value': self.SYNTHETIC_PII_TEXT}]
            }
        }
        result = before_send(event, {})
        val = result['exception']['values'][0]['value']
        assert "alice.smith@bigcorp.com" not in val
        assert "555-867-5309" not in val
        assert "123-45-6789" not in val

    def test_pii_redacted_in_sse_error_payload(self):
        from web.backend.observability.sse_errors import build_error_payload
        payload = build_error_payload(
            job_id="j-1",
            error=self.SYNTHETIC_PII_TEXT,
        )
        assert "alice.smith@bigcorp.com" not in payload["error"]
        assert "555-867-5309" not in payload["error"]
        assert "123-45-6789" not in payload["error"]

    def test_pii_redacted_in_structured_logs(self):
        from web.backend.errors import sanitize_pii
        result = sanitize_pii(self.SYNTHETIC_PII_TEXT)
        assert "alice.smith@bigcorp.com" not in result
        assert "555-867-5309" not in result
        assert "123-45-6789" not in result

    def test_resume_content_not_in_sentry_extras(self):
        """Full resume text must never reach Sentry."""
        from web.backend.observability.sentry import before_send
        event = {
            'extra': {
                'resume': self.SYNTHETIC_PII_TEXT * 10,
                'job_id': 'j-1',
            }
        }
        result = before_send(event, {})
        assert len(result['extra']['resume']) < len(self.SYNTHETIC_PII_TEXT * 10)
