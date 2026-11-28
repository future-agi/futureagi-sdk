"""Platform calls honour ``HTTP_PROXY`` / ``HTTPS_PROXY`` / ``ALL_PROXY`` and ``NO_PROXY`` for a remote host,
as the TypeScript client does, and loopback requests bypass proxies.

The transport is built by ``PlatformShared`` (``fi._core.transport``): every client's calls, sync and async, go
through ``http()`` / ``ahttp()``. A remote host here is a made-up name that the test resolves to a local server
(the no-egress guard allows only loopback addresses), so what the test checks is which listener got the request.
"""

from __future__ import annotations

import base64
import logging
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest
from fi._core.transport import PlatformShared

REMOTE = "remote-platform.test"
PASSWORD = "proxy-pass-not-a-secret"
PROXY_ENV = ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy")


class _Server:
    """A local HTTP server that records each request and answers with its own name."""

    def __init__(self, name: str, host: str = "127.0.0.1"):
        self.name = name
        self.requests: list[tuple[str, str, dict[str, str]]] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def _answer(self):
                outer.requests.append((self.command, self.path, {k.lower(): v for k, v in self.headers.items()}))
                body = outer.name.encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            do_GET = do_POST = _answer

            def do_CONNECT(self):
                outer.requests.append((self.command, self.path, {k.lower(): v for k, v in self.headers.items()}))
                self.send_response(502)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *args):
                pass

        server_class = ThreadingHTTPServer
        if ":" in host:
            server_class = type("V6Server", (ThreadingHTTPServer,), {"address_family": socket.AF_INET6})
        self._http = server_class((host, 0), Handler)
        self.port = self._http.server_address[1]
        threading.Thread(target=self._http.serve_forever, daemon=True).start()

    def close(self):
        self._http.shutdown()
        self._http.server_close()


@pytest.fixture(name="servers")
def servers_fixture(monkeypatch):
    for name in PROXY_ENV:
        monkeypatch.delenv(name, raising=False)
    proxy, sink = _Server("proxy"), _Server("direct")
    real = socket.getaddrinfo

    def resolve(host, *args, **kwargs):
        name = host.decode() if isinstance(host, bytes) else host
        return real("127.0.0.1" if name in (REMOTE, "localhost.", "not-localhost.test") else host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    yield proxy, sink
    proxy.close()
    sink.close()


def _proxy_url(proxy, auth=f"user:{PASSWORD}@"):
    return f"http://{auth}127.0.0.1:{proxy.port}"


def _shared():
    return PlatformShared(lambda: None, retries=0)


def _get(asynchronous, url):
    shared = _shared()
    if not asynchronous:
        try:
            return shared.http().get(url)
        finally:
            shared.close()

    import asyncio

    async def go():
        try:
            return await shared.ahttp().get(url)
        finally:
            await shared.aclose()

    return asyncio.run(go())


MODES = pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])


@MODES
@pytest.mark.parametrize("variable", ["HTTP_PROXY", "ALL_PROXY"])
def test_a_remote_call_goes_through_the_environment_proxy(servers, monkeypatch, asynchronous, variable):
    proxy, sink = servers
    monkeypatch.setenv(variable, _proxy_url(proxy))
    response = _get(asynchronous, f"http://{REMOTE}:{sink.port}/omega/api/ping")
    assert response.text == "proxy"
    assert [r[1] for r in proxy.requests] == [f"http://{REMOTE}:{sink.port}/omega/api/ping"]
    assert sink.requests == []


@MODES
def test_the_proxy_credentials_in_the_url_are_sent_and_not_logged(servers, monkeypatch, caplog, capsys, asynchronous):
    proxy, sink = servers
    monkeypatch.setenv("HTTP_PROXY", _proxy_url(proxy))
    with caplog.at_level(logging.DEBUG):
        _get(asynchronous, f"http://{REMOTE}:{sink.port}/x")
    sent = proxy.requests[0][2]["proxy-authorization"]
    assert base64.b64decode(sent.split()[1]).decode() == f"user:{PASSWORD}"
    out = capsys.readouterr()
    assert PASSWORD not in caplog.text and PASSWORD not in out.out and PASSWORD not in out.err
    assert sink.requests == []


