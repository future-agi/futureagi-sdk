"""A redirect to another origin (scheme, host or port) carries no Cookie and no auth header, for each Python sender.

Real loopback sockets. The first origin answers 302 or 307 to a second origin: another host (127.0.0.2 on the same
port), another port, or plain http on the same host and port as an https first origin (one listener serves both and
reads the first byte to tell TLS from plain http). The second origin records the raw bytes of every request. The
caller sets marker values for ``Cookie`` (as a header and in a cookie jar where the sender takes one),
``Authorization``, ``X-Api-Key`` and ``X-Secret-Key``; the second origin holds 0 bytes of any marker. A sender that
follows across origins reaches the second origin (one request there, so the sink is shown to receive bytes).
A sender that refuses the cross-origin redirect raises on the 3xx and the second origin sees 0 connections.
The keyed API and platform clients follow a same-origin redirect with their keys.
"""

from __future__ import annotations

import asyncio
import ssl
from typing import Any, Callable

import pytest

from tests.core.redirect_sinks import _Listener, _markers, _tls_files

STATUSES = (302, 307)
CELLS = ("other-host", "other-port", "https-to-http")


# Each sender: (follows redirects, send(url, markers)). ``send`` makes one request to ``url`` (``.../start``) the way
# the sender's real construction sends it, with every marker the sender takes.


def _api_key_auth(url: str, m: dict[str, str]) -> None:
    from fi.api.auth import APIKeyAuth
    from fi.api.types import HttpMethod, RequestConfig

    origin = url.rsplit("/", 1)[0]
    client = APIKeyAuth(
        fi_api_key=m["x-api-key"], fi_secret_key=m["x-secret-key"], fi_base_url=origin,
        default_headers={"Cookie": f"c={m['cookie-header']}", "Authorization": f"Bearer {m['authorization']}"},
    )
    client._session.cookies.set("sid", m["cookie-jar"])
    try:
        client.request(RequestConfig(method=HttpMethod.GET, url=url, retry_attempts=1))
    finally:
        client.close()


def _kb_direct_upload(url: str, m: dict[str, str]) -> None:
    from fi.api.auth import APIKeyAuth
    from fi.kb.client import _send_direct

    origin = url.rsplit("/", 1)[0]
    client = APIKeyAuth(fi_api_key=m["x-api-key"], fi_secret_key=m["x-secret-key"], fi_base_url=origin)
    headers = {**client._default_headers, "Cookie": f"c={m['cookie-header']}", "Authorization": m["authorization"]}
    response = _send_direct("POST", client._direct_kwargs({"url": url, "headers": headers, "data": {"a": "b"}}))
    client.close()
    from fi.api.auth import refuse_redirect

    refuse_redirect(response)


def _session_keyed(url: str, m: dict[str, str]) -> None:
    from fi._core.requests_session import LoopbackDirectSession

    with LoopbackDirectSession() as session:
        session.cookies.set("sid", m["cookie-jar"])
        session.get(url, timeout=10, headers={
            "Cookie": f"c={m['cookie-header']}", "Authorization": m["authorization"],
            "X-Api-Key": m["x-api-key"], "X-Secret-Key": m["x-secret-key"],
        })


def _session_cookie_only(url: str, m: dict[str, str]) -> None:
    from fi._core.requests_session import LoopbackDirectSession

    with LoopbackDirectSession() as session:
        session.cookies.set("sid", m["cookie-jar"])
        session.get(url, timeout=10, headers={"Cookie": f"c={m['cookie-header']}"}).raise_for_status()


def _session_cookie_jar_only(url: str, m: dict[str, str]) -> None:
    from fi._core.requests_session import LoopbackDirectSession

    with LoopbackDirectSession() as session:
        session.cookies.set("sid", m["cookie-jar"])
        session.get(url, timeout=10).raise_for_status()


def _platform_headers(m: dict[str, str]) -> dict[str, str]:
    return {"Cookie": f"c={m['cookie-header']}", "Authorization": f"Bearer {m['authorization']}"}


