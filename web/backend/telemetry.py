"""
OpenTelemetry configuration and initialization for Hydra web backend.

This module provides OTLP-based observability with:
- Distributed tracing for API requests and workflow execution
- Configurable OTLP exporter (HTTP or gRPC)
- Environment-based configuration
"""

import os
import logging
from typing import Optional
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as OTLPSpanExporterGRPC
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as OTLPSpanExporterHTTP
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger(__name__)

# Global tracer instance
_tracer: Optional[trace.Tracer] = None
_initialized = False


def get_otlp_config() -> dict:
    """
    Get OTLP configuration from environment variables.

    Environment variables:
        OTEL_ENABLED: Enable/disable telemetry (default: false)
        OTEL_SERVICE_NAME: Service name for traces (default: hydra-backend)
        OTEL_SERVICE_VERSION: Service version (default: 1.0.0)
        OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint URL (default: http://localhost:4317)
        OTEL_EXPORTER_OTLP_PROTOCOL: Protocol to use - grpc or http (default: grpc)
        OTEL_EXPORTER_OTLP_HEADERS: Optional headers for OTLP exporter
        OTEL_CONSOLE_EXPORT: Also export to console for debugging (default: false)
    """
    return {
        "enabled": os.getenv("OTEL_ENABLED", "false").lower() in ("true", "1", "yes"),
        "service_name": os.getenv("OTEL_SERVICE_NAME", "hydra-backend"),
        "service_version": os.getenv("OTEL_SERVICE_VERSION", "1.0.0"),
        "endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
        "protocol": os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc"),
        "headers": os.getenv("OTEL_EXPORTER_OTLP_HEADERS", ""),
        "console_export": os.getenv("OTEL_CONSOLE_EXPORT", "false").lower() in ("true", "1", "yes"),
    }


def init_telemetry() -> Optional[trace.Tracer]:
    """
    Initialize OpenTelemetry with OTLP exporter.

    Returns:
        Tracer instance if enabled, None otherwise.
    """
    global _tracer, _initialized

    if _initialized:
        return _tracer

    config = get_otlp_config()

    if not config["enabled"]:
        logger.info("OpenTelemetry disabled (set OTEL_ENABLED=true to enable)")
        _initialized = True
        return None

    logger.info(f"Initializing OpenTelemetry with endpoint: {config['endpoint']}")

    # Create resource with service information
    resource = Resource.create({
        SERVICE_NAME: config["service_name"],
        SERVICE_VERSION: config["service_version"],
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    })

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Parse headers if provided
    headers = None
    if config["headers"]:
        headers = dict(item.split("=") for item in config["headers"].split(","))

    # Create OTLP exporter based on protocol
    try:
        if config["protocol"] == "http":
            # HTTP/protobuf exporter
            endpoint = config["endpoint"]
            if not endpoint.endswith("/v1/traces"):
                endpoint = f"{endpoint}/v1/traces"
            exporter = OTLPSpanExporterHTTP(
                endpoint=endpoint,
                headers=headers,
            )
        else:
            # gRPC exporter (default)
            exporter = OTLPSpanExporterGRPC(
                endpoint=config["endpoint"],
                headers=headers,
                insecure=not config["endpoint"].startswith("https"),
            )

        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info(f"OTLP exporter configured: {config['protocol']} -> {config['endpoint']}")

    except Exception as e:
        logger.warning(f"Failed to configure OTLP exporter: {e}")
        # Fall back to console exporter
        config["console_export"] = True

    # Optionally add console exporter for debugging
    if config["console_export"]:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("Console span exporter enabled")

    # Set the global tracer provider
    trace.set_tracer_provider(provider)

    # Create tracer
    _tracer = trace.get_tracer(config["service_name"], config["service_version"])
    _initialized = True

    logger.info(f"OpenTelemetry initialized: service={config['service_name']}")
    return _tracer


def get_tracer() -> Optional[trace.Tracer]:
    """
    Get the global tracer instance.

    Returns:
        Tracer instance if telemetry is enabled, None otherwise.
    """
    global _tracer, _initialized

    if not _initialized:
        return init_telemetry()

    return _tracer


def shutdown_telemetry():
    """Shutdown telemetry and flush any pending spans."""
    global _initialized

    provider = trace.get_tracer_provider()
    if hasattr(provider, 'shutdown'):
        provider.shutdown()

    _initialized = False
    logger.info("OpenTelemetry shutdown complete")


@contextmanager
def create_span(name: str, attributes: Optional[dict] = None):
    """
    Context manager for creating a traced span.

    Usage:
        with create_span("my_operation", {"key": "value"}) as span:
            # do work
            span.set_attribute("result", "success")

    Args:
        name: Name of the span
        attributes: Optional dict of attributes to add to the span

    Yields:
        The created span, or a no-op span if telemetry is disabled.
    """
    tracer = get_tracer()

    if tracer is None:
        # Return a no-op context if telemetry is disabled
        yield NoOpSpan()
        return

    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield span


def record_exception(span: Span, exception: Exception, attributes: Optional[dict] = None):
    """
    Record an exception on a span.

    Args:
        span: The span to record the exception on
        exception: The exception to record
        attributes: Optional additional attributes
    """
    if span is None or isinstance(span, NoOpSpan):
        return

    span.record_exception(exception)
    span.set_status(Status(StatusCode.ERROR, str(exception)))

    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)


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


# Propagator for distributed tracing context
propagator = TraceContextTextMapPropagator()


def inject_context(carrier: dict) -> dict:
    """
    Inject trace context into a carrier dict for propagation.

    Args:
        carrier: Dict to inject context into

    Returns:
        The carrier with trace context injected
    """
    propagator.inject(carrier)
    return carrier


def extract_context(carrier: dict):
    """
    Extract trace context from a carrier dict.

    Args:
        carrier: Dict containing trace context headers

    Returns:
        Extracted context
    """
    return propagator.extract(carrier)
