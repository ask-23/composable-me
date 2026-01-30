"""
OpenTelemetry tracing for CrewAI runtime agents.

This module provides tracing capabilities for:
- Agent execution
- Task execution
- Workflow stages
"""

import os
import logging
from typing import Optional
from contextlib import contextmanager

# Import from web backend's telemetry if available, otherwise use local implementation
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode, Span
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

logger = logging.getLogger(__name__)

# Global tracer reference
_tracer: Optional["trace.Tracer"] = None


def get_tracer() -> Optional["trace.Tracer"]:
    """
    Get the global tracer instance for runtime instrumentation.

    Returns:
        Tracer instance if OpenTelemetry is available and enabled, None otherwise.
    """
    global _tracer

    if not OTEL_AVAILABLE:
        return None

    if _tracer is not None:
        return _tracer

    # Check if telemetry is enabled
    if os.getenv("OTEL_ENABLED", "false").lower() not in ("true", "1", "yes"):
        return None

    # Get tracer from global provider (initialized by web backend)
    _tracer = trace.get_tracer("hydra-runtime", "1.0.0")
    return _tracer


class NoOpSpan:
    """No-op span for when telemetry is disabled."""

    def set_attribute(self, key: str, value) -> None:
        pass

    def set_attributes(self, attributes: dict) -> None:
        pass

    def add_event(self, name: str, attributes: Optional[dict] = None) -> None:
        pass

    def record_exception(self, exception: Exception) -> None:
        pass

    def set_status(self, status) -> None:
        pass

    def end(self) -> None:
        pass

    @property
    def is_recording(self) -> bool:
        return False


@contextmanager
def trace_agent_execution(agent_role: str, attributes: Optional[dict] = None):
    """
    Context manager for tracing agent execution.

    Usage:
        with trace_agent_execution("Gap Analyzer", {"job_id": "123"}) as span:
            result = agent.execute(context)
            span.set_attribute("result.confidence", result.get("confidence"))

    Args:
        agent_role: The role/name of the agent being executed
        attributes: Optional dict of attributes to add to the span

    Yields:
        The created span, or a NoOpSpan if telemetry is disabled.
    """
    tracer = get_tracer()

    if tracer is None:
        yield NoOpSpan()
        return

    span_name = f"agent.{agent_role.lower().replace(' ', '_')}"

    with tracer.start_as_current_span(span_name) as span:
        span.set_attribute("agent.role", agent_role)

        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        yield span


@contextmanager
def trace_task_execution(task_name: str, agent_role: str, attributes: Optional[dict] = None):
    """
    Context manager for tracing task execution.

    Args:
        task_name: Name of the task being executed
        agent_role: Role of the agent executing the task
        attributes: Optional attributes to add

    Yields:
        The created span, or a NoOpSpan if telemetry is disabled.
    """
    tracer = get_tracer()

    if tracer is None:
        yield NoOpSpan()
        return

    span_name = f"task.{task_name.lower().replace(' ', '_')}"

    with tracer.start_as_current_span(span_name) as span:
        span.set_attribute("task.name", task_name)
        span.set_attribute("task.agent", agent_role)

        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        yield span


@contextmanager
def trace_workflow_stage(stage_name: str, attributes: Optional[dict] = None):
    """
    Context manager for tracing workflow stages.

    Args:
        stage_name: Name of the workflow stage (e.g., "gap_analysis", "tailoring")
        attributes: Optional attributes to add

    Yields:
        The created span, or a NoOpSpan if telemetry is disabled.
    """
    tracer = get_tracer()

    if tracer is None:
        yield NoOpSpan()
        return

    span_name = f"workflow.stage.{stage_name}"

    with tracer.start_as_current_span(span_name) as span:
        span.set_attribute("workflow.stage", stage_name)

        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        yield span


def record_agent_error(span, exception: Exception, agent_role: str):
    """
    Record an exception on an agent span.

    Args:
        span: The span to record the exception on
        exception: The exception that occurred
        agent_role: The role of the agent that failed
    """
    if span is None or isinstance(span, NoOpSpan):
        return

    if OTEL_AVAILABLE:
        span.record_exception(exception)
        span.set_status(Status(StatusCode.ERROR, str(exception)))
        span.set_attribute("agent.error", True)
        span.set_attribute("agent.error_type", type(exception).__name__)


def record_agent_result(span, result: dict, agent_role: str):
    """
    Record agent result attributes on a span.

    Args:
        span: The span to add attributes to
        result: The agent result dictionary
        agent_role: The role of the agent
    """
    if span is None or isinstance(span, NoOpSpan):
        return

    # Record common result attributes
    if "confidence" in result:
        span.set_attribute("agent.result.confidence", result["confidence"])

    span.set_attribute("agent.result.success", True)
