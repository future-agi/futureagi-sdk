"""Base HTTP client with retry, error mapping, and callback dispatch."""

from __future__ import annotations

import logging
import random
import time
from abc import ABC
from dataclasses import dataclass, field
from typing import Any, TypeVar

import anyio
import httpx

from fi.gateway._constants import (
    DEFAULT_KEEPALIVE_CONNECTIONS,
    DEFAULT_KEEPALIVE_EXPIRY,
    DEFAULT_MAX_CONNECTIONS,
    DEFAULT_MAX_RETRIES,
    HEADER_API_KEY,
    HEADER_CONTENT_TYPE,
    HEADER_SDK_VERSION,
    HEADER_USER_AGENT,
    NOT_GIVEN,
    AGENTCC_PARAM_TO_HEADER,
    RETRYABLE_STATUS_CODES,
    __version__,
)
from fi.gateway._exceptions import APIConnectionError, APIStatusError, APITimeoutError
from fi.gateway._utils import parse_timeout, serialize_agentcc_param

logger = logging.getLogger("agentcc")

T = TypeVar("T")


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
    """Internal request descriptor built by resource methods."""

    method: str
    url: str
    body: dict[str, Any] | None = None
    headers: dict[str, str] = field(default_factory=dict)
    timeout: httpx.Timeout | None = None
    max_retries: int | None = None


class BaseClient(ABC):
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
    _config: Any  # GatewayConfig | None — typed in Step 10
    _callbacks: list[Any]
    _retry_policy: Any  # RetryPolicy | None

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://gateway.futureagi.com",
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
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = parse_timeout(timeout)
        self._max_retries = max_retries
        self._retry_config = retry_config or RetryConfig(max_retries=max_retries)
        self._default_headers = default_headers or {}
        self._default_query = default_query or {}
        self._session_id = session_id
        self._metadata = metadata
        self._config = config
        self._callbacks = callbacks or []
        self._custom_http_client = http_client
        self._retry_policy = retry_policy

    def _build_headers(self, options: RequestOptions, agentcc_params: dict[str, Any] | None = None) -> dict[str, str]:
        """Build the full header dict using the 7-level priority merge."""
        headers: dict[str, str] = {}

        # 1. SDK auto-headers
        headers[HEADER_USER_AGENT] = f"agentcc-python/{__version__}"
        headers[HEADER_CONTENT_TYPE] = "application/json"
        headers[HEADER_SDK_VERSION] = __version__

        # 2. Auth
        headers[HEADER_API_KEY] = f"Bearer {self._api_key}"

        # 3. Client-level default_headers
        headers.update(self._default_headers)

        # 4. Client-level defaults (session_id, metadata)
        if self._session_id is not None:
            headers[AGENTCC_PARAM_TO_HEADER["session_id"]] = self._session_id
        if self._metadata is not None:
            headers[AGENTCC_PARAM_TO_HEADER["request_metadata"]] = serialize_agentcc_param(
                "request_metadata", self._metadata
            )

        # 5. Config headers (GatewayConfig.to_headers() — Step 10)
        if self._config is not None and hasattr(self._config, "to_headers"):
            headers.update(self._config.to_headers())

        # 6. Per-request AgentCC params
        if agentcc_params:
            for key, value in agentcc_params.items():
                if value is NOT_GIVEN or value is None:
                    continue
                header_name = AGENTCC_PARAM_TO_HEADER.get(key)
                if header_name:
                    headers[header_name] = serialize_agentcc_param(key, value)

        # 7. Per-request extra_headers (from options)
        headers.update(options.headers)

        return headers

    def _build_url(self, path: str) -> str:
        """Join base_url and path, handling slashes correctly."""
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return self._base_url + "/" + path.lstrip("/")

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

    def _calculate_delay(self, attempt: int, response_headers: dict[str, str] | None = None) -> float:
        rc = self._retry_config

        # Check Retry-After header
        if rc.respect_retry_after and response_headers:
            retry_after = response_headers.get("retry-after") or response_headers.get("Retry-After")
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

    def _dispatch_callback(self, method_name: str, *args: Any) -> None:
        """Call a method on all registered callbacks, swallowing exceptions."""
        for callback in self._callbacks:
            fn = getattr(callback, method_name, None)
            if fn is not None:
                try:
                    fn(*args)
                except Exception:
                    logger.debug(
                        "Callback %s.%s raised an exception", type(callback).__name__, method_name, exc_info=True
                    )

    def _process_response_body(self, response: httpx.Response, response_cls: type[T]) -> T:
        """Parse response JSON into a Pydantic model and attach AgentCCMetadata."""
        from fi.gateway.types.agentcc_metadata import AgentCCMetadata

        body = response.json()

        # Plain dict/list responses (control-plane resources) — return as-is
        if response_cls is dict or response_cls is list:
            return body  # type: ignore[return-value]

        result = response_cls.model_validate(body)  # type: ignore[union-attr]

        # Attach AgentCCMetadata
        metadata = AgentCCMetadata.from_headers(dict(response.headers), http_response=response)
        object.__setattr__(result, "agentcc", metadata)

        return result

    def _process_error(self, response: httpx.Response) -> None:
        """Raise the appropriate exception for an error response."""
        exc = APIStatusError.from_response(response)
        raise exc

    def _process_guardrail_warning(self, response: httpx.Response) -> None:
        """Raise a GuardrailWarning with the completion body attached."""
        exc = APIStatusError.from_response(response)
        raise exc


