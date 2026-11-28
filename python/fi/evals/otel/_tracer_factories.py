"""Factories for tracer."""
from __future__ import annotations

from fi.evals.otel.tracer import (
    Any, CompositeSpanProcessor, ExporterConfig, Optional, TraceConfig,
)

def _create_sampler(config: TraceConfig) -> Any:
    """Create a sampler based on configuration."""
    from fi.evals.otel.tracer import (Any, SamplingStrategy, TraceConfig)
    from opentelemetry.sdk.trace.sampling import ALWAYS_ON, ALWAYS_OFF, TraceIdRatioBased, ParentBased

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


def _answering_redirects(exporter_class: Any) -> Any:
    """An OTLP HTTP exporter class whose ``export`` reports a refused 3xx answer as a failed export, as the
    exporter contract asks, instead of raising it."""
    from opentelemetry.sdk.trace.export import SpanExportResult

    if not isinstance(exporter_class, type):
        # Not a class to extend: the caller's header check then refuses what it builds.
        return exporter_class

    class _Exporter(exporter_class):
        def export(self, spans: Any) -> Any:
            from fi.errors import KeyedRedirectRefusedError

            try:
                return super().export(spans)
            except KeyedRedirectRefusedError:
                return SpanExportResult.FAILURE

    from fi._core.loopback import dial_localhost_channels

    return dial_localhost_channels(_Exporter)


def _futureagi_headers(config: ExporterConfig) -> Any:
    """The headers for a Future AGI endpoint: the configured ones, else the keys from the environment."""
    from fi.evals.otel.tracer import os

    headers = config.headers
    if not headers:
        api_key = os.environ.get("FI_API_KEY", "")
        secret_key = os.environ.get("FI_SECRET_KEY", "")
        if api_key and secret_key:
            headers = {
                "X-Api-Key": api_key,
                "X-Secret-Key": secret_key,
            }
    return headers


def _futureagi_http_exporter(config: ExporterConfig, endpoint: str) -> Any:
    """An OTLP HTTP exporter for a Future AGI endpoint.

    It sends the SDK's headers and nothing from OTEL_EXPORTER_OTLP_*, over a fresh session of the SDK's own
    that skips proxies for keyed or loopback plain HTTP requests. Requests carrying credentials refuse redirects;
    an unkeyed request can follow a readable redirect, and no hop reads .netrc, so a credential provider or netrc
    entry meant for the user's backend stays out of it."""
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    from fi._core.http_security import require_secure_credential_headers
    from fi._core.requests_session import LoopbackDirectSession
    from fi._otlp_headers import pin_headers, refuse_ambiguous_endpoint

    refuse_ambiguous_endpoint(endpoint, tls=endpoint.lower().startswith("https://"))
    headers = _futureagi_headers(config)
    require_secure_credential_headers(
        endpoint, headers, setting="FI_BASE_URL or the exporter endpoint", proxies_disabled=True
    )
    return pin_headers(
        _answering_redirects(OTLPSpanExporter)(
            endpoint=endpoint, headers=headers or None, session=LoopbackDirectSession()
        ),
        headers,
    )


def _user_endpoint_session() -> Any:
    """The session for an endpoint the user chose when no key of the SDK is in play: the SDK's direct session, carrying the
    headers of the user's own credential provider (OTEL_PYTHON_EXPORTER_OTLP_HTTP_*CREDENTIAL_PROVIDER) as that provider sets
    them. The provider's session is not used itself, so a request that carries credentials keeps the direct
    session's rules (no redirect, no proxy for plain http)."""
    from fi._core.requests_session import LoopbackDirectSession

    session = LoopbackDirectSession()
    try:
        from opentelemetry.exporter.otlp.proto.http._common import _load_session_from_envvar
        from opentelemetry.sdk.environment_variables import (
            _OTEL_PYTHON_EXPORTER_OTLP_HTTP_TRACES_CREDENTIAL_PROVIDER as traces_provider,
        )
    except ImportError:
        return session
    provided = _load_session_from_envvar(traces_provider)
    if provided is not None:
        session.headers.update(provided.headers)
        provided.close()
    return session


