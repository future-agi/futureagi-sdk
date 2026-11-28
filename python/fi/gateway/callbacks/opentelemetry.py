"""OpenTelemetry callback — requires the 'otel' extra unless a tracer is supplied."""

from __future__ import annotations

import json
from typing import Any

from fi.gateway._utils import redact_headers
from fi.gateway.callbacks.base import CallbackHandler, redact_credentials


class OpenTelemetryCallback(CallbackHandler):
    """Export detached, credential-masked request attributes on one span per call."""

    def __init__(self, *, tracer: Any = None) -> None:
        if tracer is None:
            try:
                from opentelemetry import trace
            except ImportError as exc:
                raise ImportError("Install futureagi[gateway-otel] or supply a tracer.") from exc

            tracer = trace.get_tracer("fi.gateway")
        self._tracer = tracer
        self._spans: dict[int, Any] = {}

    def on_request_start(self, request: Any) -> None:
        span = self._tracer.start_span("gateway.request")
        self._spans[id(request)] = span
        span.set_attribute("http.request.method", request.method)
        span.set_attribute("url.path", request.url)
        headers = {key: value for key, value in request.headers.items()
                   if key.lower() != "x-agentcc-config"}
        for name, value in (("body", request.body), ("headers", redact_headers(headers))):
            span.set_attribute("gateway.request." + name,
                               json.dumps(redact_credentials(value), default=str))
        # File payloads and streams are not telemetry, even when caller-owned.

    def on_request_end(self, request: Any, response: Any) -> None:
        span = self._spans.pop(id(request), None)
        if span is not None:
            span.set_attribute("http.response.status_code", response.status_code)
            span.end()

    def on_error(self, request: Any, error: Exception) -> None:
        span = self._spans.pop(id(request), None)
        if span is not None:
            span.set_attribute("error.type", type(error).__name__)
            span.end()