class SyncBaseClient(BaseClient):
    """Synchronous HTTP transport with retry."""

    _client: httpx.Client | None
    _owns_client: bool

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._client = None
        self._owns_client = True
        if self._custom_http_client is not None:
            self._client = self._custom_http_client
            self._owns_client = False

    def _ensure_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=self._timeout,
                limits=httpx.Limits(
                    max_connections=DEFAULT_MAX_CONNECTIONS,
                    max_keepalive_connections=DEFAULT_KEEPALIVE_CONNECTIONS,
                    keepalive_expiry=DEFAULT_KEEPALIVE_EXPIRY,
                ),
            )
            self._owns_client = True
        return self._client

    def _request(
        self,
        options: RequestOptions,
        response_cls: type[T],
        agentcc_params: dict[str, Any] | None = None,
    ) -> T:
        """Execute a single HTTP request and return the parsed response."""
        url = self._build_url(options.url)
        headers = self._build_headers(options, agentcc_params)
        timeout = options.timeout or self._timeout
        client = self._ensure_client()

        try:
            response = client.request(
                method=options.method,
                url=url,
                json=options.body,
                headers=headers,
                timeout=timeout,
            )
        except httpx.TimeoutException as e:
            raise APITimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise APIConnectionError(f"Connection error: {e}") from e

        # 246 is a guardrail warning — request succeeded but with a warning
        if response.status_code == 246:
            self._process_guardrail_warning(response)

        if response.status_code >= 400:
            self._process_error(response)

        return self._process_response_body(response, response_cls)

    def _request_with_retry(
        self,
        options: RequestOptions,
        response_cls: type[T],
        agentcc_params: dict[str, Any] | None = None,
    ) -> T:
        """Execute a request with retry logic."""
        max_retries = options.max_retries if options.max_retries is not None else self._max_retries

        # When retry_policy is set, use the highest per-type limit as the loop bound
        if self._retry_policy is not None:
            loop_max = max(
                self._retry_policy.get_retries_for_timeout(),
                self._retry_policy.get_retries_for_connection_error(),
                self._retry_policy.RateLimitErrorRetries,
                self._retry_policy.InternalServerErrorRetries,
                self._retry_policy.BadGatewayRetries,
                self._retry_policy.ServiceUnavailableRetries,
                self._retry_policy.GatewayTimeoutRetries,
            )
        else:
            loop_max = max_retries

        last_exc: Exception | None = None

        self._dispatch_callback("on_request_start", options)

        for attempt in range(loop_max + 1):
            try:
                result = self._request(options, response_cls, agentcc_params)
                self._dispatch_callback("on_request_end", options, result)
                return result
            except APIStatusError as exc:
                last_exc = exc
                if self._should_retry(exc.status_code, attempt, max_retries):
                    resp_headers = (
                        dict(exc.response.headers) if exc.response and hasattr(exc.response, "headers") else None
                    )
                    delay = self._calculate_delay(attempt, resp_headers)
                    self._dispatch_callback("on_retry", options, exc, attempt + 1, delay)
                    time.sleep(delay)
                    continue
                self._dispatch_callback("on_error", options, exc)
                raise
            except APITimeoutError as exc:
                last_exc = exc
                effective_max = (
                    self._retry_policy.get_retries_for_timeout() if self._retry_policy is not None else max_retries
                )
                if attempt < effective_max:
                    delay = self._calculate_delay(attempt)
                    self._dispatch_callback("on_retry", options, exc, attempt + 1, delay)
                    time.sleep(delay)
                    continue
                self._dispatch_callback("on_error", options, exc)
                raise
            except APIConnectionError as exc:
                last_exc = exc
                effective_max = (
                    self._retry_policy.get_retries_for_connection_error()
                    if self._retry_policy is not None
                    else max_retries
                )
                if attempt < effective_max:
                    delay = self._calculate_delay(attempt)
                    self._dispatch_callback("on_retry", options, exc, attempt + 1, delay)
                    time.sleep(delay)
                    continue
                self._dispatch_callback("on_error", options, exc)
                raise

        # Should not reach here, but just in case
        if last_exc is not None:
            self._dispatch_callback("on_error", options, last_exc)
            raise last_exc
        raise RuntimeError("Retry loop exited unexpectedly")  # pragma: no cover

    def _request_raw(
        self,
        options: RequestOptions,
        agentcc_params: dict[str, Any] | None = None,
    ) -> bytes:
        """Execute a single HTTP request and return the raw response bytes."""
        url = self._build_url(options.url)
        headers = self._build_headers(options, agentcc_params)
        timeout = options.timeout or self._timeout
        client = self._ensure_client()

        try:
            response = client.request(
                method=options.method,
                url=url,
                json=options.body,
                headers=headers,
                timeout=timeout,
            )
        except httpx.TimeoutException as e:
            raise APITimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise APIConnectionError(f"Connection error: {e}") from e

        if response.status_code == 246:
            self._process_guardrail_warning(response)

        if response.status_code >= 400:
            self._process_error(response)

        return response.content

    def _request_raw_with_retry(
        self,
        options: RequestOptions,
        agentcc_params: dict[str, Any] | None = None,
    ) -> bytes:
        """Execute a raw-bytes request with retry logic."""
        max_retries = options.max_retries if options.max_retries is not None else self._max_retries

        if self._retry_policy is not None:
            loop_max = max(
                self._retry_policy.get_retries_for_timeout(),
                self._retry_policy.get_retries_for_connection_error(),
                self._retry_policy.RateLimitErrorRetries,
                self._retry_policy.InternalServerErrorRetries,
                self._retry_policy.BadGatewayRetries,
                self._retry_policy.ServiceUnavailableRetries,
                self._retry_policy.GatewayTimeoutRetries,
            )
        else:
            loop_max = max_retries

        last_exc: Exception | None = None

        self._dispatch_callback("on_request_start", options)

        for attempt in range(loop_max + 1):
            try:
                result = self._request_raw(options, agentcc_params)
                self._dispatch_callback("on_request_end", options, result)
                return result
            except APIStatusError as exc:
                last_exc = exc
                if self._should_retry(exc.status_code, attempt, max_retries):
                    resp_headers = (
                        dict(exc.response.headers) if exc.response and hasattr(exc.response, "headers") else None
                    )
                    delay = self._calculate_delay(attempt, resp_headers)
                    self._dispatch_callback("on_retry", options, exc, attempt + 1, delay)
                    time.sleep(delay)
                    continue
                self._dispatch_callback("on_error", options, exc)
                raise
            except APITimeoutError as exc:
                last_exc = exc
                effective_max = (
                    self._retry_policy.get_retries_for_timeout() if self._retry_policy is not None else max_retries
                )
                if attempt < effective_max:
                    delay = self._calculate_delay(attempt)
                    self._dispatch_callback("on_retry", options, exc, attempt + 1, delay)
                    time.sleep(delay)
                    continue
                self._dispatch_callback("on_error", options, exc)
                raise
            except APIConnectionError as exc:
                last_exc = exc
                effective_max = (
                    self._retry_policy.get_retries_for_connection_error()
                    if self._retry_policy is not None
                    else max_retries
                )
                if attempt < effective_max:
                    delay = self._calculate_delay(attempt)
                    self._dispatch_callback("on_retry", options, exc, attempt + 1, delay)
                    time.sleep(delay)
                    continue
                self._dispatch_callback("on_error", options, exc)
                raise

        if last_exc is not None:
            self._dispatch_callback("on_error", options, last_exc)
            raise last_exc
        raise RuntimeError("Retry loop exited unexpectedly")  # pragma: no cover

    def _stream_request(
        self,
        options: RequestOptions,
        agentcc_params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute a streaming request and return the raw response."""
        url = self._build_url(options.url)
        headers = self._build_headers(options, agentcc_params)
        timeout = options.timeout or self._timeout
        client = self._ensure_client()

        try:
            response = client.send(
                client.build_request(
                    method=options.method,
                    url=url,
                    json=options.body,
                    headers=headers,
                    timeout=timeout,
                ),
                stream=True,
            )
        except httpx.TimeoutException as e:
            raise APITimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise APIConnectionError(f"Connection error: {e}") from e

        if response.status_code >= 400:
            response.read()
            self._process_error(response)

        return response

    def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None and self._owns_client:
            self._client.close()
            self._client = None


class AsyncBaseClient(BaseClient):
    """Asynchronous HTTP transport with retry."""

    _client: httpx.AsyncClient | None
    _owns_client: bool

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._client = None
        self._owns_client = True
        if self._custom_http_client is not None:
            self._client = self._custom_http_client
            self._owns_client = False

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                limits=httpx.Limits(
                    max_connections=DEFAULT_MAX_CONNECTIONS,
                    max_keepalive_connections=DEFAULT_KEEPALIVE_CONNECTIONS,
                    keepalive_expiry=DEFAULT_KEEPALIVE_EXPIRY,
                ),
            )
            self._owns_client = True
        return self._client

    async def _request(
        self,
        options: RequestOptions,
        response_cls: type[T],
        agentcc_params: dict[str, Any] | None = None,
    ) -> T:
        url = self._build_url(options.url)
        headers = self._build_headers(options, agentcc_params)
        timeout = options.timeout or self._timeout
        client = self._ensure_client()

        try:
            response = await client.request(
                method=options.method,
                url=url,
                json=options.body,
                headers=headers,
                timeout=timeout,
            )
        except httpx.TimeoutException as e:
            raise APITimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise APIConnectionError(f"Connection error: {e}") from e

        if response.status_code == 246:
            self._process_guardrail_warning(response)

        if response.status_code >= 400:
            self._process_error(response)

        return self._process_response_body(response, response_cls)

    async def _request_with_retry(
        self,
        options: RequestOptions,
        response_cls: type[T],
        agentcc_params: dict[str, Any] | None = None,
    ) -> T:
        max_retries = options.max_retries if options.max_retries is not None else self._max_retries

        # When retry_policy is set, use the highest per-type limit as the loop bound
        if self._retry_policy is not None:
            loop_max = max(
                self._retry_policy.get_retries_for_timeout(),
                self._retry_policy.get_retries_for_connection_error(),
                self._retry_policy.RateLimitErrorRetries,
                self._retry_policy.InternalServerErrorRetries,
                self._retry_policy.BadGatewayRetries,
                self._retry_policy.ServiceUnavailableRetries,
                self._retry_policy.GatewayTimeoutRetries,
            )
        else:
            loop_max = max_retries

        last_exc: Exception | None = None

        self._dispatch_callback("on_request_start", options)

        for attempt in range(loop_max + 1):
            try:
                result = await self._request(options, response_cls, agentcc_params)
                self._dispatch_callback("on_request_end", options, result)
                return result
            except APIStatusError as exc:
                last_exc = exc
                if self._should_retry(exc.status_code, attempt, max_retries):
                    resp_headers = (
                        dict(exc.response.headers) if exc.response and hasattr(exc.response, "headers") else None
                    )
                    delay = self._calculate_delay(attempt, resp_headers)
                    self._dispatch_callback("on_retry", options, exc, attempt + 1, delay)
                    await anyio.sleep(delay)
                    continue
                self._dispatch_callback("on_error", options, exc)
                raise
            except APITimeoutError as exc:
                last_exc = exc
                effective_max = (
                    self._retry_policy.get_retries_for_timeout() if self._retry_policy is not None else max_retries
                )
                if attempt < effective_max:
                    delay = self._calculate_delay(attempt)
                    self._dispatch_callback("on_retry", options, exc, attempt + 1, delay)
                    await anyio.sleep(delay)
                    continue
                self._dispatch_callback("on_error", options, exc)
                raise
            except APIConnectionError as exc:
                last_exc = exc
                effective_max = (
                    self._retry_policy.get_retries_for_connection_error()
                    if self._retry_policy is not None
                    else max_retries
                )
                if attempt < effective_max:
                    delay = self._calculate_delay(attempt)
                    self._dispatch_callback("on_retry", options, exc, attempt + 1, delay)
                    await anyio.sleep(delay)
                    continue
                self._dispatch_callback("on_error", options, exc)
                raise

        if last_exc is not None:
            self._dispatch_callback("on_error", options, last_exc)
            raise last_exc
        raise RuntimeError("Retry loop exited unexpectedly")  # pragma: no cover

    async def _request_raw(
        self,
        options: RequestOptions,
        agentcc_params: dict[str, Any] | None = None,
    ) -> bytes:
        """Execute a single HTTP request and return the raw response bytes."""
        url = self._build_url(options.url)
        headers = self._build_headers(options, agentcc_params)
        timeout = options.timeout or self._timeout
        client = self._ensure_client()

        try:
            response = await client.request(
                method=options.method,
                url=url,
                json=options.body,
                headers=headers,
                timeout=timeout,
            )
        except httpx.TimeoutException as e:
            raise APITimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise APIConnectionError(f"Connection error: {e}") from e

        if response.status_code == 246:
            self._process_guardrail_warning(response)

        if response.status_code >= 400:
            self._process_error(response)

        return response.content

    async def _request_raw_with_retry(
        self,
        options: RequestOptions,
        agentcc_params: dict[str, Any] | None = None,
    ) -> bytes:
        """Execute a raw-bytes request with retry logic."""
        max_retries = options.max_retries if options.max_retries is not None else self._max_retries

        if self._retry_policy is not None:
            loop_max = max(
                self._retry_policy.get_retries_for_timeout(),
                self._retry_policy.get_retries_for_connection_error(),
                self._retry_policy.RateLimitErrorRetries,
                self._retry_policy.InternalServerErrorRetries,
                self._retry_policy.BadGatewayRetries,
                self._retry_policy.ServiceUnavailableRetries,
                self._retry_policy.GatewayTimeoutRetries,
            )
        else:
            loop_max = max_retries

        last_exc: Exception | None = None

        self._dispatch_callback("on_request_start", options)

        for attempt in range(loop_max + 1):
            try:
                result = await self._request_raw(options, agentcc_params)
                self._dispatch_callback("on_request_end", options, result)
                return result
            except APIStatusError as exc:
                last_exc = exc
                if self._should_retry(exc.status_code, attempt, max_retries):
                    resp_headers = (
                        dict(exc.response.headers) if exc.response and hasattr(exc.response, "headers") else None
                    )
                    delay = self._calculate_delay(attempt, resp_headers)
                    self._dispatch_callback("on_retry", options, exc, attempt + 1, delay)
                    await anyio.sleep(delay)
                    continue
                self._dispatch_callback("on_error", options, exc)
                raise
            except APITimeoutError as exc:
                last_exc = exc
                effective_max = (
                    self._retry_policy.get_retries_for_timeout() if self._retry_policy is not None else max_retries
                )
                if attempt < effective_max:
                    delay = self._calculate_delay(attempt)
                    self._dispatch_callback("on_retry", options, exc, attempt + 1, delay)
                    await anyio.sleep(delay)
                    continue
                self._dispatch_callback("on_error", options, exc)
                raise
            except APIConnectionError as exc:
                last_exc = exc
                effective_max = (
                    self._retry_policy.get_retries_for_connection_error()
                    if self._retry_policy is not None
                    else max_retries
                )
                if attempt < effective_max:
                    delay = self._calculate_delay(attempt)
                    self._dispatch_callback("on_retry", options, exc, attempt + 1, delay)
                    await anyio.sleep(delay)
                    continue
                self._dispatch_callback("on_error", options, exc)
                raise

        if last_exc is not None:
            self._dispatch_callback("on_error", options, last_exc)
            raise last_exc
        raise RuntimeError("Retry loop exited unexpectedly")  # pragma: no cover

    async def _stream_request(
        self,
        options: RequestOptions,
        agentcc_params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        url = self._build_url(options.url)
        headers = self._build_headers(options, agentcc_params)
        timeout = options.timeout or self._timeout
        client = self._ensure_client()

        try:
            response = await client.send(
                client.build_request(
                    method=options.method,
                    url=url,
                    json=options.body,
                    headers=headers,
                    timeout=timeout,
                ),
                stream=True,
            )
        except httpx.TimeoutException as e:
            raise APITimeoutError(f"Request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise APIConnectionError(f"Connection error: {e}") from e

        if response.status_code >= 400:
            await response.aread()
            self._process_error(response)

        return response

    async def aclose(self) -> None:
        """Close the underlying async HTTP client."""
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None