def _platform_sync(url: str, m: dict[str, str]) -> None:
    from fi.platform import Client

    origin = url.rsplit("/", 1)[0]
    with Client(api_key=m["x-api-key"], secret_key=m["x-secret-key"], base_url=origin, max_retries=0,
                default_headers=_platform_headers(m)) as client:
        client.request("GET", "/start")


def _platform_async(url: str, m: dict[str, str]) -> None:
    from fi.platform import AsyncClient

    async def run() -> None:
        client = AsyncClient(api_key=m["x-api-key"], secret_key=m["x-secret-key"], base_url=url.rsplit("/", 1)[0],
                             max_retries=0, default_headers=_platform_headers(m))
        try:
            await client.request("GET", "/start")
        finally:
            await client.aclose()

    asyncio.run(run())


def _gateway_headers(m: dict[str, str]) -> dict[str, str]:
    return {"Cookie": f"c={m['cookie-header']}", "X-Api-Key": m["x-api-key"], "X-Secret-Key": m["x-secret-key"]}


def _gateway_sync(url: str, m: dict[str, str]) -> None:
    from fi.gateway import AgentCC

    client = AgentCC(api_key=m["authorization"], base_url=url.rsplit("/", 1)[0] + "/start", max_retries=0,
                     default_headers=_gateway_headers(m))
    try:
        client.models.list()
    finally:
        client.close()


def _gateway_async(url: str, m: dict[str, str]) -> None:
    from fi.gateway import AsyncAgentCC

    async def run() -> None:
        client = AsyncAgentCC(api_key=m["authorization"], base_url=url.rsplit("/", 1)[0] + "/start", max_retries=0,
                              default_headers=_gateway_headers(m))
        try:
            await client.models.list()
        finally:
            await client.aclose()

    asyncio.run(run())


def _core_headers(m: dict[str, str]) -> dict[str, str]:
    return {"Cookie": f"c={m['cookie-header']}", "Authorization": f"Bearer {m['authorization']}"}


def _futureagi_sync(url: str, m: dict[str, str]) -> None:
    from fi import FutureAGIClient

    origin = url.rsplit("/", 1)[0]
    with FutureAGIClient(api_key=m["x-api-key"], secret_key=m["x-secret-key"], base_url=origin, retries=0,
                         headers=_core_headers(m)) as client:
        client.users.current()


def _futureagi_async(url: str, m: dict[str, str]) -> None:
    from fi import AsyncFutureAGIClient
    from fi.futureagi_client import _adetailed
    from fi.generated.openapi_client.api.annotation_queues import list_annotation_queues

    async def run() -> None:
        client = AsyncFutureAGIClient(api_key=m["x-api-key"], secret_key=m["x-secret-key"],
                                      base_url=url.rsplit("/", 1)[0], retries=0, headers=_core_headers(m))
        async with client.generated_client.get_async_httpx_client():
            await _adetailed(list_annotation_queues.asyncio_detailed, client=client.generated_client)

    asyncio.run(run())


def _generated(m: dict[str, str], **kwargs: Any) -> Any:
    from fi.generated.openapi_client import AuthenticatedClient

    return AuthenticatedClient(
        token=m["authorization"], follow_redirects=True, cookies={"sid": m["cookie-jar"]},
        headers={"Cookie": f"c={m['cookie-header']}", "X-Api-Key": m["x-api-key"], "X-Secret-Key": m["x-secret-key"]},
        **kwargs,
    )


def _generated_sync(url: str, m: dict[str, str]) -> None:
    with _generated(m, base_url=url.rsplit("/", 1)[0]).get_httpx_client() as http:
        http.get("/start").raise_for_status()


def _generated_sync_key_header(url: str, m: dict[str, str]) -> None:
    client = _generated(m, base_url=url.rsplit("/", 1)[0], auth_header_name="X-Api-Key", prefix="")
    with client.get_httpx_client() as http:
        http.get("/start", headers={"Authorization": f"Bearer {m['authorization']}"}).raise_for_status()


def _generated_async(url: str, m: dict[str, str]) -> None:
    async def run() -> None:
        async with _generated(m, base_url=url.rsplit("/", 1)[0]).get_async_httpx_client() as http:
            (await http.get("/start")).raise_for_status()

    asyncio.run(run())


