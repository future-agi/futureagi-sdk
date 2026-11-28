"""With FI_ALLOW_INSECURE_HTTP=1, a request that the caller's own client or session routes through a proxy is
refused before any credential header is written. The proxy here is a listener on 127.0.0.1 that records what it
receives; the target host is a reserved name no connection goes to."""

from __future__ import annotations

import socketserver
import threading

import httpx
import pytest

from fi._credentials import Credentials
from fi._http import LazyKeyAuth
from fi.errors import ConfigurationError

TARGET = "http://app.example.test"
KEY = "key-not-a-secret"
SECRET = "secret-not-a-secret"


class ProxySink:
    """A loopback listener that records each request it is sent and answers 502."""

    def __init__(self) -> None:
        sink = self
        self.received: list[bytes] = []

        class Handler(socketserver.BaseRequestHandler):
            def handle(self) -> None:
                self.request.settimeout(2)
                data = b""
                try:
                    while b"\r\n\r\n" not in data:
                        chunk = self.request.recv(65536)
                        if not chunk:
                            break
                        data += chunk
                except OSError:
                    pass
                sink.received.append(data)
                try:
                    self.request.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
                except OSError:
                    pass

        self.server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    @property
    def text(self) -> bytes:
        return b"".join(self.received).lower()


@pytest.fixture
def sink():
    s = ProxySink()
    yield s
    s.close()


@pytest.fixture(autouse=True)
def opted_in(monkeypatch):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    for name in ("NO_PROXY", "no_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.delenv(name, raising=False)


def _auth(**kwargs):
    creds = Credentials(api_key=KEY, secret_key=SECRET, base_url=TARGET, keys_source="argument", base_url_source="argument")
    return LazyKeyAuth(lambda: creds, **kwargs)


def _refused(error: pytest.ExceptionInfo) -> None:
    assert error.value.code == "KEYED_PROXY_REFUSED"
    text = str(error.value)
    assert "FI_ALLOW_INSECURE_HTTP" in text and "does not apply to a request routed through a proxy" in text
    assert KEY not in text and SECRET not in text


def _nothing_sent(sink: ProxySink) -> None:
    assert sink.received == []
    assert KEY.encode() not in sink.text and b"x-api-key" not in sink.text


def test_httpx_client_proxy_argument(sink):
    with httpx.Client(proxy=sink.url, auth=_auth()) as client:
        with pytest.raises(ConfigurationError) as error:
            client.get(TARGET + "/v1/x")
    _refused(error)
    _nothing_sent(sink)


def test_httpx_client_mounts_with_a_proxy_transport(sink):
    mounts = {"http://": httpx.HTTPTransport(proxy=httpx.Proxy(sink.url))}
    with httpx.Client(mounts=mounts, auth=_auth()) as client:
        with pytest.raises(ConfigurationError) as error:
            client.get(TARGET + "/v1/x")
    _refused(error)
    _nothing_sent(sink)


def test_httpx_client_proxy_for_one_host_only(sink):
    mounts = {"http://app.example.test": httpx.HTTPTransport(proxy=httpx.Proxy(sink.url))}
    with httpx.Client(mounts=mounts, auth=_auth()) as client:
        with pytest.raises(ConfigurationError) as error:
            client.get(TARGET + "/v1/x")
    _refused(error)
    _nothing_sent(sink)


@pytest.mark.anyio
async def test_httpx_async_client_proxy_argument(sink):
    async with httpx.AsyncClient(proxy=sink.url, auth=_auth()) as client:
        with pytest.raises(ConfigurationError) as error:
            await client.get(TARGET + "/v1/x")
    _refused(error)
    _nothing_sent(sink)


def test_httpx_client_without_a_proxy_sends_with_the_opt_in():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("x-api-key"))
        return httpx.Response(200)

    with httpx.Client(transport=httpx.MockTransport(handler), auth=_auth()) as client:
        assert client.get(TARGET + "/v1/x").status_code == 200
    assert seen == [KEY]


