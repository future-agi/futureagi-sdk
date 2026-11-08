"""Synchronous HTTP transport with retry (httpx.Client)."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import httpx

from fi.gateway._constants import (
    DEFAULT_KEEPALIVE_CONNECTIONS,
    DEFAULT_KEEPALIVE_EXPIRY,
    DEFAULT_MAX_CONNECTIONS,
)
from fi.gateway._exceptions import APIConnectionError, APIStatusError, APITimeoutError
from fi.gateway._transport._base import (
    BaseClient,
    RequestOptions,
    T,
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
        """Send one attempt and raise the mapped error for a 246 or an error status."""
        arguments = self._request_arguments(options, agentcc_params)
        timeout = options.timeout or self._timeout
        client = self._ensure_client()

        try:
            response = client.request(
                **arguments, timeout=timeout, follow_redirects=False,
            )
        except httpx.TimeoutException as e:
            raise APITimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise APIConnectionError(f"Connection error: {e}") from e

        options._callback_http = response
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

        self._dispatch_callback("on_request_start", options)

        for attempt in range(loop_max + 1):
            try:
                result = attempt_once()
                self._dispatch_callback("on_request_end", options, result)
                return result
            except (APIStatusError, APIConnectionError) as exc:
                last_exc = exc
                delay = self._retry_delay(options, exc, attempt, max_retries)
                if delay is None:
                    raise
                time.sleep(delay)

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
        arguments = self._request_arguments(options, agentcc_params)
        timeout = options.timeout or self._timeout
        client = self._ensure_client()

        try:
            response = client.send(
                client.build_request(**arguments, timeout=timeout),
                stream=True, follow_redirects=False,
            )
        except httpx.TimeoutException as e:
            raise APITimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise APIConnectionError(f"Connection error: {e}") from e

        if response.status_code == 246 or response.status_code >= 400:
            try:
                response.read()
                self._check_status(response)
            finally:
                response.close()

        self._record_header_cost(response)
        return response

    def _open_stream(self, options: RequestOptions, agentcc_params: Any, chunk_cls: Any) -> Any:
        from fi.gateway._streaming import Stream, ResponseStream
        from fi.gateway.callbacks.base import StreamInfo
        from fi.gateway.types.responses import ResponseStreamEvent

        self._bind_request(options, agentcc_params)
        self._dispatch_callback("on_request_start", options)
        try:
            response = self._stream_request(options, agentcc_params)
            on_chunk, on_finish = self._stream_hooks(options, response)
            if chunk_cls is ResponseStreamEvent:
                stream = ResponseStream(response, on_chunk=on_chunk, on_finish=on_finish)
            else:
                stream = Stream(response, chunk_cls, on_chunk=on_chunk, on_finish=on_finish)
        except Exception as exc:
            if "response" in locals():
                response.close()
            self._dispatch_callback("on_error", options, exc)
            raise
        self._dispatch_callback("on_stream_start", options, StreamInfo(agentcc=stream.agentcc))
        return stream

    def close(self) -> None:
        """Close the pool's HTTP client, unless it was passed as ``http_client``."""
        self._pool.close()
