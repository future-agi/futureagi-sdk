"""How a caller's ``httpx`` transport is judged when its connection pool is not httpcore's own direct pool.

``fi.platform`` and ``fi.gateway`` send a keyed plain-``http://`` request through a caller's ``httpx`` client only
when the transport the client selects sends directly. A transport counts as direct when its pool is exactly
``httpcore.ConnectionPool`` or ``httpcore.AsyncConnectionPool``, with one of httpcore's own network backends and
no ``proxy=`` setting. Every other pool is read as a proxy, and the request is refused with the code
``KEYED_PROXY_REFUSED`` before any connection is made. The pool shapes under test each send to a proxy listener:

* ``delegating-subclass``: a pool subclass that hands every request to an inner ``httpcore.HTTPProxy``;
* ``forward-subclass``: a pool subclass whose ``create_connection`` opens a forward-proxy connection, in the way
  ``httpx-socks`` builds its pools;
* ``redirecting-backend``: an exact pool built with a caller network backend that connects to the proxy listener
  whatever host it is asked for;
* ``proxy-argument``: an exact pool built with httpcore's own ``proxy=`` setting;
* ``replaced-pool-method``: an exact pool whose ``handle_request`` (``handle_async_request``) is replaced on the
  instance by the method of an ``httpcore.HTTPProxy``;
* ``replaced-create-connection``: an exact pool whose ``create_connection`` is replaced on the instance by one that
  opens a forward-proxy connection;
* ``replaced-backend-method``: an exact pool whose own network backend has ``connect_tcp`` replaced on the instance
  by one that connects to the proxy listener;
* ``inner-backend`` (async pools only): an exact pool whose automatic backend holds a caller backend as the backend
  it hands each connection to.

Each shape is sent to a loopback listener and to ``other-host.test`` (a lookup shim maps it to the loopback
interface), opted in with ``FI_ALLOW_INSECURE_HTTP=1``. Controls check that the
SDK's own transport and a caller's plain ``httpx`` transport send the keyed request directly, and that every shape,
used on its own, sends to the proxy listener.
"""

from __future__ import annotations

import asyncio
import socket
import time

import httpcore
import httpx
import pytest
from httpcore._async.http_proxy import AsyncForwardHTTPConnection
from httpcore._backends.auto import AutoBackend
from httpcore._sync.http_proxy import ForwardHTTPConnection

from fi.errors import KeyedProxyRefusedError
from fi.gateway import AsyncGateway, Gateway
from fi.platform import AsyncClient, Client
from tests.test_plain_http_key_guards import KEY, SECRET, Net, _attempt, _marker_forms, net, use_proxy  # noqa: F401

OTHER = "other-host.test"
SENDERS = ("platform-sync", "platform-async", "gateway-sync", "gateway-async")
HOSTS = {
    "loopback": "127.0.0.1",
    # Retain the released case ID; these clients expose the opt-in through the environment.
    "opted-in-by-argument": OTHER,
    "opted-in-by-environment": OTHER,
}


def lookup_shim(original):
    """A ``socket.getaddrinfo`` that resolves :data:`OTHER` to the loopback interface and passes other names on."""

    def shim(host, *args, **kwargs):
        name = host.decode("ascii", "replace") if isinstance(host, bytes) else host
        return original("127.0.0.1" if name == OTHER else host, *args, **kwargs)

    return shim


@pytest.fixture(autouse=True)
def other_host(net, monkeypatch):  # noqa: F811
    monkeypatch.setattr(socket, "getaddrinfo", lookup_shim(socket.getaddrinfo))


# ---------------------------------------------------------------------------------------------
# pool shapes: each returns a connection pool that sends to the proxy listener on ``proxy_port``
# ---------------------------------------------------------------------------------------------


def _proxy_url(port: int) -> str:
    return f"http://127.0.0.1:{port}"


class DelegatingPool(httpcore.ConnectionPool):
    def __init__(self, proxy_port: int) -> None:
        super().__init__()
        self._inner = httpcore.HTTPProxy(proxy_url=_proxy_url(proxy_port))

    def handle_request(self, request):
        return self._inner.handle_request(request)

    def close(self) -> None:
        self._inner.close()
        super().close()


class AsyncDelegatingPool(httpcore.AsyncConnectionPool):
    def __init__(self, proxy_port: int) -> None:
        super().__init__()
        self._inner = httpcore.AsyncHTTPProxy(proxy_url=_proxy_url(proxy_port))

    async def handle_async_request(self, request):
        return await self._inner.handle_async_request(request)

    async def aclose(self) -> None:
        await self._inner.aclose()
        await super().aclose()


class ForwardPool(httpcore.ConnectionPool):
    def __init__(self, proxy_port: int) -> None:
        super().__init__()
        self._proxy_origin = httpcore.URL(_proxy_url(proxy_port)).origin

    def create_connection(self, origin):
        return ForwardHTTPConnection(
            proxy_origin=self._proxy_origin,
            remote_origin=origin,
            keepalive_expiry=self._keepalive_expiry,
            network_backend=self._network_backend,
        )


