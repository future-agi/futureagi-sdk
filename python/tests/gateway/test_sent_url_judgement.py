"""Keyed gateway requests with caller-supplied HTTPX clients.

A network-path base and its explicit-scheme twin are judged using the caller's
origin. A path-only base is rejected. Loopback listeners record connections
and marker bytes for chat, streaming, and raw requests.
"""
# ruff: noqa: F811

from __future__ import annotations

import asyncio
from urllib.parse import urlsplit

import httpx
import pytest

from fi.errors import InsecureHttpRefusedError, KeyedProxyRefusedError
from fi.gateway import AgentCCError, APIConnectionError, AsyncGateway, Gateway
from tests.test_plain_http_key_guards import KEY, SECRET, _attempt, net, use_proxy  # noqa: F401  (net is autouse)

HOST = "api.futureagi.com"
MESSAGES = [{"role": "user", "content": "hi"}]

PATH_ONLY = "/api"
SCHEMELESS_BASES = (
    pytest.param(PATH_ONLY, id="path"),
    pytest.param("//{authority}", id="network-path"),
)
SCHEMELESS = pytest.mark.parametrize("base", SCHEMELESS_BASES)
CALLER_BASES = pytest.mark.parametrize(
    "base", [*SCHEMELESS_BASES, pytest.param("{caller_base}", id="explicit-scheme")],
)
TRANSPORTS = pytest.mark.parametrize("transport", [pytest.param("sync", id="sync"), pytest.param("async", id="async")])
CALLS = pytest.mark.parametrize("call", [pytest.param("chat", id="chat"), pytest.param("stream", id="stream"), pytest.param("raw", id="raw")])


def _sync_call(gw, call: str) -> None:
    if call == "chat":
        gw.chat.completions.create(model="m", messages=MESSAGES)
    elif call == "stream":
        for _ in gw.chat.completions.create(model="m", messages=MESSAGES, stream=True):
            pass
    else:
        gw.files.content("file-1")


async def _async_call(gw, call: str) -> None:
    if call == "chat":
        await gw.chat.completions.create(model="m", messages=MESSAGES)
    elif call == "stream":
        async for _ in await gw.chat.completions.create(model="m", messages=MESSAGES, stream=True):
            pass
    else:
        await gw.files.content("file-1")


def send(transport: str, base: str, http=None, *, call: str = "chat"):
    """Send one keyed request through ``Gateway`` or ``AsyncGateway``. ``http(cls)`` builds the caller's httpx
    client from ``httpx.Client`` or ``httpx.AsyncClient``; ``None`` leaves the client to the SDK."""
    if transport == "sync":
        def run():
            caller = http(httpx.Client) if http else None
            try:
                gw = Gateway(api_key=KEY, base_url=base, max_retries=0, timeout=3, http_client=caller)
                try:
                    _sync_call(gw, call)
                finally:
                    gw.close()
            finally:
                if caller is not None:
                    caller.close()

        return _attempt(run)

    async def arun():
        caller = http(httpx.AsyncClient) if http else None
        try:
            gw = AsyncGateway(api_key=KEY, base_url=base, max_retries=0, timeout=3, http_client=caller)
            try:
                await _async_call(gw, call)
            finally:
                await gw.aclose()
        finally:
            if caller is not None:
                await caller.aclose()

    return _attempt(lambda: asyncio.run(arun()))


def _schemeless_refusal(exc):
    assert isinstance(exc, AgentCCError), repr(exc)
    assert "must be an absolute HTTP(S) URL" in str(exc)
    assert KEY not in str(exc) and SECRET not in str(exc)


def _coded_refusal(exc, cls, code):
    assert isinstance(exc, cls), repr(exc)
    assert exc.code == code
    assert KEY not in str(exc) and SECRET not in str(exc)


def caller_client(base_url: str, **kwargs):
    return lambda cls: cls(base_url=base_url, **kwargs)


def send_with_caller(mode, base, caller_base, *, call="chat", **client_options):
    written = base.format(authority=urlsplit(caller_base).netloc, caller_base=caller_base)
    return send(mode, written, caller_client(caller_base, **client_options), call=call)


def plain_base(net) -> str:
    return f"http://{HOST}:{net.target.port}"


def _future_agi_http_refusal(base, exc):
    if base == PATH_ONLY:
        _schemeless_refusal(exc)
    else:
        _coded_refusal(exc, InsecureHttpRefusedError, "INSECURE_HTTP_REFUSED")
        assert exc.host == HOST


def _tls_attempt_failed(exc, net, *, proxied):
    assert type(exc) is APIConnectionError, repr(exc)
    assert KEY not in str(exc) and SECRET not in str(exc)
    assert net.target.marker_bytes() == net.proxy.marker_bytes() == 0, net.report()
    assert (net.target.connections, net.proxy.connections) == ((0, 1) if proxied else (1, 0)), net.report()


@TRANSPORTS
@CALLS
@CALLER_BASES
def test_caller_future_agi_http_base_is_refused(net, transport, call, base):
    exc = send_with_caller(transport, base, plain_base(net), call=call)
    net.nothing_sent()
    _future_agi_http_refusal(base, exc)


@TRANSPORTS
@CALLS
@CALLER_BASES
@pytest.mark.parametrize("variable", [pytest.param(("HTTP_PROXY",), id="HTTP_PROXY"), pytest.param(("ALL_PROXY",), id="ALL_PROXY")])
def test_caller_future_agi_http_base_with_environment_proxy_is_refused(monkeypatch, net, transport, call, base, variable):
    use_proxy(monkeypatch, net, names=variable)
    exc = send_with_caller(transport, base, plain_base(net), call=call)
    net.nothing_sent()
    _future_agi_http_refusal(base, exc)


