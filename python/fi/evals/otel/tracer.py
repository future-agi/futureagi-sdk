"""
OpenTelemetry Tracer Setup.

Factory functions and utilities for setting up OpenTelemetry
tracing with LLM-specific processors and exporters.
"""

from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager
import logging
import os

from .config import (
    TraceConfig,
    ExporterConfig,
    ProcessorConfig,
    SamplingStrategy,
)
from .types import ExporterType, ProcessorType
from .processors import (
    OTEL_AVAILABLE,
    CompositeSpanProcessor,
    LLMSpanProcessor,
    EvaluationSpanProcessor,
    CostSpanProcessor,
)

logger = logging.getLogger(__name__)

# Global tracer provider instance
_tracer_provider: Optional[Any] = None
_is_initialized = False


def setup_tracing(
    config: Optional[TraceConfig] = None,
    service_name: Optional[str] = None,
    project_name: Optional[str] = None,
    otlp_endpoint: Optional[str] = None,
    **kwargs,
) -> Any:
    """
    Set up OpenTelemetry tracing for LLM applications.

    This is the main entry point for configuring OTEL tracing.
    It creates exporters, processors, and a tracer provider.

    Args:
        config: Full TraceConfig, or None to use defaults/env vars
        service_name: Service name (overrides config)
        otlp_endpoint: OTLP endpoint (overrides config)
        **kwargs: Additional arguments passed to TraceConfig

    Returns:
        The configured TracerProvider

    Example:
        # Simple setup with environment variables
        setup_tracing(service_name="my-llm-service")

        # Full configuration
        from fi.evals.otel import TraceConfig, ExporterConfig, ExporterType

        config = TraceConfig(
            service_name="my-service",
            exporters=[
                ExporterConfig(type=ExporterType.OTLP_GRPC, endpoint="localhost:4317"),
                ExporterConfig(type=ExporterType.CONSOLE),
            ],
        )
        setup_tracing(config)
    """
    global _tracer_provider, _is_initialized

    if not OTEL_AVAILABLE:
        logger.warning(
            "OpenTelemetry SDK not available. Install with: "
            "pip install opentelemetry-sdk opentelemetry-exporter-otlp"
        )
        return None

    # Build configuration
    if config is None:
        config = _build_config_from_env(service_name, otlp_endpoint, **kwargs)
    else:
        # Override with explicit args
        if service_name:
            config.service_name = service_name
        if otlp_endpoint:
            config.exporters = [ExporterConfig(
                type=ExporterType.OTLP_GRPC,
                endpoint=otlp_endpoint,
            )]

    if not config.enabled:
        logger.info("Tracing is disabled")
        return None

    # Import OTEL components
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME

    # Create resource
    resource_attrs = {
        SERVICE_NAME: config.service_name,
        "service.version": config.service_version or "unknown",
        "deployment.environment": config.deployment_environment,
        **config.resource.attributes,
    }

    # Always set trace source
    resource_attrs["fi.trace.source"] = "traceai"

    # Auto-inject FutureAGI project attributes when using FUTUREAGI exporter
    has_fi_exporter = any(
        e.type == ExporterType.FUTUREAGI for e in config.exporters
    )
    if has_fi_exporter:
        import json as _json
        import uuid as _uuid
        resource_attrs.setdefault(
            "project_name",
            project_name or os.environ.get("FI_PROJECT_NAME", config.service_name),
        )
        resource_attrs.setdefault("project_type", "observe")
        resource_attrs.setdefault(
            "project_version_name",
            os.environ.get("FI_PROJECT_VERSION_NAME", "v1"),
        )
        resource_attrs.setdefault("project_version_id", str(_uuid.uuid4()))
        resource_attrs.setdefault("eval_tags", _json.dumps([]))
        resource_attrs.setdefault("metadata", _json.dumps({}))

    resource = Resource.create(resource_attrs)

    # Create tracer provider
    provider = TracerProvider(
        resource=resource,
        sampler=_create_sampler(config),
    )

    # Add exporters
    for exporter_config in config.exporters:
        exporter = _create_exporter(exporter_config)
        if exporter:
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            provider.add_span_processor(BatchSpanProcessor(exporter))

    # Add custom processors
    custom_processors = _create_custom_processors(config)
    if custom_processors:
        provider.add_span_processor(custom_processors)

    # Set as global provider
    trace.set_tracer_provider(provider)
    _tracer_provider = provider
    _is_initialized = True

    logger.info(
        f"OpenTelemetry tracing initialized for '{config.service_name}' "
        f"with {len(config.exporters)} exporter(s)"
    )

    return provider


