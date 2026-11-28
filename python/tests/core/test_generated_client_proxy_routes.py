"""The generated ``AuthenticatedClient`` sends its token over plain http to a loopback host straight to this machine
with the environment's proxy variables off, as the platform client and the judge do, and refuses a plain-http token
that a proxy of the caller's transport would carry, for loopback and for a remote host opted in alike."""

from __future__ import annotations

import asyncio
import uuid

import httpx
import pytest

from fi.errors import KeyedProxyRefusedError
from fi.generated.openapi_client.client import AuthenticatedClient
from tests.core._localhost_dial import Sink, proxy, resolver_shim, target  # noqa: F401


def _token() -> str:
    return "tok" + uuid.uuid4().hex + "mark"


def _send_sync(client: AuthenticatedClient) -> None:
    client.get_httpx_client().get("/probe")


def _send_async(client: AuthenticatedClient) -> None:
    async def run() -> None:
        await client.get_async_httpx_client().get("/probe")

    asyncio.run(run())


SENDERS = {"sync": _send_sync, "async": _send_async}


def _send(kind: str, client: AuthenticatedClient) -> None:
    try:
        SENDERS[kind](client)
    except KeyedProxyRefusedError:
        raise
    except BaseException:  # the listener ends the exchange; only where the connection went is measured
        pass


def _transport(kind: str, sink: Sink) -> object:
    url = f"http://127.0.0.1:{sink.port}"
    return httpx.HTTPTransport(proxy=url) if kind == "sync" else httpx.AsyncHTTPTransport(proxy=url)


@pytest.mark.parametrize("kind", SENDERS)
@pytest.mark.parametrize("variable", ["HTTP_PROXY", "http_proxy", "ALL_PROXY"])
@pytest.mark.parametrize("host", ["127.0.0.1", "localhost"])
def test_a_loopback_token_goes_direct_with_an_environment_proxy(kind, variable, host, target, proxy):
    token = _token()
    with resolver_shim({variable: f"http://127.0.0.1:{proxy.port}"}):
        _send(kind, AuthenticatedClient(base_url=f"http://{host}:{target.port}", token=token))
    assert proxy.connections == 0 and proxy.raw.count(token.encode()) == 0, proxy.first_lines
    assert target.connections >= 1 and target.raw.count(token.encode()) >= 1


@pytest.mark.parametrize("kind", SENDERS)
@pytest.mark.parametrize("host", ["127.0.0.1", "localhost"])
def test_a_loopback_token_through_a_caller_transport_proxy_is_refused(kind, host, target, proxy):
    token = _token()
    client = AuthenticatedClient(
        base_url=f"http://{host}:{target.port}", token=token, httpx_args={"transport": _transport(kind, proxy)}
    )
    with resolver_shim({}), pytest.raises(KeyedProxyRefusedError):
        _send(kind, client)
    assert proxy.connections == 0 and proxy.raw.count(token.encode()) == 0
    assert target.connections == 0


@pytest.mark.parametrize("kind", SENDERS)
def test_an_opted_in_remote_token_through_a_caller_transport_proxy_is_refused(kind, proxy):
    token = _token()
    client = AuthenticatedClient(
        base_url="http://remote.test:8080", token=token, httpx_args={"transport": _transport(kind, proxy)}
    )
    with resolver_shim({"FI_ALLOW_INSECURE_HTTP": "1"}), pytest.raises(KeyedProxyRefusedError):
        _send(kind, client)
    assert proxy.connections == 0 and proxy.raw.count(token.encode()) == 0


@pytest.mark.parametrize("kind", SENDERS)
def test_an_https_base_url_with_a_caller_transport_proxy_builds_its_client(kind, proxy):
    client = AuthenticatedClient(
        base_url="https://remote.test", token=_token(), httpx_args={"transport": _transport(kind, proxy)}
    )
    with resolver_shim({}):
        built = client.get_httpx_client() if kind == "sync" else client.get_async_httpx_client()
    assert built is not None and proxy.connections == 0
