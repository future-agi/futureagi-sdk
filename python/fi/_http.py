"""HTTP defaults for the generated-client wrappers.

- a default ``httpx.Timeout(30, connect=10)``;
- a retrying transport. With no retry class (below) the rule is:

  * 429 (the server refused before doing anything): every method;
  * 502, 503 and 504: idempotent methods only (GET, HEAD, OPTIONS, PUT, DELETE). A 5xx on a POST
    or PATCH may mean the request ran, so it is never repeated: a create that documents "one
    attempt" (``datasets.versions.create``, ``experiment_runs.create``) makes one attempt;
  * a pre-send error (``httpx.ConnectError``, ``httpx.ConnectTimeout``: nothing left the
    machine): every method;
  * any other network error (``ReadError``, ``WriteError``, ``RemoteProtocolError``: the request
    may have been sent): idempotent methods only;
  * a timeout after connecting (``ReadTimeout``, ``WriteTimeout``, ``PoolTimeout``): never.

  Backoff is 0.5-1-2-4 s (capped at 30 s) and ``Retry-After`` is honoured;
- lazy keys: :class:`LazyKeyAuth` resolves credentials on the first request, so constructing a
  client never raises for missing keys;
- :class:`ClientRetryingTransport` serves both httpx clients of a generated client (its
  ``httpx_args`` reach the sync and the async constructor alike);
- a per-request retry class: ``request.extensions["fi.retry"]`` is one of
  :data:`RETRY_CLASSES` (or ``{"class": ..., "retries": N}``; ``{"retries": N}`` alone keeps the
  default rule and changes only the count):

  * ``keyed`` (a durable idempotency key) and ``http-idempotent`` (the operation is idempotent):
    429, 502, 503 and 504, and any network error, on any method;
  * ``keyed-not-durable`` (a restarted server forgets the key) and ``unsafe`` (a 5xx may mean the
    request ran): 429 and pre-send errors only, never a 5xx.

  Timeouts after connecting are never retried, in any class. The 409 "key in progress" wait and
  the idempotency key itself belong to the caller (the platform's idempotency layer), not to this
  transport. TypeScript's ``resilientFetch`` (``transport.ts``) follows the same table.

Imports nothing from ``fi.utils`` or ``fi.api``, which other distributions also ship.
"""

from __future__ import annotations

import asyncio
import email.utils
import math
import threading
import time
from typing import Any, Callable, Generator, Mapping, Optional

import httpx

from fi._credentials import Credentials
from fi._core.http_security import check_http_security
from fi._extra_headers import ExtraHeaders

DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
RETRY_ALWAYS = frozenset({429})  # every method: the server refused before doing anything
RETRY_IDEMPOTENT = frozenset({502, 503, 504})  # idempotent methods only: the request may have run
IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})
MAX_SLEEP_S = 30.0


def retry_after_seconds(response: httpx.Response) -> Optional[float]:
    value = response.headers.get("Retry-After")
    if not value:
        return None
    try:
        seconds = float(value)
    except ValueError:
        pass
    else:
        return max(0.0, seconds) if math.isfinite(seconds) else None
    try:
        when = email.utils.parsedate_to_datetime(value)
        return max(0.0, when.timestamp() - time.time())
    except (TypeError, ValueError, OverflowError):
        return None


RETRY_EXTENSION = "fi.retry"
RETRY_CLASSES = frozenset({"keyed", "keyed-not-durable", "http-idempotent", "unsafe"})
_RETRY_5XX = frozenset({502, 503, 504})


