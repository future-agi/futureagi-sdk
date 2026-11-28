"""The platform's HTTP clients: one per mode, built from the shared transport.

``RetryingTransport`` / ``AsyncRetryingTransport`` (``fi._http``) wrap :class:`_AttemptRecorder`,
which wraps the real httpx transport and logs each attempt's outcome (a status, or the transport
error) into ``request.extensions["fi.attempts"]``. The executor reads that log to tell whether an
earlier attempt may have applied, without any change to the shared transport. Clients are built with
``follow_redirects=False`` and ``trust_env=True``. Because a ``transport=`` is passed, httpx does not
build its own proxy transports, so the default inner transport (:class:`_EnvRoutedTransport`) does it: it
asks an httpx client with ``trust_env=True`` which transport a URL gets (``HTTP_PROXY`` / ``HTTPS_PROXY`` /
``ALL_PROXY``, ``NO_PROXY``, the same rule httpx applies without a custom transport), and sends a request to
a loopback host (``fi._core.loopback``, the one rule) straight to the machine whatever the environment says,
so a credential meant for this machine is not handed to a proxy. A plain ``http://`` request that carries keys
also goes straight to its host: it reaches the transport only when ``FI_ALLOW_INSECURE_HTTP=1`` allows it, and a
request that opt-in allows is not handed to a proxy.

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
from typing import Any, Callable, Collection, Mapping, Optional, Protocol, Union

import httpx

from fi._core.loopback import is_loopback_host, pin_localhost
from fi._core.origins import PlatformOrigin
from fi._core.policy import OperationSpec, lookup
from fi._core.proxy_routing import carries_credentials
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


class _EnvRoutedTransport(httpx.BaseTransport, httpx.AsyncBaseTransport):
    """The default transport under :class:`_AttemptRecorder`: ``direct`` for a loopback host, a host
    ``NO_PROXY`` names, or when the environment has no proxy, and the proxy transport httpx would pick for
    the URL otherwise.

    ``router`` is an httpx client built with ``trust_env=True`` that does not send: it reads the
    proxy variables once and holds one transport per proxy (``_transport_for_url``, the rule httpx applies
    to a client without a custom transport; ``_transport`` is its direct one). Proxy credentials in the
    proxy URL go in the ``Proxy-Authorization`` header and nowhere else."""

    _fi_decided_by_environment = True  # the plain-HTTP check asks the same router (fi._core.http_security)

    def __init__(self, direct: Any, router: Any) -> None:
        self._direct = direct
        self._router_source = router
        self._router_built: Any = None
        self._router_lock = threading.Lock()

    @property
    def _router(self) -> Any:
        """The proxy router, built on first use: a literal loopback host does not ask it, so a proxy variable the router
        cannot read does not stop a request that goes direct."""
        with self._router_lock:
            if self._router_built is None:
                source = self._router_source
                self._router_built = source() if callable(source) else source
            return self._router_built

    def _pick(self, url: httpx.URL, request: Optional[httpx.Request] = None) -> Any:
        if is_loopback_host(url.host):
            return self._direct
        if url.scheme == "http" and request is not None and carries_credentials(request.headers):
            return self._direct  # plain HTTP that carries keys is allowed only by the opt-in, and goes straight to its host
        picked = self._router._transport_for_url(url)
        return self._direct if picked is self._router._transport else picked

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        return self._pick(request.url, request).handle_request(request)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return await self._pick(request.url, request).handle_async_request(request)

    def close(self) -> None:
        self._direct.close()
        if self._router_built is not None:
            self._router_built.close()

    async def aclose(self) -> None:
        await self._direct.aclose()
        if self._router_built is not None:
            await self._router_built.aclose()


class _AttemptRecorder(httpx.BaseTransport, httpx.AsyncBaseTransport):
    """Sits under ``RetryingTransport`` and logs every attempt's outcome into the request."""

    @property
    def _fi_decided_by_environment(self) -> bool:
        return self._inner is None and self._inner_async is None

    def __init__(self, inner: Any = None, inner_async: Any = None) -> None:
        self._inner = inner
        self._inner_async = inner_async
        self._default_sync: _EnvRoutedTransport | None = None
        self._default_async: _EnvRoutedTransport | None = None
        self._lock = threading.Lock()

    def _sync(self) -> httpx.BaseTransport:
        with self._lock:
            if self._inner is not None:
                return self._inner
            if self._default_sync is None:
                self._default_sync = _EnvRoutedTransport(
                    pin_localhost(httpx.HTTPTransport(trust_env=True)), httpx.Client(trust_env=True)
                )
            return self._default_sync

    def _async(self) -> httpx.AsyncBaseTransport:
        with self._lock:
            if self._inner_async is not None:
                return self._inner_async
            if isinstance(self._inner, httpx.AsyncBaseTransport):
                return self._inner
            if self._default_async is None:
                self._default_async = _EnvRoutedTransport(
                    pin_localhost(httpx.AsyncHTTPTransport(trust_env=True)), httpx.AsyncClient(trust_env=True)
                )
            return self._default_async

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
        for transport in (self._inner, self._default_sync):
            if transport is not None and hasattr(transport, "close"):
                transport.close()

    async def aclose(self) -> None:
        shared = self._inner if self._inner_async is None and isinstance(self._inner, httpx.AsyncBaseTransport) else None
        for transport in (self._inner_async, shared, self._default_async):
            if transport is not None and hasattr(transport, "aclose"):
                await transport.aclose()


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
    ``{}`` for a URL that is not under the client's ``base_url``; raises on a malformed setting.
    A platform call sends them through ``without_scope``, which drops the workspace and
    organization headers in ``names`` (lower case) and says so once per name on stderr."""

    def for_url(self, url: Any) -> Mapping[str, str]:
        ...

    def without_scope(self, headers: Mapping[str, str], names: Collection[str]) -> dict[str, str]:
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

    @property
    def sends_plain_http_direct(self) -> bool:
        """Whether the transport is the SDK's own, which sends a plain-http request that carries keys straight to its host."""
        return self._recorder._fi_decided_by_environment

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
    """Return non-closing views of the pooled transports for a ``with_options`` copy.
    Build any missing transports under the core client's ``ClientRetryingTransport``."""
    sync_inner = transport._sync_transport()._wrapped
    async_inner = transport._async_transport()._wrapped
    return _NoClose(sync_inner), _NoClose(async_inner)