@TRANSPORTS
@CALLER_BASES
def test_caller_future_agi_http_base_with_no_proxy_is_refused(monkeypatch, net, transport, base):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY",), no_proxy=HOST)
    exc = send_with_caller(transport, base, plain_base(net))
    net.nothing_sent()
    _future_agi_http_refusal(base, exc)


@TRANSPORTS
@CALLER_BASES
def test_caller_future_agi_http_base_with_trust_env_disabled_is_refused(monkeypatch, net, transport, base):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY",))
    exc = send_with_caller(transport, base, plain_base(net), trust_env=False)
    net.nothing_sent()
    _future_agi_http_refusal(base, exc)


@TRANSPORTS
@CALLS
@CALLER_BASES
@pytest.mark.parametrize("variable", [pytest.param(("HTTP_PROXY",), id="HTTP_PROXY"), pytest.param(("ALL_PROXY",), id="ALL_PROXY")])
def test_opt_in_does_not_permit_caller_future_agi_http_base_with_environment_proxy(monkeypatch, net, transport, call, base, variable):
    use_proxy(monkeypatch, net, names=variable)
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    exc = send_with_caller(transport, base, plain_base(net), call=call)
    net.nothing_sent()
    _future_agi_http_refusal(base, exc)


@TRANSPORTS
@CALLER_BASES
def test_opt_in_does_not_permit_caller_future_agi_http_base_with_explicit_proxy(monkeypatch, net, transport, base):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    exc = send_with_caller(transport, base, plain_base(net), proxy=f"http://127.0.0.1:{net.proxy.port}")
    net.nothing_sent()
    _future_agi_http_refusal(base, exc)


@TRANSPORTS
@CALLER_BASES
def test_caller_loopback_http_base_with_environment_proxy_is_refused(monkeypatch, net, transport, base):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY",))
    exc = send_with_caller(transport, base, f"http://127.0.0.1:{net.target.port}")
    net.nothing_sent()
    if base == PATH_ONLY:
        _schemeless_refusal(exc)
    else:
        _coded_refusal(exc, KeyedProxyRefusedError, "KEYED_PROXY_REFUSED")


@TRANSPORTS
@CALLS
@CALLER_BASES
def test_opt_in_does_not_permit_caller_future_agi_http_base_with_trust_env_disabled(monkeypatch, net, transport, call, base):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"))
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    exc = send_with_caller(transport, base, plain_base(net), call=call, trust_env=False)
    net.nothing_sent()
    _future_agi_http_refusal(base, exc)


@TRANSPORTS
@CALLER_BASES
def test_caller_https_base_attempts_direct_tls(net, transport, base):
    exc = send_with_caller(transport, base, f"https://{HOST}:{net.target.port}")
    if base == PATH_ONLY:
        net.nothing_sent()
        _schemeless_refusal(exc)
    else:
        _tls_attempt_failed(exc, net, proxied=False)


@TRANSPORTS
@CALLER_BASES
def test_caller_https_base_attempts_tls_via_environment_proxy(monkeypatch, net, transport, base):
    use_proxy(monkeypatch, net, names=("HTTPS_PROXY",))
    exc = send_with_caller(transport, base, f"https://{HOST}:{net.target.port}")
    if base == PATH_ONLY:
        net.nothing_sent()
        _schemeless_refusal(exc)
    else:
        _tls_attempt_failed(exc, net, proxied=True)
        connect, _, tls = net.proxy.raw.partition(b"\r\n\r\n")
        assert connect.split(b"\r\n", 1)[0] == f"CONNECT {HOST}:{net.target.port} HTTP/1.1".encode()
        assert tls.startswith(b"\x16\x03")


@TRANSPORTS
def test_absolute_plain_http_base_with_callers_client_is_refused(net, transport):
    exc = send(transport, plain_base(net), caller_client(plain_base(net)))
    net.nothing_sent()
    _coded_refusal(exc, InsecureHttpRefusedError, "INSECURE_HTTP_REFUSED")


@TRANSPORTS
def test_absolute_loopback_base_with_callers_client_and_environment_proxy_is_not_sent_through_the_proxy(monkeypatch, net, transport):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY",))
    loopback = f"http://127.0.0.1:{net.target.port}"
    exc = send(transport, loopback, caller_client(loopback))
    net.nothing_sent()
    _coded_refusal(exc, KeyedProxyRefusedError, "KEYED_PROXY_REFUSED")


@TRANSPORTS
@SCHEMELESS
def test_schemeless_base_with_the_sdks_own_client_fails_before_any_connection(net, transport, base):
    exc = send(transport, base.format(authority=f"{HOST}:{net.target.port}"))
    net.nothing_sent()
    _schemeless_refusal(exc)


@TRANSPORTS
def test_bare_slash_base_is_rejected_when_the_client_is_built(net, transport):
    exc = send(transport, "/", caller_client(plain_base(net)))
    net.nothing_sent()
    _schemeless_refusal(exc)


@TRANSPORTS
@CALLER_BASES
def test_caller_in_process_transport_handles_absolute_and_network_path_bases(net, transport, base):
    seen: list[tuple[str, str, bool]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, str(request.url), request.headers.get("Authorization") == f"Bearer {KEY}"))
        return httpx.Response(200, json={"id": "c", "object": "chat.completion", "created": 0, "model": "m", "choices": []})

    exc = send_with_caller(transport, base, plain_base(net), transport=httpx.MockTransport(handler))
    net.nothing_sent()
    if base == PATH_ONLY:
        assert seen == []
        _schemeless_refusal(exc)
    else:
        assert exc is None, repr(exc)
        assert seen == [("POST", f"{plain_base(net)}/v1/chat/completions", True)]