class AsyncForwardPool(httpcore.AsyncConnectionPool):
    def __init__(self, proxy_port: int) -> None:
        super().__init__()
        self._proxy_origin = httpcore.URL(_proxy_url(proxy_port)).origin

    def create_connection(self, origin):
        return AsyncForwardHTTPConnection(
            proxy_origin=self._proxy_origin,
            remote_origin=origin,
            keepalive_expiry=self._keepalive_expiry,
            network_backend=self._network_backend,
        )


class RedirectingBackend(httpcore.NetworkBackend):
    """Connects to the proxy listener whatever host and port it is asked for."""

    def __init__(self, proxy_port: int) -> None:
        self._port = proxy_port
        self._inner = httpcore.SyncBackend()

    def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        return self._inner.connect_tcp("127.0.0.1", self._port, timeout, local_address, socket_options)

    def connect_unix_socket(self, path, timeout=None, socket_options=None):
        return self._inner.connect_unix_socket(path, timeout, socket_options)

    def sleep(self, seconds: float) -> None:
        self._inner.sleep(seconds)


class AsyncRedirectingBackend(httpcore.AsyncNetworkBackend):
    """:class:`RedirectingBackend` for an async pool, over httpcore's automatic backend."""

    def __init__(self, proxy_port: int) -> None:
        self._port = proxy_port
        self._inner = AutoBackend()

    async def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        return await self._inner.connect_tcp("127.0.0.1", self._port, timeout, local_address, socket_options)

    async def connect_unix_socket(self, path, timeout=None, socket_options=None):
        return await self._inner.connect_unix_socket(path, timeout, socket_options)

    async def sleep(self, seconds: float) -> None:
        await self._inner.sleep(seconds)


def _replaced_pool_method(port: int, is_async: bool):
    if is_async:
        pool = httpcore.AsyncConnectionPool()
        pool.handle_async_request = httpcore.AsyncHTTPProxy(proxy_url=_proxy_url(port)).handle_async_request
    else:
        pool = httpcore.ConnectionPool()
        pool.handle_request = httpcore.HTTPProxy(proxy_url=_proxy_url(port)).handle_request
    return pool


def _replaced_create_connection(port: int, is_async: bool):
    pool = httpcore.AsyncConnectionPool() if is_async else httpcore.ConnectionPool()
    connection = AsyncForwardHTTPConnection if is_async else ForwardHTTPConnection
    proxy_origin = httpcore.URL(_proxy_url(port)).origin
    pool.create_connection = lambda origin: connection(
        proxy_origin=proxy_origin, remote_origin=origin, network_backend=pool._network_backend
    )
    return pool


def _replaced_backend_method(proxy_port: int, is_async: bool):
    pool = httpcore.AsyncConnectionPool() if is_async else httpcore.ConnectionPool()
    backend = pool._network_backend
    original = backend.connect_tcp
    if is_async:

        async def connect_tcp(host, port, timeout=None, local_address=None, socket_options=None):
            return await original("127.0.0.1", proxy_port, timeout, local_address, socket_options)

    else:

        def connect_tcp(host, port, timeout=None, local_address=None, socket_options=None):
            return original("127.0.0.1", proxy_port, timeout, local_address, socket_options)

    backend.connect_tcp = connect_tcp
    return pool


def _inner_backend(port: int):
    pool = httpcore.AsyncConnectionPool()
    pool._network_backend._backend = AsyncRedirectingBackend(port)
    return pool


SHAPES = {
    "delegating-subclass": (DelegatingPool, AsyncDelegatingPool),
    "forward-subclass": (ForwardPool, AsyncForwardPool),
    "redirecting-backend": (
        lambda port: httpcore.ConnectionPool(network_backend=RedirectingBackend(port)),
        lambda port: httpcore.AsyncConnectionPool(network_backend=AsyncRedirectingBackend(port)),
    ),
    "proxy-argument": (
        lambda port: httpcore.ConnectionPool(proxy=httpcore.Proxy(_proxy_url(port))),
        lambda port: httpcore.AsyncConnectionPool(proxy=httpcore.Proxy(_proxy_url(port))),
    ),
    "replaced-pool-method": (
        lambda port: _replaced_pool_method(port, False),
        lambda port: _replaced_pool_method(port, True),
    ),
    "replaced-create-connection": (
        lambda port: _replaced_create_connection(port, False),
        lambda port: _replaced_create_connection(port, True),
    ),
    "replaced-backend-method": (
        lambda port: _replaced_backend_method(port, False),
        lambda port: _replaced_backend_method(port, True),
    ),
    "inner-backend": (None, _inner_backend),
}


def _sync_shape_exists(shape: str, asynchronous: bool) -> None:
    if not asynchronous and SHAPES[shape][0] is None:
        pytest.skip(f"{shape} has an async pool only")


def shape_client(shape: str, is_async: bool, proxy_port: int):
    """An ``httpx`` client whose HTTP transport holds the pool ``shape`` builds."""
    pool = SHAPES[shape][1 if is_async else 0](proxy_port)
    transport = httpx.AsyncHTTPTransport() if is_async else httpx.HTTPTransport()
    transport._pool = pool
    return httpx.AsyncClient(transport=transport) if is_async else httpx.Client(transport=transport)


