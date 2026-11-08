"""The transport's shared half: request descriptor, header merge, URL join, retry decisions.

The sync and async transports (``_sync.py``, ``_async.py``) differ only in how they
send and sleep; everything they decide is decided here, once.
"""

from __future__ import annotations

import logging
import random
from abc import ABC
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

import httpx

from fi.gateway._constants import (
    DEFAULT_MAX_RETRIES, HEADER_RESPONSE_COST, RETRYABLE_STATUS_CODES,
)
from fi.gateway._transport._request import RequestBuilder, _uses_form
from fi.gateway._exceptions import APIConnectionError, APIStatusError, APITimeoutError
from fi.gateway._gateway_evidence import GatewayEvidence
from fi.gateway._transport._pool import HttpPool
from fi.gateway._transport._callbacks import CallbackLifecycle
from fi.gateway._utils import parse_timeout

logger = logging.getLogger("fi.gateway")

T = TypeVar("T")


def _transport_error(
    error: httpx.TransportError,
    evidence: GatewayEvidence,
    response_status: int | None,
    response: httpx.Response | None = None,
) -> APIConnectionError:
    """Keep public error classes, but replay only when the outcome is provably safe."""
    from fi.gateway._retry_policy import _UNKNOWN_DISPATCH_REMEDY
    from fi.gateway._transport._response import safe_response

    pre_send = response_status is None and isinstance(
        error, (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout),
    )
    # Never embed a caller/transport message: it can contain authentication data.
    message = "Request timed out." if isinstance(error, httpx.TimeoutException) else "Connection error."
    if not pre_send and evidence.dispatched == "unknown":
        message += " " + _UNKNOWN_DISPATCH_REMEDY
    cls = APITimeoutError if isinstance(error, httpx.TimeoutException) else APIConnectionError
    translated = cls(message, gateway_evidence=evidence)
    translated._retryable = pre_send and evidence.dispatched is not True
    if response is not None and response_status is not None and response_status >= 400:
        # An unreadable refusal is still an HTTP refusal. Use its status/headers,
        # not the timeout/connection retry budget; preserve the public error type.
        snapshot = safe_response(response)
        snapshot.status_code = response_status
        translated._status_error = APIStatusError.from_response(snapshot)
    return translated


@dataclass
class Timeout:
    """Fine-grained timeout configuration.

    All values are in seconds.  Pass a single ``float`` for a uniform timeout
    or use this class for per-phase control.
    """

    connect: float | None = None
    read: float | None = None
    write: float | None = None
    pool: float | None = None


@dataclass
class RetryConfig:
    """Configuration for the retry engine."""

    max_retries: int = DEFAULT_MAX_RETRIES
    backoff_factor: float = 0.5
    backoff_max: float = 8.0
    backoff_jitter: float = 0.25
    respect_retry_after: bool = True


@dataclass
class RequestOptions:
    """Internal request descriptor built by resource methods.

    ``body`` is sent as JSON, or serialized as published multipart fields when
    ``files`` is present. An explicit ``form`` supplies httpx-ready fields instead.
    """

    method: str
    url: str
    body: dict[str, Any] | None = None
    headers: dict[str, str] = field(default_factory=dict)
    timeout: httpx.Timeout | None = None
    max_retries: int | None = None
    files: dict[str, Any] | None = None
    form: dict[str, Any] | None = None


def send_arguments(options: RequestOptions, headers: dict[str, str]) -> dict[str, Any]:
    """The body arguments of one send: ``json=`` or, with ``files``, the multipart
    ``files=`` and ``data=``.

    A multipart send drops the JSON ``Content-Type`` from *headers* (any spelling), so
    httpx sets the form's own with its boundary.
    """
    if not _uses_form(options):
        return {"json": options.body}
    for name in [k for k in headers if k.lower() == "content-type"]:
        del headers[name]
    data = options.form
    if data is None:
        import json

        # Published multipart descriptors retain their unencoded body for callbacks.
        data = {
            key: value if isinstance(value, str) else json.dumps(value)
            if isinstance(value, (list, dict)) else str(value)
            for key, value in (options.body or {}).items()
        }
    return {"files": options.files, "data": data}