def _refuse_plain_http(endpoint: Any, setting: str = "the exporter endpoint", *, keys: bool = False) -> None:
    """The plain-http rule of the shared senders for an endpoint the SDK's keys may reach, then the exporter-only checks.

    The code a caller sees is the one the shared rule gives: ``InsecureHttpRefusedError`` for a Future AGI host and
    ``insecure_http_origin`` for another host without ``FI_ALLOW_INSECURE_HTTP=1``. The transports built here send plain
    http directly, so the proxy settings of the environment do not decide it."""
    from fi._core.http_security import future_agi_connect_host, require_secure_credentials_url
    from fi._otlp_headers import refuse_ambiguous_endpoint, refuse_plain_http_futureagi

    text = str(endpoint or "")
    # A Future AGI host takes https only, with or without keys in the headers.
    if text.strip().lower().startswith("http://") and (keys or future_agi_connect_host(text.strip()) is not None):
        refuse_ambiguous_endpoint(text)
        require_secure_credentials_url(text.strip(), setting=setting, proxies_disabled=True)
    refuse_plain_http_futureagi(endpoint, setting, keys=keys)


def _keyed_http_exporter(config: ExporterConfig, endpoint: str, exporter_class: Any, **extra: Any) -> Any:
    """An OTLP HTTP exporter for an endpoint that is not Future AGI's, when the exporter's own headers hold the
    SDK's keys: it sends over a session that follows no redirect and, for ``http://``, reaches its target directly."""
    from fi._otlp_headers import futureagi_session

    return exporter_class(endpoint=endpoint, headers=config.headers or None, session=futureagi_session(
        plain=endpoint.lower().startswith("http://")), **extra)


