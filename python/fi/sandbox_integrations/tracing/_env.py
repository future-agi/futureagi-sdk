"""Trace context for a sandbox command's ``env``, and the in-sandbox side that reads it back.

``tracing_env()`` returns ``TRACEPARENT`` and ``TRACESTATE`` (the OpenTelemetry environment-carrier
names for W3C Trace Context) for a span: the one you pass, else the current one. Every other key is
opt-in and off by default: ``BAGGAGE``, ``FI_BASE_URL``, ``FI_PROJECT_NAME``,
``FI_PROJECT_VERSION_NAME``, ``FI_HIDE_*`` / ``FI_PII_REDACTION`` and ``OTEL_RESOURCE_ATTRIBUTES``.
No result ever holds a name in :data:`REFUSED_ENV_NAMES`: a command's ``env`` is for plain,
non-secret values only.

OpenTelemetry is imported when a function runs, not when this module loads. Without it, or with no
valid span, the result has no trace keys. The W3C propagators are used directly (not the globally
configured ones), so the keys follow W3C conventions regardless of ``OTEL_PROPAGATORS``.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Mapping, Optional
from urllib.parse import quote

from fi.sandbox.errors import ConfigurationError

#: Credential names that do not go into a command's ``env``. A refusal list for the SDK's own names,
#: not a secret detector.
REFUSED_ENV_NAMES = frozenset(
    {
        "FI_API_KEY",
        "FI_SECRET_KEY",
        "FUTUREAGI_OMEGA_API_KEY",
        "FI_PLATFORM_TOKEN",
        "OMEGA_OS_API_KEY",
    }
)

#: The environment-carrier names, by the lower-case key the W3C propagators use.
_CARRIER_NAMES = {"traceparent": "TRACEPARENT", "tracestate": "TRACESTATE", "baggage": "BAGGAGE"}
_PRIVACY_PREFIX = "FI_HIDE_"
_PRIVACY_NAMES = ("FI_PII_REDACTION",)


def refuse_secret_names(env: Optional[Mapping[str, str]], operation: str) -> None:
    """Raise ``ConfigurationError(code="secret_in_env")`` when ``env`` names a refused variable.
    The message names the variable, not its value."""
    if not env:
        return
    for name in env:
        if str(name).upper() in REFUSED_ENV_NAMES:
            raise ConfigurationError(
                f"{operation}: {name} may not be passed in a command's env. A command's env is for "
                "plain, non-secret values only; credentials do not travel there.",
                code="secret_in_env",
                operation=operation,
            )


def _trace_keys(span: Any, baggage: bool) -> Dict[str, str]:
    """TRACEPARENT / TRACESTATE (and BAGGAGE when asked) for ``span`` or the current span."""
    try:
        from opentelemetry import trace  # the top-level name first: a blocked package stops here
        from opentelemetry.baggage.propagation import W3CBaggagePropagator
        from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    except ImportError:
        return {}
    context = trace.set_span_in_context(span) if span is not None else None
    carrier: Dict[str, str] = {}
    TraceContextTextMapPropagator().inject(carrier, context=context)
    if "traceparent" not in carrier:
        return {}  # no valid span: like the no-op API, nothing to join
    if baggage:
        W3CBaggagePropagator().inject(carrier, context=context)
    out: Dict[str, str] = {}
    for key, value in carrier.items():
        name = _CARRIER_NAMES.get(key.lower())
        if name is None or (name == "BAGGAGE" and not baggage) or not value:
            continue
        out[name] = value
    return out


def _resource_attributes(attributes: Mapping[str, Any]) -> str:
    """``key=value`` pairs joined by commas, values percent-encoded (``OTEL_RESOURCE_ATTRIBUTES``)."""
    pairs = []
    for key, value in attributes.items():
        name = str(key)
        if not name or name != name.strip() or any(c in name for c in ",= \t\r\n"):
            raise ConfigurationError(
                f"tracing_env: resource attribute name {name!r} may not be empty or hold a comma, "
                "an equals sign or white space",
                code="invalid_option",
                operation="tracing_env",
            )
        pairs.append(f"{name}={quote(str(value), safe='')}")
    return ",".join(pairs)


def tracing_env(
    *,
    span: Any = None,
    baggage: bool = False,
    collector: bool = False,
    project_name: Optional[str] = None,
    project_version_name: Optional[str] = None,
    privacy_flags: bool = False,
    resource_attributes: Optional[Mapping[str, Any]] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> Dict[str, str]:
    """Variables for ``sbx.commands.run(env=...)`` that carry the trace into the command.

    By default only ``TRACEPARENT`` and ``TRACESTATE`` (``TRACESTATE`` only when the span carries
    trace state), for ``span`` (an OpenTelemetry span, for example ``ctx.span`` in an experiment)
    or else the current span. Each opt-in adds only its own keys:

    - ``baggage=True``: ``BAGGAGE`` from the same context.
    - ``collector=True``: ``FI_BASE_URL`` copied from ``environ`` (the collector address; not a secret).
    - ``project_name`` / ``project_version_name``: ``FI_PROJECT_NAME`` / ``FI_PROJECT_VERSION_NAME``
      (from the arguments; ``environ`` is not read for them).
    - ``privacy_flags=True``: every ``FI_HIDE_*`` and ``FI_PII_REDACTION`` copied from ``environ``.
    - ``resource_attributes``: ``OTEL_RESOURCE_ATTRIBUTES``, comma-joined ``key=value`` with
      percent-encoded values.

    ``environ`` defaults to ``os.environ``. No result holds a name in :data:`REFUSED_ENV_NAMES`.
    """
    source = os.environ if environ is None else environ
    out = _trace_keys(span, baggage)
    if collector and source.get("FI_BASE_URL"):
        out["FI_BASE_URL"] = source["FI_BASE_URL"]
    if project_name is not None:
        out["FI_PROJECT_NAME"] = str(project_name)
    if project_version_name is not None:
        out["FI_PROJECT_VERSION_NAME"] = str(project_version_name)
    if privacy_flags:
        for name, value in source.items():
            if name.startswith(_PRIVACY_PREFIX) or name in _PRIVACY_NAMES:
                out[name] = value
    if resource_attributes is not None:
        joined = _resource_attributes(resource_attributes)
        if joined:
            out["OTEL_RESOURCE_ATTRIBUTES"] = joined
    return {name: value for name, value in out.items() if name.upper() not in REFUSED_ENV_NAMES}


def context_from_env(environ: Optional[Mapping[str, str]] = None) -> Any:
    """Inside the sandbox: the OpenTelemetry context that ``TRACEPARENT``, ``TRACESTATE`` and
    ``BAGGAGE`` in ``environ`` (default ``os.environ``) describe, to attach before starting spans::

        from opentelemetry import context
        token = context.attach(context_from_env())

    Returns an empty context when ``TRACEPARENT`` is missing or malformed. Needs ``opentelemetry-api``
    where it runs."""
    try:
        from opentelemetry import context as otel_context
        from opentelemetry.baggage.propagation import W3CBaggagePropagator
        from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    except ImportError as error:
        raise ImportError(
            "context_from_env needs OpenTelemetry where it runs: install opentelemetry-api"
        ) from error
    source = os.environ if environ is None else environ
    carrier = {key: source[name] for key, name in _CARRIER_NAMES.items() if source.get(name)}
    ctx = TraceContextTextMapPropagator().extract(carrier, context=otel_context.Context())
    return W3CBaggagePropagator().extract(carrier, context=ctx)


__all__ = ["REFUSED_ENV_NAMES", "tracing_env", "context_from_env"]
