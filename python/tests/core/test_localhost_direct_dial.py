"""The name ``localhost`` is dialed to 127.0.0.1 or ``::1`` on every direct path, whatever the system resolver answers,
and a name that only resolves to loopback is routed like any other host.

Each sender sends one https request carrying planted marker keys to a loopback listener. The resolver is replaced by
a shim that answers ``localhost`` with a routable test address and ``loop.test`` with 127.0.0.1; every connect is
recorded, and a connect to the test address is redirected to the listener so that nothing leaves this machine. The
listeners count connections and the raw marker bytes they receive: the target, and a CONNECT-aware proxy sink.
"""

from __future__ import annotations

import asyncio
import socket
from typing import Any, Callable, Optional

import httpx
import pytest

from fi._credentials import Credentials
from fi._core.transport import _AttemptRecorder
from fi._http import AsyncRetryingTransport, ClientRetryingTransport, LazyKeyAuth, RetryingTransport
from tests.core._localhost_dial import (  # noqa: F401
    KEY, LOOPBACK_ADDRESSES, RESOLVER_ANSWER, SECRET, Sink, resolver_shim, target, proxy,
)


# --- the senders: each sends one keyed https request, with any failure of the exchange ignored ----------------------


def _creds(url: str) -> Credentials:
    return Credentials(api_key=KEY, secret_key=SECRET, base_url=url, keys_source="argument", base_url_source="argument")


def _headers() -> dict[str, str]:
    return {"X-Api-Key": KEY, "X-Secret-Key": SECRET}


def _client_sync(url: str) -> None:
    auth = LazyKeyAuth(lambda: _creds(url))
    with httpx.Client(transport=ClientRetryingTransport(retries=0), auth=auth, timeout=2, follow_redirects=False) as client:
        client.get(url)


def _client_async(url: str) -> None:
    auth = LazyKeyAuth(lambda: _creds(url))

    async def go() -> None:
        async with httpx.AsyncClient(transport=ClientRetryingTransport(retries=0), auth=auth, timeout=2,
                                     follow_redirects=False) as client:
            await client.get(url)

    asyncio.run(go())


def _platform_sync(url: str) -> None:
    with httpx.Client(transport=RetryingTransport(_AttemptRecorder(), retries=0), timeout=2, follow_redirects=False) as client:
        client.get(url, headers=_headers())


def _platform_async(url: str) -> None:
    async def go() -> None:
        transport = AsyncRetryingTransport(_AttemptRecorder(), retries=0)
        async with httpx.AsyncClient(transport=transport, timeout=2, follow_redirects=False) as client:
            await client.get(url, headers=_headers())

    asyncio.run(go())


def _gateway_sync(url: str) -> None:
    from fi.gateway._transport._direct import LoopbackDirectClient

    with LoopbackDirectClient(timeout=2) as client:
        client.get(url, headers=_headers())


def _gateway_async(url: str) -> None:
    from fi.gateway._transport._direct import AsyncLoopbackDirectClient

    async def go() -> None:
        async with AsyncLoopbackDirectClient(timeout=2) as client:
            await client.get(url, headers=_headers())

    asyncio.run(go())


def _requests_session(url: str) -> None:
    from fi._core.requests_session import LoopbackDirectSession

    with LoopbackDirectSession() as session:
        session.get(url, headers=_headers(), timeout=2)


def _plan(url: str) -> Any:
    from fi.sandbox._channel.connect import ConnectionPlan

    return ConnectionPlan(url=url, origin="https://localhost", secret=(["proto", KEY], KEY))


def _channel_sync(url: str) -> None:
    from fi.sandbox._channel._sync.stream import ExecStream

    ExecStream._connect(_plan(url.replace("https://", "wss://")), lambda text: text)


def _channel_async(url: str) -> None:
    from fi.sandbox._channel._async.stream import AsyncExecStream

    asyncio.run(AsyncExecStream._connect(_plan(url.replace("https://", "wss://")), lambda text: text))


SENDERS: dict[str, Callable[[str], None]] = {
    "client-sync": _client_sync,
    "client-async": _client_async,
    "platform-sync": _platform_sync,
    "platform-async": _platform_async,
    "gateway-sync": _gateway_sync,
    "gateway-async": _gateway_async,
    "requests-session": _requests_session,
    "channel-sync": _channel_sync,
    "channel-async": _channel_async,
}
# The senders that read the environment's proxy variables for a host that is not loopback as written.
ROUTED_BY_ENVIRONMENT = [name for name in SENDERS if not name.startswith("client-")]


def send(sender: str, url: str) -> None:
    try:
        SENDERS[sender](url)
    except BaseException:  # the listener ends the exchange: only where the connection went is measured
        pass