def plain_client(is_async: bool):
    if is_async:
        return httpx.AsyncClient(transport=httpx.AsyncHTTPTransport())
    return httpx.Client(transport=httpx.HTTPTransport())


def is_async(sender: str) -> bool:
    return sender.endswith("-async")


def base_url(net: Net, host: str) -> str:  # noqa: F811
    return f"http://{HOSTS[host]}:{net.target.port}"


def send(net: Net, sender: str, host: str, http_client=None):  # noqa: F811
    """Send one keyed request from ``sender`` to the target listener, capturing any exception."""
    kwargs = dict(api_key=KEY, base_url=base_url(net, host), max_retries=0, timeout=3, http_client=http_client)
    messages = [{"role": "user", "content": "hi"}]

    def run():
        if sender == "platform-sync":
            with Client(secret_key=SECRET, **kwargs) as client:
                return client.request("GET", "/v1/ping", unwrap=None)
        with Gateway(**kwargs) as client:
            return client.chat.completions.create(model="m", messages=messages)

    async def run_async():
        if sender == "platform-async":
            async with AsyncClient(secret_key=SECRET, **kwargs) as client:
                return await client.request("GET", "/v1/ping", unwrap=None)
        async with AsyncGateway(**kwargs) as client:
            return await client.chat.completions.create(model="m", messages=messages)

    return _attempt(lambda: asyncio.run(run_async())) if is_async(sender) else _attempt(run)


def observed(net: Net) -> tuple:  # noqa: F811
    """(proxy connections, proxy marker occurrences, target connections, target marker occurrences)."""
    time.sleep(0.05)
    forms = _marker_forms(KEY, SECRET)
    counts = []
    for sink in (net.proxy, net.target):
        with sink._lock:
            counts += [sink.connections, sum(sink.raw.count(form) for form in forms)]
    return tuple(counts)


def _opt_in_by_environment(monkeypatch, host: str) -> None:
    if host != "loopback":
        monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")


senders = pytest.mark.parametrize("sender", list(SENDERS))
hosts = pytest.mark.parametrize("host", list(HOSTS))
shapes = pytest.mark.parametrize("shape", list(SHAPES))


# ---------------------------------------------------------------------------------------------
# a pool that sends through a proxy: refused before any connection
# ---------------------------------------------------------------------------------------------


@shapes
@hosts
@senders
def test_keyed_request_through_a_pool_that_is_not_httpcore_direct_is_refused(monkeypatch, net, sender, host, shape):  # noqa: F811
    _sync_shape_exists(shape, is_async(sender))
    _opt_in_by_environment(monkeypatch, host)
    exc = send(net, sender, host, shape_client(shape, is_async(sender), net.proxy.port))
    assert observed(net) == (0, 0, 0, 0), f"proxy conns, proxy markers, target conns, target markers; error: {exc!r}"
    assert exc is not None, "no error was raised"
    assert isinstance(exc, KeyedProxyRefusedError), f"{type(exc).__name__}: {exc}"
    assert getattr(exc, "code", None) == "KEYED_PROXY_REFUSED", f"code: {getattr(exc, 'code', None)!r}"
    assert KEY not in str(exc) and SECRET not in str(exc)


# ---------------------------------------------------------------------------------------------
# controls: direct transports send the keyed request to the target; every shape routes to the proxy
# ---------------------------------------------------------------------------------------------


@hosts
@senders
def test_sdk_transport_sends_the_keyed_request_directly(monkeypatch, net, sender, host):  # noqa: F811
    _opt_in_by_environment(monkeypatch, host)
    use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"), no_proxy="")
    send(net, sender, host)
    proxy_conns, proxy_markers, _, target_markers = observed(net)
    assert (proxy_conns, proxy_markers) == (0, 0)
    assert target_markers > 0


@hosts
@senders
def test_caller_plain_httpx_transport_sends_the_keyed_request_directly(monkeypatch, net, sender, host):  # noqa: F811
    _opt_in_by_environment(monkeypatch, host)
    send(net, sender, host, plain_client(is_async(sender)))
    proxy_conns, proxy_markers, _, target_markers = observed(net)
    assert (proxy_conns, proxy_markers) == (0, 0)
    assert target_markers > 0


@pytest.mark.parametrize("host", ["127.0.0.1", OTHER])
@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@shapes
def test_each_shape_used_without_the_sdk_sends_to_the_proxy(net, shape, asynchronous, host):  # noqa: F811
    _sync_shape_exists(shape, asynchronous)
    url = f"http://{host}:{net.target.port}/v1/ping"
    client = shape_client(shape, asynchronous, net.proxy.port)
    if asynchronous:
        async def run():
            async with client:
                return await client.get(url)

        response = asyncio.run(run())
    else:
        with client:
            response = client.get(url)
    assert response.status_code == 200
    proxy_conns, _, target_conns, _ = observed(net)
    assert (proxy_conns, target_conns) == (1, 0)
