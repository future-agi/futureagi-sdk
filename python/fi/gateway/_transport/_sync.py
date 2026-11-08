"""Synchronous HTTP transport with retry (httpx.Client)."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

import httpx

from fi.gateway._constants import (
    DEFAULT_KEEPALIVE_CONNECTIONS,
    DEFAULT_KEEPALIVE_EXPIRY,
    DEFAULT_MAX_CONNECTIONS,
)
from fi.gateway._exceptions import APIConnectionError, APIStatusError
from fi.gateway._gateway_evidence import capture_gateway_evidence
from fi.gateway._http_security import validate_destination
from fi.gateway._transport._response import (
    ResponseCapture, body_decode_error, close_response, safe_response, protect_stream_cleanup,
)
from fi.gateway._transport._scrub import scrub_sent_request
from fi.gateway._transport._base import (
    BaseClient,
    RequestOptions,
    T,
    _transport_error,
)


class SyncBaseClient(BaseClient):
    """Synchronous HTTP transport with retry."""

    def _ensure_client(self) -> httpx.Client:
        """The pool's httpx client, built on first use (shared with ``with_options()`` copies)."""
        client: httpx.Client = self._pool.get(self._new_http_client)
        return client

    def _new_http_client(self) -> httpx.Client:
        return httpx.Client(
            timeout=self._timeout,
            limits=httpx.Limits(
                max_connections=DEFAULT_MAX_CONNECTIONS,
                max_keepalive_connections=DEFAULT_KEEPALIVE_CONNECTIONS,
                keepalive_expiry=DEFAULT_KEEPALIVE_EXPIRY,
            ),
        )

    def _send(
        self, options: RequestOptions, agentcc_params: dict[str, Any] | None
    ) -> httpx.Response:
        """Send and consume one attempt, including its completion-warning body."""
        response = self._send_response(options, agentcc_params, streaming=False)
        self._remember_callback_response(options, response)
        return response

    def _send_response(
        self, options: RequestOptions, agentcc_params: Any, *, streaming: bool,
    ) -> httpx.Response:
        arguments, composed_names = self._request_arguments(options, agentcc_params, stream=streaming)
        timeout = options.timeout or self._timeout
        client = self._ensure_client()
        capture = ResponseCapture()
        failure = None
        request = response = error = None
        try:
            with capture.client(client) as sender:
                try:
                    if streaming:
                        request = sender.build_request(**arguments, timeout=timeout)
                        validate_destination(self._base_url, str(request.url), warn_cleartext=False)
                        response = sender.send(request, stream=True, follow_redirects=False)
                    else:
                        # Preserve the caller's request() override without building
                        # or consuming an upload twice. Capture still observes each
                        # actual exchange before response hooks and body readers.
                        url = httpx.URL(arguments["url"], params=client.params or None)
                        validate_destination(self._base_url, str(url), warn_cleartext=False)
                        response = sender.request(**arguments, timeout=timeout, follow_redirects=False)
                except BaseException as exc:
                    error = exc
                    raise
                finally:
                    scrub_sent_request(request, response, error, composed_names)
                    capture.scrub(composed_names)
            capture.capture(response)
            if not streaming or response.status_code == 246 or response.status_code >= 400:
                response.read()
        except httpx.TransportError as exc:
            failure = _transport_error(exc, capture.evidence, capture.status, capture.response)
        except (httpx.RequestError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            if capture.response is not None and capture.status is not None and capture.status >= 400:
                failure = APIStatusError.from_response(safe_response(capture.response))
            else:
                failure = body_decode_error(exc, capture.evidence)
        finally:
            if error is not None or failure is not None or not streaming or (capture.status is not None and (
                capture.status == 246 or capture.status >= 400
            )):
                close_response(capture.response)
        if failure is not None:
            # No original request-bearing exception in either cause or context.
            raise failure
        self._check_status(response)
        return response

    def _request(
        self,
        options: RequestOptions,
        response_cls: type[T],
        agentcc_params: dict[str, Any] | None = None,
    ) -> T:
        """Execute a single HTTP request and return the parsed response."""
        response = self._send(options, agentcc_params)
        return self._process_response_body(response, response_cls)

    def _request_raw(
        self,
        options: RequestOptions,
        agentcc_params: dict[str, Any] | None = None,
    ) -> bytes:
        """Execute a single HTTP request and return the raw response bytes."""
        response = self._send(options, agentcc_params)
        self._record_header_cost(response)
        return response.content

    def _retrying(self, options: RequestOptions, attempt_once: Callable[[], T]) -> T:
        """Run *attempt_once* under the retry policy, firing the request callbacks."""
        max_retries = (
            options.max_retries
            if options.max_retries is not None
            else self._max_retries
        )
        loop_max = self._retry_loop_bound(max_retries)
        last_exc: Exception | None = None
        in_flight_replayed = False

        self._dispatch_callback("on_request_start", options)

        for attempt in range(loop_max + 1):
            try:
                result = attempt_once()
                self._dispatch_callback("on_request_end", options, result)
                return result
            except (APIStatusError, APIConnectionError) as exc:
                last_exc = exc
                if in_flight_replayed:
                    # The one credit replay exhausts this request, even if the
                    # next failure is a different status, connection or timeout.
                    self._dispatch_callback("on_error", options, exc)
                    raise
                delay = self._retry_delay(options, exc, attempt, max_retries)
                if delay is None:
                    raise
                in_flight_replayed = isinstance(exc, APIStatusError) and exc.status_code == 402
                time.sleep(delay)
            except Exception as exc:
                self._dispatch_callback("on_error", options, exc)
                raise

        # Unreachable while every limit is at most the loop bound; kept as a guard.
        if last_exc is not None:
            self._dispatch_callback("on_error", options, last_exc)
            raise last_exc
        raise RuntimeError("Retry loop exited unexpectedly")  # pragma: no cover

    def _request_with_retry(
        self,
        options: RequestOptions,
        response_cls: type[T],
        agentcc_params: dict[str, Any] | None = None,
    ) -> T:
        """Execute a request with retry logic."""
        self._bind_request(options, agentcc_params)
        return self._retrying(
            options, lambda: self._request(options, response_cls, agentcc_params)
        )

    def _request_raw_with_retry(
        self,
        options: RequestOptions,
        agentcc_params: dict[str, Any] | None = None,
    ) -> bytes:
        """Execute a raw-bytes request with retry logic."""
        self._bind_request(options, agentcc_params)
        return self._retrying(
            options, lambda: self._request_raw(options, agentcc_params)
        )

    def _stream_request(
        self,
        options: RequestOptions,
        agentcc_params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute a streaming request and return the raw response."""
        response = self._send_response(options, agentcc_params, streaming=True)
        self._record_header_cost(response)
        return response

    def _open_stream(self, options: RequestOptions, agentcc_params: Any, chunk_cls: Any) -> Any:
        from fi.gateway._streaming import Stream, ResponseStream
        from fi.gateway.callbacks.base import StreamInfo
        from fi.gateway.types.responses import ResponseStreamEvent

        self._bind_request(options, agentcc_params)
        self._dispatch_callback("on_request_start", options)
        response = None
        failure = None
        try:
            response = self._stream_request(options, agentcc_params)
            protect_stream_cleanup(response)
            on_chunk, on_finish = self._stream_hooks(options, response)
            if chunk_cls is ResponseStreamEvent:
                stream = ResponseStream(response, on_chunk=on_chunk, on_finish=on_finish)
            else:
                stream = Stream(response, chunk_cls, on_chunk=on_chunk, on_finish=on_finish)
        except httpx.TransportError as exc:
            failure = _transport_error(exc, capture_gateway_evidence(response),
                                       response.status_code if response is not None else None, response)
        except (httpx.RequestError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            failure = (body_decode_error(exc, capture_gateway_evidence(response))
                       if response is not None else exc)
        except Exception as exc:
            failure = exc
        if failure is not None:
            close_response(response)
            self._dispatch_callback("on_error", options, failure)
            raise failure
        self._dispatch_callback("on_stream_start", options, StreamInfo(agentcc=stream.agentcc))
        return stream

    def close(self) -> None:
        """Close the pool's HTTP client, unless it was passed as ``http_client``."""
        self._pool.close()
