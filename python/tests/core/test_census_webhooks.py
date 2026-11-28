"""The webhooks clients send their keys under the plain-http rules: a host that is not loopback is refused before a connection,
a loopback host is reached directly, and an environment proxy receives nothing."""

import asyncio

import pytest

from fi.webhooks import AsyncWebhooks, Webhooks
from tests.experiments.unit.test_header_key_senders import MARKER, proxied, remote, rig  # noqa: F401  (fixture)
from tests.experiments.unit.oracle_probe import SECRET


def sync_call(base):
    with Webhooks(MARKER, SECRET.decode(), base_url=base, retries=0, timeout=3) as client:
        client.endpoints.list()


def async_call(base):
    async def run():
        async with AsyncWebhooks(MARKER, SECRET.decode(), base_url=base, retries=0, timeout=3) as client:
            await client.endpoints.list()

    asyncio.run(run())


CALLS = {"Webhooks": sync_call, "AsyncWebhooks": async_call}


def attempt(call, base):
    try:
        call(base)
    except Exception as error:  # noqa: BLE001 - the listener's reply is not an API answer
        return error
    return None


@pytest.mark.parametrize("name", list(CALLS))
def test_a_non_loopback_host_is_refused_before_a_connection(rig, monkeypatch, name):
    proxied(rig, monkeypatch)
    error = attempt(CALLS[name], remote(rig.target))
    assert error is not None
    assert rig.connections() == 0 and rig.bytes() == 0, error


@pytest.mark.parametrize("name", list(CALLS))
def test_the_opt_in_with_an_environment_proxy_is_sent_directly(rig, monkeypatch, name):
    proxied(rig, monkeypatch)
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    attempt(CALLS[name], remote(rig.target))
    assert rig.proxy.connections == 0 and rig.proxy.marker_bytes == 0
    assert rig.target.marker_bytes > 0


@pytest.mark.parametrize("name", list(CALLS))
def test_a_loopback_host_is_sent_directly_with_an_environment_proxy(rig, monkeypatch, name):
    proxied(rig, monkeypatch)
    attempt(CALLS[name], f"http://localhost:{rig.target.port}")
    assert rig.proxy.connections == 0 and rig.proxy.marker_bytes == 0
    assert rig.target.marker_bytes > 0