def request_retry_policy(request: httpx.Request) -> tuple[Optional[str], Optional[int]]:
    """``(retry_class, retries)`` from ``request.extensions["fi.retry"]``; ``(None, None)`` when unset.

    Raises ``ValueError`` for an unknown class: a typo must not silently fall back to retrying.
    """
    value: Any = request.extensions.get(RETRY_EXTENSION)
    if value is None:
        return None, None
    retries: Optional[int] = None
    if isinstance(value, str):
        retry_class: Optional[str] = value
    elif isinstance(value, Mapping):
        retry_class = value.get("class")
        retries = value.get("retries")
        if retries is not None and (not isinstance(retries, int) or retries < 0):
            raise ValueError(f"{RETRY_EXTENSION} retries must be a non-negative int, not {retries!r}")
    else:
        raise ValueError(f"{RETRY_EXTENSION} must be a retry class or a mapping, not {type(value).__name__}")
    if retry_class is not None and retry_class not in RETRY_CLASSES:
        raise ValueError(f"unknown {RETRY_EXTENSION} class {retry_class!r}; one of {sorted(RETRY_CLASSES)}")
    return retry_class, retries


def should_retry(method: str, status: int, retry_class: Optional[str] = None) -> bool:
    if retry_class is None:
        return status in RETRY_ALWAYS or (status in RETRY_IDEMPOTENT and method.upper() in IDEMPOTENT_METHODS)
    if retry_class in ("keyed", "http-idempotent"):
        return status == 429 or status in _RETRY_5XX
    return status == 429  # keyed-not-durable, unsafe: never a 5xx


PRE_SEND_ERRORS = (httpx.ConnectError, httpx.ConnectTimeout)  # nothing left the machine
_SENT_NETWORK_ERRORS = (httpx.NetworkError, httpx.RemoteProtocolError)  # the request may have been sent


def should_retry_error(method: str, exc: BaseException, retry_class: Optional[str] = None) -> bool:
    """Whether a transport error (no HTTP response) is retried; the same table as TypeScript's
    ``shouldRetryNetworkError``."""
    if isinstance(exc, PRE_SEND_ERRORS):
        return True  # every method, every class
    if not isinstance(exc, _SENT_NETWORK_ERRORS):
        return False  # a timeout after connecting, or a local protocol error: never
    if retry_class in ("keyed", "http-idempotent"):
        return True
    if retry_class is None:
        return method.upper() in IDEMPOTENT_METHODS
    return False  # keyed-not-durable, unsafe


def backoff_s(attempt: int, response: Optional[httpx.Response], base: float) -> float:
    hinted = retry_after_seconds(response) if response is not None else None
    # A server hint is a minimum wait, not locally generated exponential backoff.
    return hinted if hinted is not None else min(base * (2**attempt), MAX_SLEEP_S)


