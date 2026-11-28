"""The gateway clients (``AgentCC`` and ``AsyncAgentCC``) send a loopback gateway's requests straight to this
machine, so the API key is not handed to an environment proxy; a remote gateway keeps ``HTTP_PROXY`` /
``HTTPS_PROXY`` / ``ALL_PROXY`` and ``NO_PROXY``.

A remote host here is a made-up name the test resolves to a local server (the no-egress guard allows only loopback
addresses), so what the test checks is which listener got the request. The answer is not a gateway's, so the call
itself fails; only where it went is asserted.
"""

from __future__ import annotations

import asyncio
import warnings

import pytest

from tests.platform.test_env_proxy import REMOTE, _proxy_url, _Server, servers_fixture  # noqa: F401  (fixture)

MODES = [pytest.param(False, id="sync"), pytest.param(True, id="async")]


def _list_models(asynchronous: bool, base_url: str) -> None:
    from fi.gateway import AgentCC, AsyncAgentCC

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # an http:// remote gateway is warned about; that is not under test here
        if not asynchronous:
            client = AgentCC(api_key="sk-test-gateway-key", base_url=base_url, max_retries=0)
            try:
                client.models.list()
            except Exception:
                pass
            finally:
                client.close()
            return

        async def go() -> None:
            client = AsyncAgentCC(api_key="sk-test-gateway-key", base_url=base_url, max_retries=0)
            try:
                await client.models.list()
            except Exception:
                pass
            finally:
                await client.aclose()

        asyncio.run(go())


@pytest.mark.parametrize("asynchronous", MODES)
@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "[::1]"])
def test_a_loopback_gateway_skips_the_environment_proxy(servers, monkeypatch, asynchronous, host):
    proxy, sink = servers
    if host == "[::1]":
        try:
            sink = _Server("direct", host="::1")
        except OSError:
            pytest.skip("this machine has no IPv6 loopback")
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        monkeypatch.setenv(name, _proxy_url(proxy))
    _list_models(asynchronous, f"http://{host}:{sink.port}")
    assert proxy.requests == []
    assert len(sink.requests) >= 1
    assert sink.requests[0][2].get("authorization") == "Bearer sk-test-gateway-key"


@pytest.mark.parametrize("asynchronous", MODES)
def test_a_remote_plain_http_gateway_is_sent_direct_whatever_the_environment_proxy_says(servers, monkeypatch, asynchronous):
    proxy, sink = servers
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        monkeypatch.setenv(name, _proxy_url(proxy))
    _list_models(asynchronous, f"http://{REMOTE}:{sink.port}")
    assert proxy.requests == []
    assert len(sink.requests) >= 1


@pytest.mark.parametrize("asynchronous", MODES)
def test_no_proxy_leaves_a_remote_gateway_out_of_the_proxy(servers, monkeypatch, asynchronous):
    proxy, sink = servers
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        monkeypatch.setenv(name, _proxy_url(proxy))
    monkeypatch.setenv("NO_PROXY", REMOTE)
    _list_models(asynchronous, f"http://{REMOTE}:{sink.port}")
    assert proxy.requests == []
    assert len(sink.requests) >= 1


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost"])
def test_health_check_and_check_valid_key_send_a_loopback_gateway_s_key_directly(servers, monkeypatch, host):
    from fi.gateway import check_valid_key, health_check

    proxy, sink = servers
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        monkeypatch.setenv(name, _proxy_url(proxy))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        health_check(api_key="sk-test-gateway-key", base_url=f"http://{host}:{sink.port}")
        health_check(model="m", api_key="sk-test-gateway-key", base_url=f"http://{host}:{sink.port}")
        check_valid_key("sk-test-gateway-key", f"http://{host}:{sink.port}")
    assert proxy.requests == []
    assert [path for _, path, _ in sink.requests] == ["/healthz", "/v1/chat/completions", "/v1/models"]


def test_health_check_sends_a_remote_plain_http_gateway_direct_whatever_the_proxy_says(servers, monkeypatch):
    from fi.gateway import health_check

    proxy, sink = servers
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        monkeypatch.setenv(name, _proxy_url(proxy))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = health_check(api_key="sk-test-gateway-key", base_url=f"http://{REMOTE}:{sink.port}")
    assert "environment proxy" not in str(result.get("error"))
    assert proxy.requests == []
    assert len(sink.requests) >= 1


@pytest.fixture(autouse=True)
def _allow_plain_http_to_test_hosts(monkeypatch):
    """The tests in this module send to ``http://`` hosts that are not loopback, which needs the opt-in."""
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