class BaseClient(RequestBuilder, CallbackLifecycle, ABC):
    """Shared logic for sync and async clients."""

    _api_key: str
    _base_url: str
    _timeout: httpx.Timeout
    _max_retries: int
    _retry_config: RetryConfig
    _default_headers: dict[str, str]
    _default_query: dict[str, str]
    _session_id: str | None
    _metadata: dict[str, Any] | None
    _config: Any  # GatewayConfig | None
    _callbacks: list[Any]
    _retry_policy: Any  # RetryPolicy | None

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout: float | Timeout | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_config: RetryConfig | None = None,
        default_headers: dict[str, str] | None = None,
        default_query: dict[str, str] | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        config: Any = None,
        callbacks: list[Any] | None = None,
        http_client: Any = None,
        retry_policy: Any = None,
        on_cost: Callable[[float], None] | None = None,
        pool: HttpPool | None = None,
        redact_messages: bool = False,
        owner: Any = None,
        metadata_mode: str = "replace",
    ) -> None:
        """``base_url`` has no default: there is no hosted fallback, so a key is never sent
        to a gateway the caller did not name.

        ``pool`` is the httpx client this transport sends through, shared with the
        client's ``with_options()`` copies; without one the transport has its own,
        holding ``http_client`` if given.
        """
        super().__init__(
            api_key=api_key, base_url=base_url, default_headers=default_headers,
            default_query=default_query, session_id=session_id,
            metadata=metadata, config=config, metadata_mode=metadata_mode,
        )
        self._redact_messages = redact_messages
        self._owner = owner
        if owner is not None:
            self._warned_http_origins = owner._warned_http_origins
            self._http_warning_lock = owner._http_warning_lock
        self._timeout = parse_timeout(timeout)
        self._max_retries = max_retries
        self._retry_config = retry_config or RetryConfig(max_retries=max_retries)
        self._callbacks = callbacks or []
        self._custom_http_client = http_client
        self._retry_policy = retry_policy
        self._on_cost = on_cost
        self._pool = pool if pool is not None else HttpPool(http_client)

    @property
    def _client(self) -> Any:
        """The httpx client sends go through, ``None`` until the first one."""
        return self._pool.client

    @property
    def _owns_client(self) -> bool:
        """Whether closing closes the httpx client (never one passed as ``http_client``)."""
        return self._pool.owned

    def _request_arguments(
        self, options: RequestOptions, params: Any = None, *, stream: bool = False,
    ) -> tuple[dict[str, Any], frozenset[str]]:
        """Build wire arguments and private names together, once per attempt."""
        headers, composed_names = self._build_headers(options, params)
        if stream and options.form is None:
            return {
                "method": options.method, "url": self._build_url(options.url),
                "headers": headers, "json": options.body,
            }, composed_names
        if not _uses_form(options):
            request = self._build_request(options, params, headers=headers)
            return {
                "method": request.method, "url": request.url,
                "headers": request.headers, "content": request.content,
            }, composed_names
        body = send_arguments(options, headers)
        return {
            "method": options.method, "url": self._build_url(options.url),
            "headers": headers, **body,
        }, composed_names

    def _should_retry(self, status_code: int, attempt: int, max_retries: int) -> bool:
        # When a retry_policy is set, use per-status-code retry limits
        if self._retry_policy is not None:
            policy_max = self._retry_policy.get_retries_for_status(status_code)
            if policy_max <= 0:
                return False
            return attempt < policy_max
        if attempt >= max_retries:
            return False
        return status_code in RETRYABLE_STATUS_CODES

    def _calculate_delay(
        self, attempt: int, response_headers: dict[str, str] | None = None
    ) -> float:
        rc = self._retry_config

        # Check Retry-After header
        if rc.respect_retry_after and response_headers:
            retry_after = response_headers.get("retry-after") or response_headers.get(
                "Retry-After"
            )
            if retry_after is not None:
                try:
                    return min(float(retry_after), rc.backoff_max)
                except (ValueError, TypeError):
                    pass

        # Exponential backoff with jitter
        delay = rc.backoff_factor * (2**attempt)
        jitter = delay * rc.backoff_jitter
        delay += random.uniform(-jitter, jitter)
        return min(delay, rc.backoff_max)

    def _retry_loop_bound(self, max_retries: int) -> int:
        """How many retries the loop allows: the highest per-type limit under a RetryPolicy."""
        policy = self._retry_policy
        if policy is None:
            return max_retries
        return max(
            policy.get_retries_for_timeout(),
            policy.get_retries_for_connection_error(),
            policy.RateLimitErrorRetries,
            policy.InternalServerErrorRetries,
            policy.BadGatewayRetries,
            policy.ServiceUnavailableRetries,
            policy.GatewayTimeoutRetries,
        )

    def _retry_delay(
        self,
        options: RequestOptions,
        exc: APIStatusError | APIConnectionError,
        attempt: int,
        max_retries: int,
    ) -> float | None:
        """Decide one failed attempt: the delay before the next one, or ``None`` to give up.

        Fires ``on_retry`` (with the delay) or ``on_error`` before returning.
        """
        delay: float | None = None
        status_error = exc if isinstance(exc, APIStatusError) else getattr(exc, "_status_error", None)
        if status_error is not None:
            # Classify before status retry: unknown codes and terminal refusals never replay.
            from fi.gateway._retry_policy import (
                classify_refusal, no_code_outcome_unknown, positive_retry_after,
            )
            from fi.gateway._exceptions import _error_metadata

            resp_headers = getattr(status_error.response, "headers", None)
            _, retry = classify_refusal(status_error.status_code, status_error.code, _error_metadata(status_error.body))
            if no_code_outcome_unknown(status_error.status_code, status_error.code, status_error.gateway_evidence):
                retry = False
            if status_error.code is None and status_error.dispatched is True:
                retry = False
            if retry is True and status_error.status_code == 402 and attempt >= 1:
                # Gateway contract: an in-flight credit refusal is retried once, never more.
                retry = False
            status = 429 if retry is True and status_error.status_code in (402, 409) else status_error.status_code
            if retry is not False and self._should_retry(status, attempt, max_retries):
                after = positive_retry_after(resp_headers)
                if retry is True:
                    delay = after  # Missing/invalid header is not permission for backoff.
                elif status_error.code is not None and after is not None:
                    # Contract Retry-After is a minimum, not capped by backoff_max.
                    delay = after
                else:
                    delay = self._calculate_delay(attempt, resp_headers if status_error.code is None else None)
        elif exc._retryable:
            policy = self._retry_policy
            if isinstance(exc, APITimeoutError):
                effective_max = (
                    policy.get_retries_for_timeout()
                    if policy is not None
                    else max_retries
                )
            else:
                effective_max = (
                    policy.get_retries_for_connection_error()
                    if policy is not None
                    else max_retries
                )
            if attempt < effective_max:
                delay = self._calculate_delay(attempt)
        if delay is None:
            self._dispatch_callback("on_error", options, exc)
        else:
            self._dispatch_callback("on_retry", options, exc, attempt + 1, delay)
        return delay

    def _check_status(self, response: httpx.Response) -> None:
        """Raise for a 246 guardrail warning or any status of 400 and above."""
        if response.status_code == 246:
            self._process_guardrail_warning(response)
        if response.status_code >= 400:
            self._process_error(response)

    def _process_response_body(
        self, response: httpx.Response, response_cls: type[T]
    ) -> T:
        """Parse response JSON into a Pydantic model and attach AgentCCMetadata."""
        from fi.gateway.types.agentcc_metadata import AgentCCMetadata

        from fi.gateway._gateway_evidence import capture_gateway_evidence
        from fi.gateway._transport._response import body_decode_error

        failure = None
        try:
            body = response.json()
        except ValueError as exc:
            failure = body_decode_error(exc, capture_gateway_evidence(response))
        if failure is not None:
            # Raise outside the handler so no credential-bearing cause/context escapes.
            raise failure

        # Plain dict/list responses (control-plane resources) — return as-is
        if response_cls is dict or response_cls is list:
            return body  # type: ignore[return-value]

        result = response_cls.model_validate(body)  # type: ignore[attr-defined]

        # Attach AgentCCMetadata
        metadata = AgentCCMetadata.from_headers(
            response.headers, http_response=response
        )
        object.__setattr__(result, "agentcc", metadata)
        self._record_cost(metadata.cost)

        return result

    def _record_cost(self, cost: float | None) -> None:
        """Count a response's ``x-agentcc-cost`` into the client's ``current_cost``."""
        if cost is not None and self._on_cost is not None:
            self._on_cost(cost)

    def _record_header_cost(self, response: httpx.Response) -> None:
        """The cost in a response's headers, for responses with no parsed body (a
        stream, raw audio bytes)."""
        from fi.gateway.types.agentcc_metadata import _float_or_none

        self._record_cost(_float_or_none(response.headers.get(HEADER_RESPONSE_COST)))

    def _process_error(self, response: httpx.Response) -> None:
        """Raise the appropriate exception for an error response."""
        from fi.gateway._transport._response import safe_response

        exc = APIStatusError.from_response(safe_response(response))
        raise exc

    def _process_guardrail_warning(self, response: httpx.Response) -> None:
        """Raise a GuardrailWarning with the completion body attached."""
        from fi.gateway._transport._response import safe_response

        exc = APIStatusError.from_response(safe_response(response))
        raise exc