def _plain(m: dict[str, str], base_url: str, lower: bool, transport: Any) -> Any:
    """The generated unauthenticated ``Client`` with every marker in the caller's ``headers`` (title case or lower case
    names) and ``cookies=``; plain http goes direct as the SDK's own clients send it, so the loopback proxy variables
    of the test run do not take the second origin."""
    from fi.generated.openapi_client import Client

    headers = {
        "Cookie": f"c={m['cookie-header']}", "Authorization": f"Bearer {m['authorization']}",
        "X-Api-Key": m["x-api-key"], "X-Secret-Key": m["x-secret-key"],
    }
    return Client(
        base_url=base_url, follow_redirects=True, cookies={"sid": m["cookie-jar"]},
        headers={name.lower() if lower else name: value for name, value in headers.items()},
        httpx_args={"mounts": {"http://": transport()}},
    )


def _plain_sync(lower: bool) -> Callable[[str, dict[str, str]], None]:
    def send(url: str, m: dict[str, str]) -> None:
        import httpx

        with _plain(m, url.rsplit("/", 1)[0], lower, httpx.HTTPTransport).get_httpx_client() as http:
            http.get("/start").raise_for_status()

    return send


def _plain_async(lower: bool) -> Callable[[str, dict[str, str]], None]:
    def send(url: str, m: dict[str, str]) -> None:
        import httpx

        async def run() -> None:
            client = _plain(m, url.rsplit("/", 1)[0], lower, httpx.AsyncHTTPTransport)
            async with client.get_async_httpx_client() as http:
                (await http.get("/start")).raise_for_status()

        asyncio.run(run())

    return send


SENDERS: dict[str, tuple[bool, Callable[[str, dict[str, str]], None]]] = {
    "fi.api-APIKeyAuth": (False, _api_key_auth),
    "fi.kb-direct-upload": (False, _kb_direct_upload),
    "LoopbackDirectSession-keyed": (False, _session_keyed),
    "LoopbackDirectSession-cookie-header-and-jar": (True, _session_cookie_only),
    "LoopbackDirectSession-cookie-jar": (True, _session_cookie_jar_only),
    "fi.platform.Client": (False, _platform_sync),
    "fi.platform.AsyncClient": (False, _platform_async),
    "fi.gateway.AgentCC": (False, _gateway_sync),
    "fi.gateway.AsyncAgentCC": (False, _gateway_async),
    "FutureAGIClient": (False, _futureagi_sync),
    "AsyncFutureAGIClient": (False, _futureagi_async),
    "generated-AuthenticatedClient-sync": (True, _generated_sync),
    "generated-AuthenticatedClient-sync-key-header": (True, _generated_sync_key_header),
    "generated-AuthenticatedClient-async": (True, _generated_async),
    "generated-Client-sync": (True, _plain_sync(lower=False)),
    "generated-Client-sync-lowercase-names": (True, _plain_sync(lower=True)),
    "generated-Client-async": (True, _plain_async(lower=False)),
    "generated-Client-async-lowercase-names": (True, _plain_async(lower=True)),
}


