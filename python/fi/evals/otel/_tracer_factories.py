"""Factories for tracer."""
from __future__ import annotations

from fi.evals.otel.tracer import (
    Any, CompositeSpanProcessor, ExporterConfig, Optional, TraceConfig,
)

def _create_sampler(config: TraceConfig) -> Any:
    """Create a sampler based on configuration."""
    from fi.evals.otel.tracer import (Any, SamplingStrategy, TraceConfig)
    from opentelemetry.sdk.trace.sampling import (
        ALWAYS_ON,
        ALWAYS_OFF,
        TraceIdRatioBased,
        ParentBased,
    )

    if config.sampling_strategy == SamplingStrategy.ALWAYS_ON:
        return ALWAYS_ON
    elif config.sampling_strategy == SamplingStrategy.ALWAYS_OFF:
        return ALWAYS_OFF
    elif config.sampling_strategy == SamplingStrategy.RATIO:
        return TraceIdRatioBased(config.sampling_ratio)
    elif config.sampling_strategy == SamplingStrategy.PARENT_BASED:
        return ParentBased(TraceIdRatioBased(config.sampling_ratio))
    else:
        return ALWAYS_ON


def _create_exporter(config: ExporterConfig) -> Optional[Any]:
    """Create an exporter based on configuration."""
    from fi.evals.otel.tracer import (Any, ExporterConfig, ExporterType, Optional, logger, os)
    try:
        if config.type == ExporterType.CONSOLE:
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            return ConsoleSpanExporter()

        elif config.type == ExporterType.OTLP_GRPC:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            return OTLPSpanExporter(
                endpoint=config.endpoint or "localhost:4317",
                headers=config.headers or None,
                insecure=config.insecure,
                timeout=config.timeout_ms // 1000,
            )

        elif config.type == ExporterType.OTLP_HTTP:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )
            return OTLPSpanExporter(
                endpoint=config.endpoint or "http://localhost:4318/v1/traces",
                headers=config.headers or None,
                timeout=config.timeout_ms // 1000,
            )

        elif config.type == ExporterType.JAEGER:
            try:
                from opentelemetry.exporter.jaeger.thrift import JaegerExporter
                return JaegerExporter(
                    agent_host_name=config.endpoint.split(":")[0] if config.endpoint else "localhost",
                    agent_port=int(config.endpoint.split(":")[1]) if config.endpoint and ":" in config.endpoint else 6831,
                )
            except ImportError:
                logger.warning("Jaeger exporter not available. Install opentelemetry-exporter-jaeger")
                return None

        elif config.type == ExporterType.ZIPKIN:
            try:
                from opentelemetry.exporter.zipkin.json import ZipkinExporter
                return ZipkinExporter(
                    endpoint=config.endpoint or "http://localhost:9411/api/v2/spans",
                )
            except ImportError:
                logger.warning("Zipkin exporter not available. Install opentelemetry-exporter-zipkin")
                return None

        elif config.type in (ExporterType.ARIZE, ExporterType.PHOENIX, ExporterType.LANGFUSE):
            # These platforms support OTLP
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )
            return OTLPSpanExporter(
                endpoint=config.endpoint,
                headers=config.headers or None,
            )

        elif config.type == ExporterType.FUTUREAGI:
            # Use OTLP HTTP for FutureAGI backend
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )
            if config.endpoint:
                endpoint = config.endpoint
            else:
                base = os.environ.get("FI_BASE_URL", "https://api.futureagi.com")
                endpoint = f"{base.rstrip('/')}/tracer/v1/traces"
            # Auto-inject FI auth headers if not provided
            headers = config.headers
            if not headers:
                api_key = os.environ.get("FI_API_KEY", "")
                secret_key = os.environ.get("FI_SECRET_KEY", "")
                if api_key and secret_key:
                    headers = {
                        "X-Api-Key": api_key,
                        "X-Secret-Key": secret_key,
                    }
            return OTLPSpanExporter(
                endpoint=endpoint,
                headers=headers or None,
            )

        else:
            logger.warning(f"Unsupported exporter type: {config.type}")
            return None

    except ImportError as e:
        logger.warning(f"Failed to create exporter {config.type}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating exporter {config.type}: {e}")
        return None


def _create_custom_processors(config: TraceConfig) -> Optional[CompositeSpanProcessor]:
    """Create custom span processors based on configuration."""
    from fi.evals.otel.tracer import (
        CompositeSpanProcessor, CostSpanProcessor, EvaluationSpanProcessor, LLMSpanProcessor,
        Optional, ProcessorType, TraceConfig,
    )
    processors = []

    # Check for processor configs
    processor_types = {p.type for p in config.processors if p.enabled}

    # LLM processor
    if ProcessorType.LLM in processor_types:
        processors.append(LLMSpanProcessor(
            capture_prompts=config.content.capture_prompts,
            capture_completions=config.content.capture_completions,
            max_content_length=config.content.max_content_length,
            redact_patterns=config.content.redact_patterns,
        ))

    # Evaluation processor
    if config.evaluation.enabled:
        processors.append(EvaluationSpanProcessor(
            metrics=config.evaluation.metrics,
            sample_rate=config.evaluation.sample_rate,
            async_evaluation=config.evaluation.async_evaluation,
            timeout_ms=config.evaluation.timeout_ms,
            cache_enabled=config.evaluation.cache_enabled,
            cache_ttl_seconds=config.evaluation.cache_ttl_seconds,
            evaluator_model=config.evaluation.evaluator_model,
        ))

    # Cost processor
    if config.cost.enabled:
        processors.append(CostSpanProcessor(
            custom_pricing=None,  # Could extend config for this
            alert_threshold_usd=config.cost.alert_threshold_usd,
        ))

    if not processors:
        return None

    return CompositeSpanProcessor(processors)
