"""The error classes and codes a request that carries the API keys raises for a redirect and for a proxied plain-http send.

The published 0.7.1 raises ``KeyedRedirectRefusedError`` (``KEYED_REDIRECT_REFUSED``) when a request carrying the keys is
answered with a 3xx, and ``KeyedProxyRefusedError`` (``KEYED_PROXY_REFUSED``) when a plain-http key send would go through a
proxy. This line raises the same classes and codes at every site that refuses for those two reasons, importable from ``fi``,
``fi.errors`` and ``fi.utils.errors``, with no key text and no URL path or query in the message. Real loopback listeners only:
the redirect target and the proxy sink record what reaches them.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest

import fi
import fi.errors
import fi.utils.errors
from fi import AsyncFutureAGIClient
from fi._credentials import Credentials
from fi._http import LazyKeyAuth
from fi._sdk_exception import SDKException
from fi.futureagi_client import _adetailed
from fi.generated.openapi_client.api.annotation_queues import list_annotation_queues
from tests.core.test_caller_proxy_plain_http import KEY, SECRET, TARGET, ProxySink, opted_in, sink  # noqa: F401 (fixtures)
from tests.core.test_core_redirect import CALLS, KEYS, _client, pair  # noqa: F401 (fixtures)
from tests.test_extra_headers_integration import DS, logs, servers  # noqa: F401 (fixtures)

REDIRECT = "KEYED_REDIRECT_REFUSED"
PROXY = "KEYED_PROXY_REFUSED"


def _redirect_message_ok(error: BaseException, *secrets: str) -> None:
    assert type(error) is fi.KeyedRedirectRefusedError
    assert error.get_error_code() == REDIRECT
    for text in (str(error), repr(error)):
        for secret in ("k-redir", "s-redir", "ak-test", "sk-test", "/steal", "/landing", "?", *secrets):
            assert secret not in text


def test_the_classes_are_the_ones_0_7_1_publishes():
    for name, code in (("KeyedRedirectRefusedError", REDIRECT), ("KeyedProxyRefusedError", PROXY)):
        cls = getattr(fi, name)
        assert cls is getattr(fi.errors, name) is getattr(fi.utils.errors, name)
        assert issubclass(cls, SDKException) and issubclass(cls, fi.errors.FutureAGIError)
        assert cls().get_error_code() == code
    assert issubclass(fi.KeyedProxyRefusedError, fi.errors.ConfigurationError)
    assert fi.KeyedProxyRefusedError().code == PROXY
    assert fi.errors.UnexpectedRedirectError is fi.KeyedRedirectRefusedError


@pytest.mark.parametrize("path", sorted(CALLS))
def test_a_302_on_a_core_or_platform_call_is_the_keyed_redirect_error(pair, path):
    a, b, _ = pair
    client = _client(a)
    if path == "platform":
        from fi import FutureAGIClient
        from tests.core._support import OPS

        client = FutureAGIClient(**KEYS, base_url=f"http://127.0.0.1:{a.port}", platform_base_url=f"http://127.0.0.1:{a.port}/omega/api", retries=0)
        client._platform.shared.table = OPS
    with pytest.raises(fi.KeyedRedirectRefusedError) as info:
        CALLS[path](client)
    _redirect_message_ok(info.value)
    assert b.seen == []


def test_a_302_on_an_async_core_call_is_the_keyed_redirect_error(pair):
    a, b, _ = pair

    async def go() -> list[BaseException]:
        found: list[BaseException] = []
        async with AsyncFutureAGIClient(**KEYS, base_url=f"http://127.0.0.1:{a.port}", retries=0) as client:
            for call in (
                lambda: client.request("GET", "/model-hub/annotation-queues/"),
                lambda: _adetailed(list_annotation_queues.asyncio_detailed, client=client.generated_client),
            ):
                try:
                    await call()
                except BaseException as exc:  # noqa: BLE001 - the test inspects the class
                    found.append(exc)
        return found

    found = asyncio.run(go())
    assert len(found) == 2
    for error in found:
        _redirect_message_ok(error)
    assert b.seen == []


def test_the_session_client_follows_a_same_origin_302_and_refuses_another_port(servers, logs):
    from fi.api.auth import APIKeyAuth
    from fi.api.types import HttpMethod, RequestConfig

    platform, other = servers
    platform.route("/redir-same", 302, Location=f"{platform.url}/landed")
    platform.route("/landed", 200, {"landed": True})
    platform.route("/redir-off", 302, Location=f"{other.url}/landing?x=1")
    client = APIKeyAuth()
    try:
        response = client.request(RequestConfig(method=HttpMethod.GET, url=f"{platform.url}/redir-same", retry_attempts=1))
        assert response.status_code == 200 and response.json() == {"landed": True}
        with pytest.raises(fi.KeyedRedirectRefusedError) as info:
            client.request(RequestConfig(method=HttpMethod.GET, url=f"{platform.url}/redir-off", retry_attempts=1))
        _redirect_message_ok(info.value)
    finally:
        client.close()
    assert [(r["method"], r["path"]) for r in platform.requests] == [
        ("GET", "/redir-same"), ("GET", "/landed"), ("GET", "/redir-off"),
    ]
    for request in platform.requests[:2]:
        assert request["headers"]["x-api-key"] == "ak-test"
        assert request["headers"]["x-secret-key"] == "sk-test"
    assert other.seen("/landing") == []


def test_a_302_on_a_knowledge_base_upload_is_the_keyed_redirect_error(servers, logs):
    from fi.kb.client import KnowledgeBase
    from fi.kb.types import KnowledgeBaseConfig

    platform, other = servers
    platform.route("/model-hub/knowledge-base/", 302, Location=f"{other.url}/landing?x=1")
    with pytest.raises(fi.KeyedRedirectRefusedError) as info:
        KnowledgeBase().create_kb("kb")
    _redirect_message_ok(info.value)
    kb = KnowledgeBase()
    kb.kb = KnowledgeBaseConfig(id=DS, name="kb")
    with pytest.raises(fi.KeyedRedirectRefusedError) as info:
        kb.update_kb("kb", new_name="renamed")
    _redirect_message_ok(info.value)
    assert other.seen("/landing") == []


def _proxy_refusal_ok(error: BaseException, sink: ProxySink) -> None:
    assert type(error) is fi.KeyedProxyRefusedError
    assert isinstance(error, fi.errors.ConfigurationError) and isinstance(error, SDKException)
    assert error.code == PROXY and error.get_error_code() == PROXY
    for text in (str(error), repr(error)):
        assert KEY not in text and SECRET not in text and "/v1/x" not in text
    assert sink.received == [] and KEY.encode() not in sink.text and b"x-api-key" not in sink.text


def _auth(**kwargs):
    creds = Credentials(api_key=KEY, secret_key=SECRET, base_url=TARGET, keys_source="argument", base_url_source="argument")
    return LazyKeyAuth(lambda: creds, **kwargs)


def test_an_httpx_client_with_a_proxy_is_the_keyed_proxy_error(sink, opted_in):
    for build in (
        lambda: httpx.Client(proxy=sink.url, auth=_auth()),
        lambda: httpx.Client(mounts={"http://": httpx.HTTPTransport(proxy=httpx.Proxy(sink.url))}, auth=_auth()),
        lambda: httpx.Client(mounts={"http://app.example.test": httpx.HTTPTransport(proxy=httpx.Proxy(sink.url))}, auth=_auth()),
    ):
        with build() as client:
            with pytest.raises(fi.KeyedProxyRefusedError) as info:
                client.get(TARGET + "/v1/x")
        _proxy_refusal_ok(info.value, sink)


@pytest.mark.anyio
async def test_an_async_httpx_client_with_a_proxy_is_the_keyed_proxy_error(sink, opted_in):
    async with httpx.AsyncClient(proxy=sink.url, auth=_auth()) as client:
        with pytest.raises(fi.KeyedProxyRefusedError) as info:
            await client.get(TARGET + "/v1/x")
    _proxy_refusal_ok(info.value, sink)


def test_a_caller_requests_session_with_a_proxy_is_the_keyed_proxy_error(sink, opted_in, monkeypatch):
    import requests
    from requests_futures.sessions import FuturesSession

    from fi.api.auth import APIKeyAuth
    from fi.api.types import HttpMethod, RequestConfig

    monkeypatch.setenv("FI_BASE_URL", TARGET)
    monkeypatch.setenv("FI_API_KEY", KEY)
    monkeypatch.setenv("FI_SECRET_KEY", SECRET)
    for make in (
        lambda: _session(FuturesSession(), proxies={"http": sink.url}),
        lambda: _session(FuturesSession(), trust_env=True),
    ):
        session = make()
        if session.trust_env and not session.proxies:
            monkeypatch.setenv("HTTP_PROXY", sink.url)
        client = APIKeyAuth(session=session)
        try:
            with pytest.raises(fi.KeyedProxyRefusedError) as info:
                client.request(RequestConfig(method=HttpMethod.GET, url=TARGET + "/v1/x", retry_attempts=1))
        finally:
            client.close()
        _proxy_refusal_ok(info.value, sink)
        monkeypatch.delenv("HTTP_PROXY", raising=False)
    assert isinstance(requests.Session(), requests.Session)


def _session(session, proxies=None, trust_env=None):
    if proxies is not None:
        session.proxies.update(proxies)
    if trust_env is not None:
        session.trust_env = trust_env
    return session