@pytest.fixture
def tls_context(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> ssl.SSLContext | None:
    files = _tls_files(tmp_path)
    if files is None:
        return None
    cert_file, key_file = files
    # httpx and requests trust the test certificate through their environment settings.
    monkeypatch.setenv("SSL_CERT_FILE", cert_file)
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", cert_file)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_file, key_file)
    return context


def _origins(cell: str, status: int, tls: ssl.SSLContext | None) -> tuple[str, list[_Listener], Callable[[], bytes]]:
    """The start URL, the listeners, and a reader of every byte the second origin received."""
    if cell == "https-to-http":
        if tls is None:
            pytest.skip("neither the cryptography package nor the openssl command is here to make a certificate")
        first = _Listener("127.0.0.1", tls=tls)
        first.redirect = ("https", status, f"http://127.0.0.1:{first.port}/done")
        return f"https://127.0.0.1:{first.port}/start", [first], (
            lambda: b"".join(raw for scheme, raw in first.records if scheme == "http")
        )
    first = _Listener("127.0.0.1")
    if cell == "other-host":
        try:
            second = _Listener("127.0.0.2", first.port)
        except OSError:
            pytest.skip("127.0.0.2 cannot listen on the port of the first origin here")
    elif cell == "other-port":
        second = _Listener("127.0.0.1")
    else:
        second = None
    target = second or first
    first.redirect = ("http", status, f"http://{target.host}:{target.port}/done")
    if second is None:
        return f"http://127.0.0.1:{first.port}/start", [first], lambda: b""
    return f"http://127.0.0.1:{first.port}/start", [first, second], lambda: b"".join(r for _, r in second.records)


def _second_origin_requests(cell: str, listeners: list[_Listener]) -> int:
    if cell == "https-to-http":
        return sum(1 for scheme, _ in listeners[0].records if scheme == "http")
    return len(listeners[1].records)


@pytest.mark.parametrize("status", STATUSES, ids=lambda status: str(status))
@pytest.mark.parametrize("cell", CELLS)
@pytest.mark.parametrize("sender", list(SENDERS))
def test_cross_origin_redirect_carries_no_cookie_or_auth_header(
    sender: str, cell: str, status: int, tls_context: ssl.SSLContext | None
) -> None:
    follows, send = SENDERS[sender]
    markers = _markers()
    url, listeners, second_bytes = _origins(cell, status, tls_context)
    error: BaseException | None = None
    try:
        send(url, markers)
    except Exception as caught:  # noqa: BLE001 - the 3xx refusal of a sender that does not follow
        error = caught
    finally:
        for listener in listeners:
            listener.close()
    raw = second_bytes()
    found = {name: raw.count(value.encode()) * len(value) for name, value in markers.items() if value.encode() in raw}
    assert sum(found.values()) == 0, f"{sum(found.values())} marker bytes at the second origin: {found}"
    first_requests = sum(1 for scheme, _ in listeners[0].records if scheme == url.split(":")[0])
    assert first_requests == 1, f"the first origin saw {first_requests} requests"
    if follows:
        assert error is None, repr(error)
        assert _second_origin_requests(cell, listeners) == 1 and raw, "the redirect did not reach the second origin"
    else:
        assert error is not None and "redirect" in f"{type(error).__name__} {error}".lower(), repr(error)
        assert _second_origin_requests(cell, listeners) == 0 and raw == b""


SAME_ORIGIN_KEYED_SENDERS = {"fi.api-APIKeyAuth", "fi.platform.Client", "fi.platform.AsyncClient"}


@pytest.mark.parametrize("sender", list(SENDERS))
def test_same_origin_redirect_is_delivered_or_refused(sender: str, tls_context: ssl.SSLContext | None) -> None:
    follows_cross_origin, send = SENDERS[sender]
    markers = _markers()
    url, listeners, _ = _origins("same-origin", 307, tls_context)
    error: BaseException | None = None
    try:
        send(url, markers)
    except Exception as caught:  # noqa: BLE001 - the 3xx refusal of a sender that does not follow
        error = caught
    finally:
        listeners[0].close()
    records = [raw for _, raw in listeners[0].records]
    assert records and any(value.encode() in records[0] for value in markers.values()), "the first origin saw no marker"
    if sender in SAME_ORIGIN_KEYED_SENDERS:
        assert error is None, repr(error)
        assert [raw.split(b"\r\n", 1)[0] for raw in records] == [b"GET /start HTTP/1.1", b"GET /done HTTP/1.1"]
        for raw in records:
            lines = raw.split(b"\r\n\r\n", 1)[0].split(b"\r\n")[1:]
            headers = {name.lower(): value.strip() for name, _, value in (line.partition(b":") for line in lines)}
            assert headers[b"x-api-key"] == markers["x-api-key"].encode()
            assert headers[b"x-secret-key"] == markers["x-secret-key"].encode()
    elif follows_cross_origin:
        assert error is None, repr(error)
        assert len(records) == 2 and b"/done" in records[1].split(b"\r\n", 1)[0]
    else:
        assert error is not None and "redirect" in f"{type(error).__name__} {error}".lower(), repr(error)
        assert len(records) == 1
