"""Released callback/session lifecycle adapted to split transports."""

from __future__ import annotations

import logging
from typing import Any


class CallbackLifecycle:
    def _bind_request(self, options: Any, params: Any = None) -> None:
        options._callback_params = params
        options._callback_request = None
        options._callback_http = None
        options._callback_session = getattr(self._owner, "_active_session", None)
        options._callback_request = self._for_callbacks(options)

    def _for_callbacks(self, options: Any) -> Any:
        from fi.gateway.callbacks.base import (
            CallbackRequest, redact_callback_request, redact_credentials,
        )
        from fi.gateway._utils import redact_headers

        if isinstance(options, CallbackRequest):
            return options
        cached = getattr(options, "_callback_request", None)
        if cached is not None:
            return cached
        # Released callbacks saw request-level headers, not composed auth/config.
        # Exclude config even when supplied explicitly: it can contain virtual keys.
        headers = {k: v for k, v in options.headers.items()
                   if k.lower() != "x-agentcc-config"}
        # Multipart files were never part of the released callback body.
        body = options.form if options.files is not None else options.body
        request = CallbackRequest(
            method=options.method, url=self._build_url(options.url),
            headers=redact_credentials(redact_headers(headers)), body=redact_credentials(body),
            timeout=options.timeout, max_retries=options.max_retries,
        )
        return redact_callback_request(request) if self._redact_messages else request

    def _callback_response(self, options: Any, result: Any) -> Any:
        from fi.gateway.callbacks.base import CallbackResponse
        from fi.gateway.types.agentcc_metadata import AgentCCMetadata

        if isinstance(result, CallbackResponse):
            return result
        http = getattr(options, "_callback_http", None)
        meta = getattr(result, "agentcc", None)
        if meta is None and http is not None:
            meta = AgentCCMetadata.from_headers(dict(http.headers), http_response=http)
        if hasattr(result, "model_dump"):
            try:
                body = result.model_dump(mode="json", exclude={"agentcc"})
            except Exception:
                # A logging snapshot must not replace a successful SDK result.
                body = None
        elif isinstance(result, dict):
            body = result
        else:
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
                        "Callback %s.%s raised", type(callback).__name__, method, exc_info=True,
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
            self._response_events(request, response)
            session = getattr(options, "_callback_session", None)
            if session is not None:
                usage = getattr(rest[0], "usage", None)
                session.track_request(
                    cost=getattr(response.agentcc, "cost", None) or 0.0,
                    tokens=getattr(usage, "total_tokens", None) or 0,
                )
            return
        self._call_callbacks(method, request, *rest)
        if method == "on_error":
            from fi.gateway._exceptions import GuardrailBlockedError, GuardrailWarning

            error = rest[0]
            if isinstance(error, GuardrailWarning):
                self._call_callbacks("on_guardrail_warning", request, error)
            elif isinstance(error, GuardrailBlockedError):
                self._call_callbacks("on_guardrail_block", request, error)

    def _stream_hooks(self, options: Any, response: Any) -> tuple[Any, Any]:
        from fi.gateway.callbacks.base import CallbackResponse, StreamInfo
        from types import SimpleNamespace

        def on_chunk(chunk: Any) -> None:
            self._dispatch_callback("on_stream_chunk", options, chunk)

        def on_finish(stream: Any, error: Exception | None) -> None:
            if error is not None:
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