@pytest.mark.parametrize("sender", SENDERS)
@pytest.mark.parametrize("with_proxy", [False, True], ids=["no-proxy", "env-proxy"])
def test_localhost_is_dialed_to_loopback_whatever_the_resolver_answers(sender, with_proxy, target, proxy):
    env = {"HTTPS_PROXY": f"http://127.0.0.1:{proxy.port}", "https_proxy": f"http://127.0.0.1:{proxy.port}"} if with_proxy else {}
    with resolver_shim(env) as connects:
        send(sender, f"https://localhost:{target.port}/")
    assert RESOLVER_ANSWER not in connects, connects
    assert connects and set(connects) <= LOOPBACK_ADDRESSES, connects
    assert connects[0] == "127.0.0.1", connects
    assert target.connections >= 1
    assert proxy.connections == 0 and proxy.marker_bytes == 0
    assert target.marker_bytes == 0  # the keys travel inside TLS: none are readable at the listener


@pytest.mark.parametrize("sender", SENDERS)
def test_localhost_keeps_its_own_name_for_the_tls_server_name(sender, target):
    with resolver_shim():
        send(sender, f"https://localhost:{target.port}/")
    hello = target.raw
    assert hello[:1] == b"\x16", hello[:16]  # a TLS ClientHello
    assert b"localhost" in hello
    assert b"127.0.0.1" not in hello and RESOLVER_ANSWER.encode() not in hello


def _ipv6_listener() -> Optional[Sink]:
    try:
        return Sink(family=socket.AF_INET6)
    except OSError:
        return None


@pytest.mark.parametrize("sender", SENDERS)
def test_localhost_is_dialed_to_the_ipv6_loopback_when_127_0_0_1_does_not_answer(sender):
    listener = _ipv6_listener()
    if listener is None:
        pytest.skip("no IPv6 loopback on this machine")
    try:
        with socket.socket() as probe:  # a port that nothing accepts on 127.0.0.1
            probe.settimeout(0.3)
            if probe.connect_ex(("127.0.0.1", listener.port)) == 0:
                pytest.skip("something answers on 127.0.0.1 at the same port")
        with resolver_shim() as connects:
            send(sender, f"https://localhost:{listener.port}/")
        assert RESOLVER_ANSWER not in connects, connects
        assert connects[:2] == ["127.0.0.1", "::1"], connects
        assert listener.connections >= 1
    finally:
        listener.close()


@pytest.mark.parametrize("sender", ROUTED_BY_ENVIRONMENT)
def test_a_name_that_resolves_to_loopback_goes_through_the_environment_proxy(sender, target, proxy):
    env = {"HTTPS_PROXY": f"http://127.0.0.1:{proxy.port}", "https_proxy": f"http://127.0.0.1:{proxy.port}"}
    with resolver_shim(env) as connects:
        send(sender, f"https://loop.test:{target.port}/")
    assert proxy.connections >= 1 and proxy.first_lines[0].startswith(b"CONNECT loop.test:"), proxy.first_lines
    assert target.connections == 0 and target.marker_bytes == 0 and proxy.marker_bytes == 0
    assert "127.0.0.1" in connects


@pytest.mark.parametrize("sender", ROUTED_BY_ENVIRONMENT)
@pytest.mark.parametrize("host", ["localhost.", "app.localhost", "a.b.localhost"])
def test_a_name_that_is_not_localhost_as_written_goes_through_the_environment_proxy(sender, host, target, proxy):
    env = {"HTTPS_PROXY": f"http://127.0.0.1:{proxy.port}", "https_proxy": f"http://127.0.0.1:{proxy.port}"}
    with resolver_shim(env):
        send(sender, f"https://{host}:{target.port}/")
    assert proxy.connections >= 1 and proxy.first_lines[0].startswith(b"CONNECT "), proxy.first_lines
    assert target.connections == 0
    assert proxy.marker_bytes == 0


def test_a_name_that_resolves_to_loopback_is_refused_over_plain_http_without_the_opt_in(target, proxy):
    """Plain http with keys to a name that is not loopback as written follows the plain-http rule, not the loopback one."""
    from fi.errors import ConfigurationError

    url = f"http://loop.test:{target.port}/"
    auth = LazyKeyAuth(lambda: _creds(url))
    with resolver_shim({"HTTP_PROXY": f"http://127.0.0.1:{proxy.port}"}):
        with httpx.Client(transport=RetryingTransport(_AttemptRecorder(), retries=0), auth=auth, timeout=2) as client:
            with pytest.raises(ConfigurationError):
                client.get(url)
    assert target.connections == 0 and proxy.connections == 0
    assert target.marker_bytes == 0 and proxy.marker_bytes == 0