@MODES
def test_a_failed_proxy_call_does_not_put_the_password_in_the_error(servers, monkeypatch, asynchronous):
    proxy, _ = servers
    monkeypatch.setenv("HTTPS_PROXY", _proxy_url(proxy))
    with pytest.raises(httpx.HTTPError) as caught:
        _get(asynchronous, f"https://{REMOTE}/omega/api/ping")  # the fake proxy refuses the CONNECT
    assert [r[0] for r in proxy.requests] == ["CONNECT"]
    assert PASSWORD not in str(caught.value) and PASSWORD not in repr(caught.value)


@MODES
@pytest.mark.parametrize("variable", ["NO_PROXY", "no_proxy"])
def test_no_proxy_names_a_host_that_then_goes_direct(servers, monkeypatch, asynchronous, variable):
    proxy, sink = servers
    monkeypatch.setenv("HTTP_PROXY", _proxy_url(proxy))
    monkeypatch.setenv(variable, REMOTE)
    response = _get(asynchronous, f"http://{REMOTE}:{sink.port}/x")
    assert response.text == "direct"
    assert proxy.requests == []


@MODES
@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "[::1]"])
def test_a_loopback_call_goes_direct_with_no_proxy_bytes(servers, monkeypatch, asynchronous, host):
    proxy, sink = servers
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        monkeypatch.setenv(name, _proxy_url(proxy))
    if host == "[::1]":
        try:
            sink = _Server("direct", "::1")
        except OSError:
            pytest.skip("no IPv6 loopback here")
    response = _get(asynchronous, f"http://{host}:{sink.port}/x")
    assert response.text == "direct"
    assert proxy.requests == []


@MODES
@pytest.mark.parametrize("host", ["localhost.", "not-localhost.test"])
def test_a_name_that_only_looks_like_loopback_is_proxied(servers, monkeypatch, asynchronous, host):
    proxy, sink = servers
    monkeypatch.setenv("HTTP_PROXY", _proxy_url(proxy))
    response = _get(asynchronous, f"http://{host}:{sink.port}/x")  # not the exact name `localhost`
    assert response.text == "proxy"


def test_without_a_proxy_in_the_environment_a_remote_call_goes_direct(servers):
    proxy, sink = servers
    assert _get(False, f"http://{REMOTE}:{sink.port}/x").text == "direct"
    assert proxy.requests == []


@MODES
@pytest.mark.parametrize("variable", ["HTTP_PROXY", "ALL_PROXY"])
def test_plain_http_that_carries_keys_goes_direct_through_the_shared_transport(servers, monkeypatch, asynchronous, variable):
    """The transport the SDK builds sends a plain ``http://`` request that carries keys straight to its host (such a
    request reaches it only with the opt-in); a request without keys keeps the environment proxy."""
    proxy, sink = servers
    monkeypatch.setenv(variable, _proxy_url(proxy))
    shared = _shared()
    try:
        if asynchronous:
            import asyncio

            async def go():
                return await shared.ahttp().get(f"http://{REMOTE}:{sink.port}/k", headers={"X-Api-Key": "k-not-a-secret"})

            response = asyncio.run(go())
        else:
            response = shared.http().get(f"http://{REMOTE}:{sink.port}/k", headers={"X-Api-Key": "k-not-a-secret"})
    finally:
        shared.close() if not asynchronous else None
    assert response.text == "direct"
    assert proxy.requests == []


def test_the_session_the_sdk_builds_sends_plain_http_with_keys_direct_and_other_requests_by_the_environment(servers, monkeypatch):
    from fi._core.requests_session import LoopbackDirectSession

    proxy, sink = servers
    monkeypatch.setenv("HTTP_PROXY", _proxy_url(proxy))
    with LoopbackDirectSession() as session:
        keyed = session.get(f"http://{REMOTE}:{sink.port}/k", headers={"X-Api-Key": "k-not-a-secret"}, timeout=5)
        assert keyed.text == "direct" and proxy.requests == []
        plain = session.get(f"http://{REMOTE}:{sink.port}/p", timeout=5)
        assert plain.text == "proxy" and [path for _, path, _ in proxy.requests][-1].endswith("/p")
