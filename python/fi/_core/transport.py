"""The platform's HTTP clients: one per mode, built from the shared transport.

``RetryingTransport`` / ``AsyncRetryingTransport`` (``fi._http``) wrap :class:`_AttemptRecorder`,
which wraps the real httpx transport and logs each attempt's outcome (a status, or the transport
error) into ``request.extensions["fi.attempts"]``. The executor reads that log to tell whether an
earlier attempt may have applied, without any change to the shared transport. Clients are built with
``follow_redirects=False`` and ``trust_env=True``. Because a ``transport=`` is passed, httpx reads
only the SSL settings from the environment (``SSL_CERT_FILE``, ``SSL_CERT_DIR``); it does **not**
apply ``HTTPS_PROXY`` / ``ALL_PROXY``, the same as the shared core clients (a known gap for both).

:class:`PlatformShared` is what a client and its ``with_options`` copies share: the lazily
resolved origin, the operation table, the connection pool and the client's extra headers
(``FI_EXTRA_HEADERS`` / ``extra_headers=``, a :class:`HeaderSource`). :class:`Settings` is what a
copy may change.
"""

from __future__ import annotations

import asyncio
import platform as _platform
import sys
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Protocol, Union

import httpx

from fi._core.origins import PlatformOrigin
from fi._core.policy import OperationSpec, lookup
from fi._http import DEFAULT_TIMEOUT, AsyncRetryingTransport, RetryingTransport
from fi.errors import PlatformNotConfiguredError

ATTEMPTS_EXTENSION = "fi.attempts"
IN_PROGRESS_BUDGET_S = 120.0
DEFAULT_STREAM_IDLE_S = 45.0
MAX_ERROR_BODY = 64 * 1024
TimeoutArg = Union[float, httpx.Timeout, None]


def user_agent() -> str:
    from fi import __version__

    return f"futureagi-python/{__version__} (python/{_platform.python_version()}; {sys.platform})"


def as_timeout(value: TimeoutArg, default: httpx.Timeout = DEFAULT_TIMEOUT) -> httpx.Timeout:
    if value is None:
        return default
    if isinstance(value, httpx.Timeout):
        return value
    return httpx.Timeout(float(value), connect=min(10.0, float(value)))


class _AttemptRecorder(httpx.BaseTransport, httpx.AsyncBaseTransport):
    """Sits under ``RetryingTransport`` and logs every attempt's outcome into the request."""

    def __init__(self, inner: Any = None, inner_async: Any = None) -> None:
        self._inner = inner
        self._inner_async = inner_async
        self._lock = threading.Lock()

    def _sync(self) -> httpx.BaseTransport:
        with self._lock:
            if self._inner is None:
                self._inner = httpx.HTTPTransport(trust_env=True)
            return self._inner

    def _async(self) -> httpx.AsyncBaseTransport:
        with self._lock:
            if self._inner_async is None:
                self._inner_async = (
                    self._inner
                    if isinstance(self._inner, httpx.AsyncBaseTransport)
                    else httpx.AsyncHTTPTransport(trust_env=True)
                )
            return self._inner_async

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        log = request.extensions.get(ATTEMPTS_EXTENSION)
        try:
            response = self._sync().handle_request(request)
        except httpx.TransportError as exc:
            _log(log, exc)
            raise
        _log(log, response.status_code)
        return response

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        log = request.extensions.get(ATTEMPTS_EXTENSION)
        try:
            response = await self._async().handle_async_request(request)
        except httpx.TransportError as exc:
            _log(log, exc)
            raise
        _log(log, response.status_code)
        return response

    def close(self) -> None:
        if self._inner is not None and hasattr(self._inner, "close"):
            self._inner.close()

    async def aclose(self) -> None:
        if self._inner_async is not None and hasattr(self._inner_async, "aclose"):
            await self._inner_async.aclose()


def _log(log: Optional[list[Any]], outcome: Any) -> None:
    if log is not None:
        log.append(outcome)


def possibly_applied(outcome: Any) -> bool:
    """A 5xx, or an error after the request left (anything but a refused/unresolved connect)."""
    if isinstance(outcome, int):
        return outcome >= 500
    return not isinstance(outcome, (httpx.ConnectError, httpx.ConnectTimeout))


@dataclass(frozen=True)
class Settings:
    """Per-client defaults a ``with_options`` copy may change."""

    timeout: httpx.Timeout = field(default_factory=lambda: DEFAULT_TIMEOUT)
    retries: Optional[int] = None  # None: the transport's own count (the client's ``retries=``)
    stream_idle_timeout: float = DEFAULT_STREAM_IDLE_S


