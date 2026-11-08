"""Released callback/session lifecycle adapted to split transports."""

from __future__ import annotations

import json
import logging

import httpx
import weakref
from dataclasses import replace
from types import SimpleNamespace
from typing import Any


class _FormRequest:
    """Expose an explicit multipart form as the published live body field."""

    def __init__(self, options: Any) -> None:
        object.__setattr__(self, "_options", options)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._options, "form" if name == "body" else name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self._options, "form" if name == "body" else name, value)


class CallbackLifecycle:
    @property
    def _snapshot_callbacks(self) -> bool:
        return getattr(self._owner, "_callback_mode", "published") == "snapshot"

    @property
    def _expanded_events(self) -> bool:
        return getattr(self._owner, "_expanded_callback_events", False)

    def _bind_request(self, options: Any, params: Any = None) -> None:
        # Session objects reference the client. Keep them off the live descriptor.
        sessions = getattr(self, "_callback_sessions", None)
        if sessions is None:
            sessions = self._callback_sessions = {}
        sessions[id(options)] = getattr(self._owner, "_active_session", None)
        weakref.finalize(options, sessions.pop, id(options), None)
        options._callback_request = None
        options._callback_http = None
        options._callback_request = self._for_callbacks(options)

    def _remember_callback_response(self, options: Any, response: Any) -> None:
        # The send boundary has already scrubbed the exchange's request headers.
        options._callback_http = response

    def _for_callbacks(self, options: Any) -> Any:
        from fi.gateway.callbacks.base import CallbackRequest, redact_body, redact_credentials
        from fi.gateway._utils import redact_headers

        if isinstance(options, CallbackRequest):
            return options
        cached = getattr(options, "_callback_request", None)
        if cached is not None:
            return cached
        has_form = options.files is not None and options.form is not None
        body = options.form if has_form else options.body
        if self._snapshot_callbacks:
            headers = {k: v for k, v in options.headers.items() if k.lower() != "x-agentcc-config"}
            request = CallbackRequest(
                method=options.method, url=self._build_url(options.url),
                headers=redact_credentials(redact_headers(headers)), body=redact_credentials(body),
                timeout=options.timeout, max_retries=options.max_retries, files=None,
            )
            if self._redact_messages:
                request.body = redact_body(request.body)
            return request
        if self._redact_messages:
            # Exactly the published shallow redactor: untouched containers,
            # headers and files remain shared; descriptor assignment is detached.
            request = replace(options, body=redact_body(body))
            if has_form:
                request.form = request.body
            return request
        return _FormRequest(options) if has_form else options

    def _snapshot_response(self, options: Any, result: Any) -> Any:
        """Detach only JSON data and HTTP header diagnostics, never client graphs."""
        from fi.gateway.callbacks.base import CallbackResponse
        from fi.gateway.types.agentcc_metadata import AgentCCMetadata

        original_meta = getattr(result, "agentcc", None)
        http = getattr(original_meta, "http_response", None)
        if http is None:
            http = getattr(options, "_callback_http", None)
        headers = dict(getattr(http, "headers", getattr(result, "headers", {})) or {})
        status = getattr(http, "status_code", getattr(result, "status_code", 200))
        # No stream, extensions, history, client or exception graph is copied.
        # A fresh HTTP envelope keeps the diagnostic header API usable.
        request = getattr(http, "_request", None)
        detached_http = httpx.Response(
            status, headers=headers,
            request=httpx.Request(request.method, str(request.url), headers=request.headers)
            if request is not None else None,
        )
        meta = AgentCCMetadata.from_headers(headers, http_response=detached_http)
        body = parsed = None
        try:
            if hasattr(result, "model_dump"):
                body = result.model_dump(mode="json", exclude={"agentcc"})
                parsed = type(result).model_validate(body)
                object.__setattr__(parsed, "agentcc", meta)
            elif isinstance(result, CallbackResponse):
                body = json.loads(json.dumps(result.body))
            elif isinstance(result, (dict, list)):
                body = json.loads(json.dumps(result))
            elif isinstance(result, (bytes, bytearray)):
                parsed = bytes(result)
        except Exception:
            # A logging snapshot must not replace a successful SDK result, nor
            # fall back to a caller-owned object when it cannot be serialized.
            body = parsed = None
        return CallbackResponse(status_code=status, headers=headers, agentcc=meta,
                                body=body, _parsed=parsed)

    def _callback_response(self, options: Any, result: Any) -> Any:
        from fi.gateway.callbacks.base import CallbackResponse

        if self._snapshot_callbacks:
            return self._snapshot_response(options, result)
        if isinstance(result, CallbackResponse):
            return result
        meta = getattr(result, "agentcc", None)
        http = getattr(meta, "http_response", None)
        if meta is None and self._expanded_events:
            # Raw bytes and control-plane JSON have no metadata attribute. Keep
            # the published empty callback envelope unless events are opted in.
            http = getattr(options, "_callback_http", None)
            if http is not None:
                from fi.gateway.types.agentcc_metadata import AgentCCMetadata

                meta = AgentCCMetadata.from_headers(http.headers, http_response=http)
        try:
            body = result.model_dump() if hasattr(result, "model_dump") else None
        except Exception:
            body = None
        return CallbackResponse(
            status_code=getattr(http, "status_code", 200),
            headers=dict(getattr(http, "headers", {}) or {}), agentcc=meta,
            body=body, _parsed=result,
        )

    def _call_callbacks(self, method: str, *args: Any) -> None:
        for callback in self._callbacks:
            fn = getattr(callback, method, None)
            if fn is not None:
                try:
                    fn(*args)
                except Exception:
                    logging.getLogger("fi.gateway").debug(
                        "Callback %s.%s raised an exception", type(callback).__name__, method, exc_info=True,
                    )

    def _response_events(self, request: Any, response: Any) -> None:
        meta = response.agentcc
        if meta is None:
            return
        cache = getattr(meta, "cache_status", None)
        if cache and cache.lower() not in {"miss", "bypass", "disabled"}:
            self._call_callbacks("on_cache_hit", request, response, cache)
        cost = getattr(meta, "cost", None)
        if cost is not None:
            self._call_callbacks("on_cost_update", request, cost, getattr(self._owner, "current_cost", cost))
        if getattr(meta, "fallback_used", False):
            self._call_callbacks(
                "on_fallback", request, (request.body or {}).get("model", ""),
                getattr(meta, "model_used", None) or "", "gateway reported fallback",
            )

    def _dispatch_callback(self, method: str, *args: Any) -> None:
        if not args:
            return self._call_callbacks(method)
        options, *rest = args
        request = self._for_callbacks(options)
        if method == "on_request_end":
            response = self._callback_response(options, rest[0])
            self._call_callbacks(method, request, response)
            if self._expanded_events:
                self._response_events(request, response)
            session = getattr(self, "_callback_sessions", {}).get(id(options))
            if session is not None and (self._snapshot_callbacks or not isinstance(rest[0], (bytes, bytearray))):
                usage = getattr(rest[0], "usage", None)
                session.track_request(
                    cost=getattr(response.agentcc, "cost", None) or 0.0,
                    tokens=getattr(usage, "total_tokens", None) or 0,
                )
            return
        self._call_callbacks(method, request, *rest)
        if method == "on_error" and self._expanded_events:
            from fi.gateway._exceptions import GuardrailBlockedError, GuardrailWarning

            error = rest[0]
            if isinstance(error, GuardrailWarning):
                self._call_callbacks("on_guardrail_warning", request, error)
            elif isinstance(error, GuardrailBlockedError):
                self._call_callbacks("on_guardrail_block", request, error)

    def _stream_hooks(self, options: Any, response: Any) -> tuple[Any, Any]:
        from fi.gateway.callbacks.base import CallbackResponse, StreamInfo

        def on_chunk(chunk: Any) -> None:
            self._dispatch_callback("on_stream_chunk", options, chunk)

        def on_finish(stream: Any, error: Exception | None) -> None:
            if error is not None:
                import httpx
                from fi.gateway._retry_policy import _UNKNOWN_DISPATCH_REMEDY

                # Stream iteration is outside the send wrapper. Do not expose its
                # original HTTPX request through the StreamError exception chain.
                cause = error.__cause__ or error.__context__
                if isinstance(cause, httpx.RequestError):
                    error.message = "Stream interrupted while reading the response body."
                    error.__cause__ = None
                    error.__context__ = None
                    if getattr(error, "dispatched", None) == "unknown":
                        error.message += " " + _UNKNOWN_DISPATCH_REMEDY
                error.args = (error.message,)
                self._dispatch_callback("on_error", options, error)
                return
            self._dispatch_callback(
                "on_stream_end", options,
                StreamInfo(agentcc=stream.agentcc, chunk_count=stream.chunk_count), stream.completion,
            )
            result = CallbackResponse(
                status_code=response.status_code, headers=dict(response.headers),
                agentcc=stream.agentcc, body=None,
                _parsed=SimpleNamespace(usage=stream.usage),
            )
            self._dispatch_callback("on_request_end", options, result)

        return on_chunk, on_finish
