"""A plain-http request that carries a key or a token is sent direct by a client the SDK builds, and refused when a client
the caller supplies may route it through a proxy. A caller's transport counts as direct only when it is httpx's own
transport class over a plain connection pool, or exactly ``httpx.MockTransport`` (no network). A subclass of either may
route a request anywhere and is refused. The knowledge-base client sends direct whatever the proxy variables say, and
the gateway clients refuse a caller's client that is proxied. Marker keys are counted at loopback listeners."""

from __future__ import annotations

import asyncio
import os
from unittest import mock

import httpx
import pytest

import fi
import fi.gateway
from fi._core.http_security import httpx_client_proxied
from tests.core._plaintext_oracle import MARKER_KEY, MARKER_SECRET, PROXY_NAMES
from tests.core._plaintext_oracle import sinks  # noqa: F401  (the fixture)

GW_KEY = "sk-agentcc-" + MARKER_KEY


def _env(sinks_, **extra):
    clean = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    return {**clean, "FI_LOGIN_FILE": "/nonexistent/login.json", **extra}


def _proxy(sinks_):
    return f"http://127.0.0.1:{sinks_['sinkA'].port}"


def _reset(sinks_):
    for each in sinks_.values():
        each.reset()


def _ok(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"object": "list", "data": [], "status": True, "result": {}})


class SubMock(httpx.MockTransport):
    pass


class SubHTTP(httpx.HTTPTransport):
    pass


class SubAsyncHTTP(httpx.AsyncHTTPTransport):
    pass


def test_exactly_the_mock_transport_is_not_proxied():
    assert httpx_client_proxied(httpx.Client(transport=httpx.MockTransport(_ok)), "http://example.test/x") is False
    assert httpx_client_proxied(httpx.AsyncClient(transport=httpx.MockTransport(_ok)), "http://example.test/x") is False


@pytest.mark.parametrize("make", [
    lambda: httpx.Client(transport=SubMock(_ok)),
    lambda: httpx.AsyncClient(transport=SubMock(_ok)),
    lambda: httpx.Client(transport=SubHTTP()),
    lambda: httpx.AsyncClient(transport=SubAsyncHTTP()),
], ids=["mock-subclass", "async-mock-subclass", "http-subclass", "async-http-subclass"])
def test_a_subclass_of_a_transport_is_proxied(make):
    assert httpx_client_proxied(make(), "http://example.test/x") is True


def test_httpxs_own_transports_are_not_proxied():
    assert httpx_client_proxied(httpx.Client(trust_env=False), "http://example.test/x") is False
    assert httpx_client_proxied(httpx.AsyncClient(trust_env=False), "http://example.test/x") is False


def test_the_mock_gateway_client_works_on_a_plain_http_base_url():
    client = fi.gateway.create_mock_client(base_url="http://localhost:8080", responses={"/v1/models": {"object": "list", "data": []}})
    assert list(client.models.list().data) == []


def _gateway(transport, asynchronous):
    from fi.gateway import AgentCC, AsyncAgentCC

    if asynchronous:
        return AsyncAgentCC(api_key=GW_KEY, base_url="http://localhost:8080", max_retries=0, http_client=httpx.AsyncClient(transport=transport))
    return AgentCC(api_key=GW_KEY, base_url="http://localhost:8080", max_retries=0, http_client=httpx.Client(transport=transport))


def _call(client, asynchronous):
    if asynchronous:
        return asyncio.run(client.models.list())
    return client.models.list()


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_a_gateway_client_over_the_mock_transport_sends(asynchronous):
    assert list(_call(_gateway(httpx.MockTransport(_ok), asynchronous), asynchronous).data) == []


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("kind", ["mock-subclass", "http-subclass"])
def test_a_gateway_client_over_a_transport_subclass_is_refused(kind, asynchronous):
    transport = SubMock(_ok) if kind == "mock-subclass" else (SubAsyncHTTP() if asynchronous else SubHTTP())
    with pytest.raises(fi.KeyedProxyRefusedError):
        _call(_gateway(transport, asynchronous), asynchronous)


def _platform(transport, asynchronous, base="http://localhost:8080"):
    import fi.platform as fp

    if asynchronous:
        return fp.AsyncClient(api_key="k", secret_key="s", base_url=base, max_retries=0, http_client=httpx.AsyncClient(transport=transport))
    return fp.Client(api_key="k", secret_key="s", base_url=base, max_retries=0, http_client=httpx.Client(transport=transport))


def _platform_call(client, asynchronous):
    if asynchronous:
        async def go():
            async with client:
                return await client.request("GET", "/probe/")
        return asyncio.run(go())
    return client.request("GET", "/probe/")


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_a_platform_client_over_the_mock_transport_sends(asynchronous):
    assert _platform_call(_platform(httpx.MockTransport(_ok), asynchronous), asynchronous) is not None


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("kind", ["mock-subclass", "http-subclass"])
def test_a_platform_client_over_a_transport_subclass_is_refused(kind, asynchronous):
    transport = SubMock(_ok) if kind == "mock-subclass" else (SubAsyncHTTP() if asynchronous else SubHTTP())
    with pytest.raises(fi.KeyedProxyRefusedError):
        _platform_call(_platform(transport, asynchronous), asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("host", ["127.0.0.1", "localhost"])
def test_a_gateway_client_given_a_proxied_client_is_refused_before_a_byte(sinks, host, asynchronous):
    from fi.gateway import AgentCC, AsyncAgentCC

    _reset(sinks)
    base = f"http://{host}:{sinks['target'].port}"
    with mock.patch.dict(os.environ, _env(sinks), clear=True):
        if asynchronous:
            http = httpx.AsyncClient(proxy=_proxy(sinks))
            client = AsyncAgentCC(api_key=GW_KEY, base_url=base, max_retries=0, http_client=http)
        else:
            http = httpx.Client(proxy=_proxy(sinks))
            client = AgentCC(api_key=GW_KEY, base_url=base, max_retries=0, http_client=http)
        with pytest.raises(fi.KeyedProxyRefusedError) as info:
            _call(client, asynchronous)
    assert info.value.get_error_code() == "KEYED_PROXY_REFUSED"
    assert all(each.marker_bytes == 0 and each.requests == 0 for each in sinks.values())


@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("variable", ["HTTP_PROXY", "ALL_PROXY"])
def test_the_knowledge_base_sends_direct_whatever_the_proxy_variables_say(sinks, operation, variable):
    from fi.kb.client import KnowledgeBase
    from fi.kb.types import KnowledgeBaseConfig

    _reset(sinks)
    env = _env(sinks, FI_BASE_URL=f"http://127.0.0.1:{sinks['target'].port}", FI_API_KEY=MARKER_KEY, FI_SECRET_KEY=MARKER_SECRET,
               **{variable: _proxy(sinks)})
    with mock.patch.dict(os.environ, env, clear=True):
        kb = KnowledgeBase()
        try:
            if operation == "create":
                kb.create_kb("kb")
            else:
                kb.kb = KnowledgeBaseConfig(id="00000000-0000-0000-0000-0000000000d5", name="kb")
                kb.update_kb("kb", new_name="renamed")
        except fi.KeyedProxyRefusedError:
            pytest.fail("the knowledge-base client refused a request it sends direct")
        except Exception:
            pass  # the sink's body is not a knowledge-base answer
    assert sinks["target"].marker_bytes > 0
    assert sinks["sinkA"].marker_bytes == 0 and sinks["sinkA"].requests == 0