class HeaderSource(Protocol):
    """The shape of the client's ``fi._extra_headers.ExtraHeaders`` (not imported here: ``fi._core``
    imports only the shared base): the headers a request to ``url`` carries, read when it is called,
    ``{}`` for a URL that is not under the client's ``base_url``; raises on a malformed setting."""

    def for_url(self, url: Any) -> Mapping[str, str]:
        ...


class PlatformShared:
    """What a client and its ``with_options`` copies share: the origin, the table, the pool and the
    client's extra headers."""

    def __init__(
        self,
        resolve_origin: Callable[[], PlatformOrigin],
        *,
        retries: int = 3,
        table: Optional[Mapping[str, OperationSpec]] = None,
        supplemental_table: Optional[Mapping[str, OperationSpec]] = None,
        transport: Any = None,
        sleep: Optional[Callable[[float], Any]] = None,
        backoff_base_s: float = 0.5,
        extra_headers: Optional[HeaderSource] = None,
        error_scrubber: Optional[Callable[[Any, list[str]], Any]] = None,
    ) -> None:
        self._resolve_origin = resolve_origin
        self._origin: Optional[PlatformOrigin] = None
        self._lock = threading.Lock()
        self.extra_headers = extra_headers
        # Namespace policy over decoded errors, before any value or field-name redaction.
        self.error_scrubber = error_scrubber
        self.table = table
        # Independently pinned namespace operations preserve the base table's identity.
        self.supplemental_table = supplemental_table or {}
        self.retries = retries
        self.sleep = sleep
        self.backoff_base_s = backoff_base_s
        self._recorder = _AttemptRecorder(transport)
        self._http: Optional[httpx.Client] = None
        self._ahttp: Optional[httpx.AsyncClient] = None

    def origin(self) -> PlatformOrigin:
        with self._lock:
            if self._origin is None:
                self._origin = self._resolve_origin()
            return self._origin

    def operation(self, name: str) -> OperationSpec:
        if self.table is None:
            try:
                from fi.generated.platform.policy import OPERATIONS  # type: ignore[import-not-found]  # isort: skip
            except ModuleNotFoundError:
                raise PlatformNotConfiguredError(
                    "this build of futureagi has no platform operation table (fi.generated.platform)",
                    code="no_contract",
                ) from None
            self.table = OPERATIONS
        if name in self.table:
            certified = lookup(self.table, name)
            if name in self.supplemental_table and self.supplemental_table[name] != certified:
                raise ValueError(f"Divergent supplemental operation: {name}")
            return certified
        return lookup(self.supplemental_table, name)

    def http(self) -> httpx.Client:
        with self._lock:
            if self._http is None:
                kw = {} if self.sleep is None else {"sleep": self.sleep}
                transport = RetryingTransport(
                    self._recorder, retries=self.retries, backoff_base_s=self.backoff_base_s, **kw
                )
                self._http = httpx.Client(
                    transport=transport, timeout=DEFAULT_TIMEOUT, follow_redirects=False, trust_env=True
                )
            return self._http

    def ahttp(self) -> httpx.AsyncClient:
        with self._lock:
            if self._ahttp is None:
                kw = {} if self.sleep is None else {"sleep": _async_sleep(self.sleep)}
                transport = AsyncRetryingTransport(
                    self._recorder, retries=self.retries, backoff_base_s=self.backoff_base_s, **kw
                )
                self._ahttp = httpx.AsyncClient(
                    transport=transport, timeout=DEFAULT_TIMEOUT, follow_redirects=False, trust_env=True
                )
            return self._ahttp

    def close(self) -> None:
        if self._http is not None:
            self._http.close()

    async def aclose(self) -> None:
        if self._ahttp is not None:
            await self._ahttp.aclose()


def _async_sleep(sleep: Callable[[float], Any]) -> Callable[[float], Any]:
    async def go(seconds: float) -> None:
        result = sleep(seconds)
        if asyncio.iscoroutine(result):
            await result

    return go


class _NoClose(httpx.BaseTransport, httpx.AsyncBaseTransport):
    """A view of a shared transport whose ``close`` is a no-op: a ``with_options`` copy uses the
    original's connection pool and must not close it."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return self._inner.handle_request(request)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return await self._inner.handle_async_request(request)

    def close(self) -> None:
        pass

    async def aclose(self) -> None:
        pass


def shared_inner(transport: Any) -> tuple[Any, Any]:
    """The pooled transports under a core client's ``ClientRetryingTransport`` (built now if they
    were not yet), as non-closing views for a ``with_options`` copy."""
    sync_inner = transport._sync_transport()._wrapped
    async_inner = transport._async_transport()._wrapped
    return _NoClose(sync_inner), _NoClose(async_inner)