def _build_config_from_env(
    service_name: Optional[str] = None,
    otlp_endpoint: Optional[str] = None,
    **kwargs,
) -> TraceConfig:
    """Build TraceConfig from environment variables."""
    # Service name
    service_name = service_name or os.getenv("OTEL_SERVICE_NAME", "llm-service")

    # OTLP endpoint
    endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    # Build exporters
    exporters = []
    if endpoint:
        exporters.append(ExporterConfig(
            type=ExporterType.OTLP_GRPC,
            endpoint=endpoint,
            headers=_parse_headers(os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")),
        ))
    else:
        # Default to console
        exporters.append(ExporterConfig(type=ExporterType.CONSOLE))

    return TraceConfig(
        service_name=service_name,
        exporters=exporters,
        deployment_environment=os.getenv("OTEL_DEPLOYMENT_ENVIRONMENT", "development"),
        **kwargs,
    )


def _parse_headers(headers_str: str) -> Dict[str, str]:
    """Parse headers from comma-separated key=value string."""
    if not headers_str:
        return {}

    headers = {}
    for pair in headers_str.split(","):
        if "=" in pair:
            key, value = pair.split("=", 1)
            headers[key.strip()] = value.strip()
    return headers


from ._tracer_factories import _create_sampler
_create_sampler.__module__ = __name__


from ._tracer_factories import _create_exporter
_create_exporter.__module__ = __name__


from ._tracer_factories import _create_custom_processors
_create_custom_processors.__module__ = __name__


def get_tracer(name: str = "fi.evals") -> Any:
    """
    Get a tracer instance.

    Args:
        name: Tracer name (typically module name)

    Returns:
        Tracer instance
    """
    if not OTEL_AVAILABLE:
        return _NoOpTracer()

    from opentelemetry import trace
    return trace.get_tracer(name)


def get_current_span() -> Any:
    """Get the current active span."""
    if not OTEL_AVAILABLE:
        return None

    from opentelemetry import trace
    return trace.get_current_span()


def is_tracing_enabled() -> bool:
    """Check if tracing is enabled and initialized."""
    return _is_initialized and _tracer_provider is not None


@contextmanager
def trace_llm_call(
    name: str,
    model: Optional[str] = None,
    system: Optional[str] = None,
    **attributes,
):
    """
    Context manager for tracing an LLM call.

    Creates a span with LLM-specific attributes.

    Args:
        name: Span name
        model: Model name
        system: Provider system (openai, anthropic, etc.)
        **attributes: Additional span attributes

    Yields:
        The active span

    Example:
        with trace_llm_call("chat", model="gpt-4", system="openai") as span:
            response = client.chat.completions.create(...)
            span.set_attribute("gen_ai.usage.input_tokens", response.usage.prompt_tokens)
    """
    from .conventions import GenAIAttributes, OPERATION_CHAT

    tracer = get_tracer()

    # Build initial attributes
    span_attrs = {
        GenAIAttributes.SPAN_KIND: "LLM",
        GenAIAttributes.OPERATION_NAME: OPERATION_CHAT,
    }
    if model:
        span_attrs[GenAIAttributes.REQUEST_MODEL] = model
    if system:
        span_attrs[GenAIAttributes.PROVIDER_NAME] = system
    span_attrs.update(attributes)

    with tracer.start_as_current_span(name, attributes=span_attrs) as span:
        yield span


def shutdown_tracing() -> None:
    """Shutdown the tracer provider and flush pending spans."""
    global _tracer_provider, _is_initialized

    if _tracer_provider:
        try:
            _tracer_provider.shutdown()
        except Exception as e:
            logger.warning(f"Error shutting down tracer: {e}")

    _tracer_provider = None
    _is_initialized = False


class _NoOpTracer:
    """No-op tracer for when OTEL is not available."""

    def start_span(self, name: str, **kwargs):
        return _NoOpSpan()

    def start_as_current_span(self, name: str, **kwargs):
        return _NoOpContextManager()


class _NoOpSpan:
    """No-op span."""

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def add_event(self, name: str, attributes: Optional[Dict] = None) -> None:
        pass

    def set_status(self, status: Any) -> None:
        pass

    def end(self, end_time: Optional[int] = None) -> None:
        pass

    def record_exception(self, exception: Exception) -> None:
        pass


class _NoOpContextManager:
    """No-op context manager."""

    def __enter__(self):
        return _NoOpSpan()

    def __exit__(self, *args):
        pass


# Keep the setup API and exporter factory signatures while applying content
# controls to each exporter's own span view, including batch exports.
from ._content_export import _configure_content_exports
_configure_content_exports(globals())


__all__ = [
    "setup_tracing",
    "get_tracer",
    "get_current_span",
    "is_tracing_enabled",
    "trace_llm_call",
    "shutdown_tracing",
]