class RetryingTransport(httpx.BaseTransport):
    def __init__(
        self,
        wrapped: Optional[httpx.BaseTransport] = None,
        *,
        retries: int = 3,
        backoff_base_s: float = 0.5,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._wrapped = wrapped or httpx.HTTPTransport()
        self.retries = retries
        self.backoff_base_s = backoff_base_s
        self._sleep = sleep

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        retry_class, override = request_retry_policy(request)
        retries = self.retries if override is None else override
        request.read()  # buffered body, so a retry resends the same bytes
        attempt = 0
        while True:
            try:
                response = self._wrapped.handle_request(request)
            except httpx.TransportError as exc:
                if attempt >= retries or not should_retry_error(request.method, exc, retry_class):
                    raise
                self._sleep(backoff_s(attempt, None, self.backoff_base_s))
                attempt += 1
                continue
            if attempt >= retries or not should_retry(request.method, response.status_code, retry_class):
                return response
            delay = backoff_s(attempt, response, self.backoff_base_s)
            response.close()
            self._sleep(delay)
            attempt += 1

    def close(self) -> None:
        self._wrapped.close()


class AsyncRetryingTransport(httpx.AsyncBaseTransport):
    def __init__(
        self,
        wrapped: Optional[httpx.AsyncBaseTransport] = None,
        *,
        retries: int = 3,
        backoff_base_s: float = 0.5,
        sleep: Optional[Callable[[float], "asyncio.Future[None] | object"]] = None,
    ) -> None:
        self._wrapped = wrapped or httpx.AsyncHTTPTransport()
        self.retries = retries
        self.backoff_base_s = backoff_base_s
        self._sleep = sleep or asyncio.sleep

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        retry_class, override = request_retry_policy(request)
        retries = self.retries if override is None else override
        await request.aread()
        attempt = 0
        while True:
            try:
                response = await self._wrapped.handle_async_request(request)
            except httpx.TransportError as exc:
                if attempt >= retries or not should_retry_error(request.method, exc, retry_class):
                    raise
                await self._sleep(backoff_s(attempt, None, self.backoff_base_s))  # type: ignore[misc]
                attempt += 1
                continue
            if attempt >= retries or not should_retry(request.method, response.status_code, retry_class):
                return response
            delay = backoff_s(attempt, response, self.backoff_base_s)
            await response.aclose()
            await self._sleep(delay)  # type: ignore[misc]
            attempt += 1

    async def aclose(self) -> None:
        await self._wrapped.aclose()


class ClientRetryingTransport(httpx.BaseTransport, httpx.AsyncBaseTransport):
    """One retrying transport for both httpx clients of a generated client.

    The generated client passes ``httpx_args`` to the ``httpx.Client`` *and* the ``httpx.AsyncClient``
    constructor, so a sync-only transport there breaks ``get_async_httpx_client()`` (and an
    async-only one breaks the sync client). Each side builds its real transport on first use.
    """

    def __init__(
        self,
        *,
        retries: int = 3,
        backoff_base_s: float = 0.5,
        wrapped: Optional[httpx.BaseTransport] = None,
        wrapped_async: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        self.retries = retries
        self.backoff_base_s = backoff_base_s
        self._wrapped = wrapped
        self._wrapped_async = wrapped_async
        self._sync: Optional[RetryingTransport] = None
        self._async: Optional[AsyncRetryingTransport] = None
        self._lock = threading.Lock()

    def _sync_transport(self) -> RetryingTransport:
        with self._lock:
            if self._sync is None:
                self._sync = RetryingTransport(self._wrapped, retries=self.retries, backoff_base_s=self.backoff_base_s)
            return self._sync

    def _async_transport(self) -> AsyncRetryingTransport:
        with self._lock:
            if self._async is None:
                self._async = AsyncRetryingTransport(
                    self._wrapped_async, retries=self.retries, backoff_base_s=self.backoff_base_s
                )
            return self._async

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return self._sync_transport().handle_request(request)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return await self._async_transport().handle_async_request(request)

    def close(self) -> None:
        if self._sync is not None:
            self._sync.close()

    async def aclose(self) -> None:
        if self._async is not None:
            await self._async.aclose()


class LazyKeyAuth(httpx.Auth):
    """Adds ``X-Api-Key`` / ``X-Secret-Key`` on each request, resolving them on the first one.

    With ``extra`` (``fi._extra_headers.ExtraHeaders``), a request to a URL under the client's base
    URL also carries ``FI_EXTRA_HEADERS`` / ``extra_headers=``, read when the request is sent; any
    other URL gets none of them. A header already on the request wins."""

    def __init__(self, resolve: Callable[[], Credentials], *, extra: Optional[ExtraHeaders] = None) -> None:
        self._resolve = resolve
        self._creds: Optional[Credentials] = None
        self._lock = threading.Lock()
        self.extra = extra

    @property
    def credentials(self) -> Credentials:
        with self._lock:
            if self._creds is None:
                self._creds = self._resolve().require()
            return self._creds

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        if self.extra is not None:
            self.extra.apply(request.headers, request.url)
        creds = self.credentials
        check_http_security(request.url, "keys")
        request.headers.setdefault("X-Api-Key", str(creds.api_key))
        request.headers.setdefault("X-Secret-Key", str(creds.secret_key))
        yield request
