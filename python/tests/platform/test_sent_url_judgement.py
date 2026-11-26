"""Keyed platform requests are judged by the URL and proxy httpx sends them with.

A caller may supply an ``httpx`` client with its own ``base_url`` and give the platform client a base URL without a
scheme (``/``, ``/api``, ``//host:port``). httpx then merges the two, so the request goes to the client's base URL,
through whatever proxy the client takes from the environment (``HTTP_PROXY``, ``ALL_PROXY``, ``NO_PROXY``, read only
when the client trusts the environment). The judgement has to be made on that final request: plain ``http://`` to a
host that is not loopback is refused without the opt-in, and a keyed plain ``http://`` request is never sent through
a proxy.

Every case sends one keyed request and reads what reached the loopback listeners (target and proxy): the connection
count and the bytes that hold the marker key. ``api.futureagi.com`` resolves to the loopback interface through the
lookup shim of ``tests/test_plain_http_key_guards.py``, so no case reaches a real host.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest

from fi.platform import APIConnectionError, AsyncClient, Client
from tests.test_plain_http_key_guards import CODE, KEY, SECRET, net, refused, use_proxy  # noqa: F401  (net is autouse)

HOST = "api.futureagi.com"

SCHEMELESS = pytest.mark.parametrize(
    "base",
    [
        pytest.param("/", id="root"),
        pytest.param("/api", id="path"),
        pytest.param("//" + HOST + ":{port}", id="network-path"),
    ],
)
TRANSPORTS = pytest.mark.parametrize("transport", [pytest.param("sync", id="sync"), pytest.param("async", id="async")])


def _attempt(call):
    try:
        call()
    except Exception as exc:  # the listener's reply may not parse; what reached the listeners is what is read
        return exc
    return None


def send(transport: str, base: str, http=None, **kwargs):
    """Send one keyed ``GET /v1/ping`` through ``Client`` or ``AsyncClient``. ``http(cls)`` builds the caller's
    httpx client from ``httpx.Client`` or ``httpx.AsyncClient``; ``None`` leaves the client to the SDK."""
    if transport == "sync":
        caller = http(httpx.Client) if http else None

        def run():
            client = Client(api_key=KEY, secret_key=SECRET, base_url=base, max_retries=0, timeout=3, http_client=caller, **kwargs)
            try:
                client.request("GET", "/v1/ping", unwrap=None)
            finally:
                client.close()
                if caller is not None:
                    caller.close()

        return _attempt(run)

    async def arun():
        caller = http(httpx.AsyncClient) if http else None
        client = AsyncClient(api_key=KEY, secret_key=SECRET, base_url=base, max_retries=0, timeout=3, http_client=caller, **kwargs)
        try:
            await client.request("GET", "/v1/ping", unwrap=None)
        finally:
            await client.aclose()
            if caller is not None:
                await caller.aclose()

    return _attempt(lambda: asyncio.run(arun()))


def caller_client(base_url: str, **kwargs):
    return lambda cls: cls(base_url=base_url, **kwargs)


def plain_base(net) -> str:
    return f"http://{HOST}:{net.target.port}"


# ---------------------------------------------------------------------------------------------
# a base URL without a scheme, merged with the plain http base URL of the caller's client
# ---------------------------------------------------------------------------------------------


@TRANSPORTS
@SCHEMELESS
def test_schemeless_base_merged_with_callers_plain_http_base_is_refused(net, transport, base):
    exc = send(transport, base.format(port=net.target.port), caller_client(plain_base(net)))
    net.nothing_sent()
    refused(exc, ValueError)


@TRANSPORTS
@SCHEMELESS
@pytest.mark.parametrize("variable", [pytest.param(("HTTP_PROXY",), id="HTTP_PROXY"), pytest.param(("ALL_PROXY",), id="ALL_PROXY")])
def test_schemeless_base_with_environment_proxy_is_refused(monkeypatch, net, transport, base, variable):
    use_proxy(monkeypatch, net, names=variable)
    exc = send(transport, base.format(port=net.target.port), caller_client(plain_base(net)))
    net.nothing_sent()
    refused(exc, ValueError)


@TRANSPORTS
@SCHEMELESS
def test_schemeless_base_that_no_proxy_sends_directly_is_refused(monkeypatch, net, transport, base):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY",), no_proxy=HOST)
    exc = send(transport, base.format(port=net.target.port), caller_client(plain_base(net)))
    net.nothing_sent()
    refused(exc, ValueError)


@TRANSPORTS
@SCHEMELESS
def test_schemeless_base_with_client_that_ignores_the_environment_is_refused(monkeypatch, net, transport, base):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY",))
    exc = send(transport, base.format(port=net.target.port), caller_client(plain_base(net), trust_env=False))
    net.nothing_sent()
    refused(exc, ValueError)


@TRANSPORTS
@SCHEMELESS
@pytest.mark.parametrize("variable", [pytest.param(("HTTP_PROXY",), id="HTTP_PROXY"), pytest.param(("ALL_PROXY",), id="ALL_PROXY")])
def test_opt_in_with_schemeless_base_is_refused_when_the_environment_proxy_applies(monkeypatch, net, transport, base, variable):
    use_proxy(monkeypatch, net, names=variable)
    exc = send(transport, base.format(port=net.target.port), caller_client(plain_base(net)), allow_insecure_http=True)
    net.nothing_sent()
    refused(exc, ValueError)


@TRANSPORTS
@SCHEMELESS
def test_opt_in_with_schemeless_base_is_refused_when_the_callers_client_has_a_proxy(net, transport, base):
    proxied = caller_client(plain_base(net), proxy=f"http://127.0.0.1:{net.proxy.port}")
    exc = send(transport, base.format(port=net.target.port), proxied, allow_insecure_http=True)
    net.nothing_sent()
    refused(exc, ValueError)


@TRANSPORTS
@SCHEMELESS
def test_schemeless_base_merged_with_callers_loopback_base_is_not_sent_through_the_environment_proxy(monkeypatch, net, transport, base):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY",))
    loopback = f"http://127.0.0.1:{net.target.port}"
    written = base.replace(HOST, "127.0.0.1").format(port=net.target.port)
    exc = send(transport, written, caller_client(loopback))
    net.nothing_sent()
    refused(exc, ValueError)


# ---------------------------------------------------------------------------------------------
# controls
# ---------------------------------------------------------------------------------------------


@TRANSPORTS
@SCHEMELESS
def test_opt_in_with_schemeless_base_and_client_that_ignores_the_environment_is_sent_directly(monkeypatch, net, transport, base):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"))
    send(transport, base.format(port=net.target.port), caller_client(plain_base(net), trust_env=False), allow_insecure_http=True)
    net.delivered_direct()


@TRANSPORTS
@SCHEMELESS
def test_schemeless_base_merged_with_callers_https_base_is_not_refused(net, transport, base):
    exc = send(transport, base.format(port=net.target.port), caller_client(f"https://{HOST}:{net.target.port}"))
    assert getattr(exc, "code", None) != CODE
    assert net.target.marker_bytes() == 0, net.report()


@TRANSPORTS
@SCHEMELESS
def test_schemeless_base_merged_with_callers_https_base_still_uses_the_environment_proxy(monkeypatch, net, transport, base):
    use_proxy(monkeypatch, net, names=("HTTPS_PROXY",))
    exc = send(transport, base.format(port=net.target.port), caller_client(f"https://{HOST}:{net.target.port}"))
    assert getattr(exc, "code", None) != CODE
    assert net.proxy.connections >= 1, net.report()
    assert net.proxy.marker_bytes() == 0, net.report()


@TRANSPORTS
def test_absolute_plain_http_base_with_callers_client_is_refused(net, transport):
    exc = send(transport, plain_base(net), caller_client(plain_base(net)))
    net.nothing_sent()
    refused(exc, ValueError)


@TRANSPORTS
def test_absolute_loopback_base_with_callers_client_and_environment_proxy_is_refused(monkeypatch, net, transport):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY",))
    loopback = f"http://127.0.0.1:{net.target.port}"
    exc = send(transport, loopback, caller_client(loopback))
    net.nothing_sent()
    refused(exc, ValueError)


@TRANSPORTS
@SCHEMELESS
def test_schemeless_base_with_the_sdks_own_client_fails_before_any_connection(net, transport, base):
    exc = send(transport, base.format(port=net.target.port))
    assert isinstance(exc, (APIConnectionError, ValueError)), repr(exc)
    assert KEY not in str(exc) and SECRET not in str(exc)
    net.nothing_sent()


@TRANSPORTS
@SCHEMELESS
def test_schemeless_base_with_callers_in_process_transport_is_answered_in_process(net, transport, base):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={})

    def http(cls):
        mock = httpx.MockTransport(handler)
        return cls(base_url=plain_base(net), transport=mock)

    exc = send(transport, base.format(port=net.target.port), http)
    assert exc is None, repr(exc)
    assert len(seen) == 1 and seen[0].url.scheme == "http" and seen[0].headers["X-Api-Key"] == KEY
    net.nothing_sent()
