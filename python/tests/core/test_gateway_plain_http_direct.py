"""A gateway client the SDK builds sends a plain-http request direct, whatever the proxy variables say, for a loopback host and
for a host that is not loopback and opted into with ``FI_ALLOW_INSECURE_HTTP=1``; the key reaches the gateway and not the
proxy. The utility calls (``check_valid_key``, ``health_check``) send the same way."""

from __future__ import annotations

import asyncio
import os
from unittest import mock

import pytest

from tests.core._plaintext_oracle import MARKER_KEY, PROXY_NAMES
from tests.core._plaintext_oracle import sinks  # noqa: F401  (the fixture)
from tests.core.test_sender_rules import resolver  # noqa: F401  (the fixture)

GW_KEY = "sk-agentcc-" + MARKER_KEY
HOSTS = ["127.0.0.1", "remote-gateway.test"]


def _env(sinks_, **extra):
    clean = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    return {**clean, "FI_ALLOW_INSECURE_HTTP": "1", "HTTP_PROXY": f"http://127.0.0.1:{sinks_['sinkA'].port}", **extra}


def _assert_direct(sinks_):
    assert sinks_["target"].marker_bytes > 0
    assert sinks_["sinkA"].marker_bytes == 0 and sinks_["sinkA"].requests == 0


@pytest.mark.parametrize("host", HOSTS)
def test_a_gateway_client_sends_plain_http_direct(sinks, resolver, host):
    from fi.gateway import AgentCC

    for each in sinks.values():
        each.reset()
    with mock.patch.dict(os.environ, _env(sinks), clear=True):
        client = AgentCC(api_key=GW_KEY, base_url=f"http://{host}:{sinks['target'].port}", max_retries=0)
        try:
            client.models.list()
        except Exception as error:  # the sink's body is not a model list
            assert type(error).__name__ in ("ValidationError", "APIStatusError"), error
        finally:
            client.close()
    _assert_direct(sinks)


@pytest.mark.parametrize("host", HOSTS)
def test_an_async_gateway_client_sends_plain_http_direct(sinks, resolver, host):
    from fi.gateway import AsyncAgentCC

    for each in sinks.values():
        each.reset()

    async def go():
        client = AsyncAgentCC(api_key=GW_KEY, base_url=f"http://{host}:{sinks['target'].port}", max_retries=0)
        try:
            await client.models.list()
        except Exception as error:
            assert type(error).__name__ in ("ValidationError", "APIStatusError"), error
        finally:
            await client.aclose()

    with mock.patch.dict(os.environ, _env(sinks), clear=True):
        asyncio.run(go())
    _assert_direct(sinks)


@pytest.mark.parametrize("host", HOSTS)
def test_the_gateway_utility_calls_send_plain_http_direct(sinks, resolver, host):
    from fi.gateway._utils import check_valid_key, health_check

    for each in sinks.values():
        each.reset()
    base = f"http://{host}:{sinks['target'].port}"
    with mock.patch.dict(os.environ, _env(sinks), clear=True):
        assert check_valid_key(GW_KEY, base) is True
        assert health_check(api_key=GW_KEY, base_url=base)["status"] == "ok"
    _assert_direct(sinks)