def _create_exporter(config: ExporterConfig) -> Optional[Any]:
    """Create an exporter based on configuration."""
    import dataclasses

    from fi._otlp_headers import refuse_plain_http_futureagi
    from fi.errors import ConfigurationError
    from fi.evals.otel.tracer import (Any, ExporterConfig, ExporterType, Optional, logger, os)
    from fi._core.loopback import grpc_channel_options
    from fi._keyed_errors import InsecureHttpRefusedError
    from fi._core.requests_session import LoopbackDirectSession
    from fi._core.http_security import (
        require_endpoint_with_keys, require_no_key_headers_in_otel_env, require_secure_credential_headers, require_secure_grpc_target,
    )
    from fi._core.proxy_routing import carries_credentials
    try:
        if isinstance(config.endpoint, str) and not config.endpoint.strip():
            # An endpoint that is empty or only white space is no endpoint.
            config = dataclasses.replace(config, endpoint=None)
        # The headers are read once into plain names and values: the checks, the pinning and the exporter all see
        # this copy, so the checks judge what is sent (a plain dict of plain text is handed on as it is).
        from fi._plain_headers import plain_header_copy
        copied = plain_header_copy(config.headers)
        if copied is not None:
            config = dataclasses.replace(config, headers=copied)
        # One check before any exporter is built: an endpoint read as two hosts is refused, whichever
        # host it names and whichever exporter type it is for.
        from fi._otlp_headers import _grpc_insecure_asked, refuse_ambiguous_endpoint

        endpoint_text = str(config.endpoint or "")
        if config.type == ExporterType.OTLP_GRPC:
            tls = not _grpc_insecure_asked(endpoint_text, config.insecure)
        else:
            tls = endpoint_text.lower().startswith("https://")
        refuse_ambiguous_endpoint(config.endpoint, tls=tls)
        if config.type not in (ExporterType.CONSOLE, ExporterType.FUTUREAGI):
            # the OpenTelemetry exporters read OTEL_EXPORTER_OTLP_*HEADERS themselves
            grpc_plain = config.type == ExporterType.OTLP_GRPC and not tls
            require_no_key_headers_in_otel_env(config.endpoint or "", plaintext=bool(grpc_plain))
        if config.type in (ExporterType.OTLP_HTTP, ExporterType.FUTUREAGI, ExporterType.ARIZE,
                           ExporterType.PHOENIX, ExporterType.LANGFUSE):
            from fi._otlp_headers import http_exporter_endpoint, require_readable_http_tls_files
            # Checked for the endpoint the exporter sends to: an http:// endpoint reads no CA file and no client key.
            require_readable_http_tls_files(http_exporter_endpoint(config.endpoint, config.type))
        if config.type == ExporterType.CONSOLE:
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            return ConsoleSpanExporter()

        elif config.type == ExporterType.OTLP_GRPC:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            from fi._otlp_headers import (
                INSECURE_GRPC_MESSAGE,
                INSECURE_LOOPBACK_GRPC_MESSAGE,
                carries_final_credentials,
                carries_sdk_keys,
                classify_grpc_endpoint,
                futureagi_grpc_credentials,
                grpc_loopback_target,
                grpc_plain_choice,
                _grpc_insecure_asked,
                pin_headers,
                refuse_env_key_headers,
                self_hosted_grpc_target,
            )

            require_endpoint_with_keys(config.endpoint, config.headers)
            endpoint = config.endpoint or "localhost:4317"
            # The mode the exporter opens: the argument, then OTEL_EXPORTER_OTLP_*INSECURE, then the scheme. The same
            # value is handed to the exporter below, so the mode judged here is the mode it uses.
            plaintext = _grpc_insecure_asked(endpoint, config.insecure)
            require_secure_grpc_target(endpoint, config.headers, insecure=plaintext)
            # Classified by the exact target the channel dials, not by the text as written.
            bound = classify_grpc_endpoint(endpoint)
            if not bound:
                # The environment's headers go to a collector the SDK did not choose: no key header among them.
                refuse_env_key_headers()
            if bound and not self_hosted_grpc_target(endpoint):
                # A channel bound for Future AGI uses TLS. For a Future AGI host, a plain channel asked for by
                # the argument, the ``http://`` scheme or OTEL_EXPORTER_OTLP_*INSECURE is refused; for a loopback
                # address named by FI_BASE_URL, FI_TRACES_URL or FI_GRPC_URL, ``insecure=True`` is refused.
                if grpc_loopback_target(endpoint):
                    if config.insecure:
                        raise ConfigurationError(INSECURE_LOOPBACK_GRPC_MESSAGE, code="insecure_loopback_grpc")
                elif config.insecure or endpoint.lower().startswith("http://") or _grpc_insecure_asked(endpoint, config.insecure):
                    raise InsecureHttpRefusedError(message=INSECURE_GRPC_MESSAGE)
            headers = _futureagi_headers(config) if bound else config.headers
            # The decision follows the final outgoing key set: the exporter's headers and the environment's
            # headers together. A self-managed target that takes the SDK's keys gets a plain channel only with
            # FI_ALLOW_INSECURE_HTTP=1 and no proxy.
            # The headers are judged by name and by value: a value that holds FI_API_KEY or FI_SECRET_KEY is a key too.
            keyed = carries_sdk_keys(config.headers) or carries_credentials(config.headers)
            plain = (bound or keyed) and grpc_plain_choice(endpoint, config.insecure)
            exporter = _answering_redirects(OTLPSpanExporter)(
                endpoint=endpoint,
                headers=headers or None,
                # A Future AGI channel is TLS whatever the setting holds. The value is a bool in every case: an unset
                # value would let the exporter read OTEL_EXPORTER_OTLP_*INSECURE again on its own.
                insecure=plain if bound else plaintext,
                timeout=config.timeout_ms // 1000,
                # A channel the environment's INSECURE setting makes plain is a plain channel as well.
                channel_options=grpc_channel_options(
                    endpoint, plaintext=(plain or plaintext)
                    and carries_final_credentials(headers)) or None,
                # On a Future AGI host no credential provider from the environment is loaded.
                **({"credentials": futureagi_grpc_credentials()} if bound and not plain else {}),
            )
            # On a Future AGI host: the SDK's headers and nothing from OTEL_EXPORTER_OTLP_*.
            return pin_headers(exporter, headers) if bound else exporter

        elif config.type == ExporterType.OTLP_HTTP:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )
            require_endpoint_with_keys(config.endpoint, config.headers)

            from fi._otlp_headers import carries_key_headers, is_future_agi_endpoint, refuse_env_key_headers

            endpoint = config.endpoint or "http://localhost:4318/v1/traces"
            bound = is_future_agi_endpoint(endpoint)
            if not bound:
                refuse_env_key_headers()
            keyed = bound or carries_key_headers(config.headers)
            _refuse_plain_http(endpoint, keys=keyed)
            if bound:
                # On the Future AGI host: the same pinned headers and session as the FUTUREAGI type.
                return _futureagi_http_exporter(config, endpoint)
            require_secure_credential_headers(endpoint, config.headers, setting="the exporter endpoint", proxies_disabled=True)
            return OTLPSpanExporter(
                endpoint=endpoint,
                headers=config.headers or None,
                timeout=config.timeout_ms // 1000,
                session=_user_endpoint_session() if not keyed else LoopbackDirectSession(),
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
                endpoint = config.endpoint or "http://localhost:9411/api/v2/spans"
                return ZipkinExporter(endpoint=endpoint, session=LoopbackDirectSession())
            except ImportError:
                logger.warning("Zipkin exporter not available. Install opentelemetry-exporter-zipkin")
                return None

        elif config.type in (ExporterType.ARIZE, ExporterType.PHOENIX, ExporterType.LANGFUSE):
            # These platforms support OTLP
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            from fi._otlp_headers import (
                carries_key_headers,
                is_future_agi_endpoint,
                refuse_ambiguous_endpoint,
                refuse_env_key_headers,
                resolved_http_endpoint,
            )

            require_endpoint_with_keys(config.endpoint, config.headers)
            # With no endpoint the exporter reads one from the environment: check what it will use.
            endpoint = config.endpoint or resolved_http_endpoint()
            refuse_ambiguous_endpoint(endpoint, tls=str(endpoint or "").lower().startswith("https://"))
            bound = is_future_agi_endpoint(endpoint)
            if not bound:
                refuse_env_key_headers()
            keyed = bound or carries_key_headers(config.headers)
            _refuse_plain_http(endpoint, keys=keyed)
            if bound:
                return _futureagi_http_exporter(config, endpoint)
            require_secure_credential_headers(endpoint or "", config.headers, setting="the exporter endpoint", proxies_disabled=True)
            return _answering_redirects(OTLPSpanExporter)(
                # A blank traces setting is unset: the endpoint is the one read above, or the exporter's own default.
                endpoint=endpoint or "http://localhost:4318/v1/traces",
                headers=config.headers or None,
                session=LoopbackDirectSession(),
            )

        elif config.type == ExporterType.FUTUREAGI:
            # Use OTLP HTTP for FutureAGI backend
            setting = "the exporter endpoint"
            if config.endpoint:
                endpoint = config.endpoint
            else:
                base = os.environ.get("FI_BASE_URL")
                if base is None or not base.strip():
                    base = "https://api.futureagi.com"
                else:
                    setting = "FI_BASE_URL"
                endpoint = f"{base.rstrip('/')}/tracer/v1/traces"
            # The exporter reads OTEL_EXPORTER_OTLP_*HEADERS itself: refused when its endpoint is not a Future AGI address.
            require_no_key_headers_in_otel_env(endpoint)
            _refuse_plain_http(endpoint, setting, keys=True)
            return _futureagi_http_exporter(config, endpoint)

        else:
            logger.warning(f"Unsupported exporter type: {config.type}")
            return None

    except ConfigurationError:
        raise
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