def test_httpx_client_proxy_for_another_scheme_does_not_apply(sink):
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("x-api-key"))
        return httpx.Response(200)

    mounts = {"https://": httpx.HTTPTransport(proxy=httpx.Proxy(sink.url)), "http://": httpx.MockTransport(handler)}
    with httpx.Client(mounts=mounts, auth=_auth()) as client:
        assert client.get(TARGET + "/v1/x").status_code == 200
    assert seen == [KEY] and sink.received == []


def test_a_proxy_does_not_matter_for_loopback(sink):
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("x-api-key"))
        return httpx.Response(200)

    mounts = {"http://": httpx.MockTransport(handler)}
    with httpx.Client(mounts=mounts, auth=_auth()) as client:
        assert client.get("http://127.0.0.1:9/v1/x").status_code == 200
    assert seen == [KEY]


def _platform_config(**kwargs):
    from fi.platform._transport import Config

    return Config(api_key=KEY, secret_key=SECRET, base_url=TARGET, timeout=2.0, max_retries=0, **kwargs)


def test_platform_client_with_a_caller_client_through_a_proxy(sink):
    from fi.platform._transport import SyncTransport

    transport = SyncTransport(_platform_config(), http_client=httpx.Client(proxy=sink.url))
    with pytest.raises(ConfigurationError) as error:
        transport.raw("GET", "/v1/x")
    _refused(error)
    _nothing_sent(sink)
    transport._http.close()


@pytest.mark.anyio
async def test_platform_async_client_with_a_caller_client_through_a_proxy(sink):
    from fi.platform._transport import AsyncTransport

    http = httpx.AsyncClient(proxy=sink.url)
    transport = AsyncTransport(_platform_config(), http_client=http)
    with pytest.raises(ConfigurationError) as error:
        await transport.raw("GET", "/v1/x")
    _refused(error)
    _nothing_sent(sink)
    await http.aclose()


def test_platform_client_with_a_caller_client_without_a_proxy():
    from fi.platform._transport import SyncTransport

    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("x-api-key"))
        return httpx.Response(200, json={"result": {}})

    transport = SyncTransport(_platform_config(), http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    transport.raw("GET", "/v1/x")
    assert seen == [KEY]


def _legacy(session):
    from fi.api.auth import APIKeyAuth

    return APIKeyAuth(fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=TARGET, session=session)


def _get(client, url):
    from fi.api.types import HttpMethod, RequestConfig

    return client.request(RequestConfig(method=HttpMethod.GET, url=url, retry_attempts=1, timeout=2))


def test_legacy_client_with_a_session_through_a_proxy(sink):
    from requests_futures.sessions import FuturesSession

    session = FuturesSession()
    session.proxies = {"http": sink.url}
    with pytest.raises(ConfigurationError) as error:
        _get(_legacy(session), TARGET + "/x")
    _refused(error)
    _nothing_sent(sink)


def test_legacy_client_with_a_session_proxy_for_all_schemes(sink):
    from requests_futures.sessions import FuturesSession

    session = FuturesSession()
    session.proxies = {"all": sink.url}
    with pytest.raises(ConfigurationError) as error:
        _get(_legacy(session), TARGET + "/x")
    _refused(error)
    _nothing_sent(sink)


def test_legacy_client_with_a_session_proxy_for_one_host(sink):
    from requests_futures.sessions import FuturesSession

    session = FuturesSession()
    session.proxies = {"http://app.example.test": sink.url}
    with pytest.raises(ConfigurationError) as error:
        _get(_legacy(session), TARGET + "/x")
    _refused(error)
    _nothing_sent(sink)


def test_legacy_client_with_a_session_proxy_for_another_scheme_sends():
    from types import SimpleNamespace

    calls = []

    class Session:
        proxies = {"https": "http://127.0.0.1:9"}

        def request(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(result=lambda: SimpleNamespace(status_code=200))

    _get(_legacy(Session()), TARGET + "/x")
    assert len(calls) == 1
