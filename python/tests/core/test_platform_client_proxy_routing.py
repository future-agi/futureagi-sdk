"""The platform client's default transport sends a literal loopback host (an address in 127.0.0.0/8, ``::1``, the name
``localhost``) straight to this machine and routes every other name, one that resolves to loopback included, by the
environment's proxy rules."""

from __future__ import annotations

import socket

import pytest

from tests.core._localhost_dial import Sink, proxy, resolver_shim, target  # noqa: F401
from tests.core.test_localhost_direct_dial import _client_async, _client_sync

SENDERS = {"sync": _client_sync, "async": _client_async}


def _proxy_env(sink: Sink) -> dict[str, str]:
    return {"HTTPS_PROXY": f"http://127.0.0.1:{sink.port}", "https_proxy": f"http://127.0.0.1:{sink.port}"}


def _send(kind: str, url: str) -> None:
    try:
        SENDERS[kind](url)
    except BaseException:  # the listener ends the exchange; only where the connection went is measured
        pass


@pytest.mark.parametrize("kind", SENDERS)
def test_a_name_that_resolves_to_loopback_goes_through_the_environment_proxy(kind, target, proxy):
    with resolver_shim(_proxy_env(proxy)):
        _send(kind, f"https://loop.test:{target.port}/")
    assert proxy.connections >= 1 and proxy.first_lines[0].startswith(b"CONNECT loop.test:"), proxy.first_lines
    assert target.connections == 0 and target.marker_bytes == 0 and proxy.marker_bytes == 0


@pytest.mark.parametrize("kind", SENDERS)
@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "LOCALHOST"])
def test_a_literal_loopback_host_goes_direct_with_an_environment_proxy(kind, host, target, proxy):
    with resolver_shim(_proxy_env(proxy)):
        _send(kind, f"https://{host}:{target.port}/")
    assert target.connections >= 1
    assert proxy.connections == 0 and proxy.marker_bytes == 0


@pytest.mark.parametrize("kind", SENDERS)
def test_the_ipv6_loopback_literal_goes_direct_with_an_environment_proxy(kind, proxy):
    try:
        listener = Sink(family=socket.AF_INET6)
    except OSError:
        pytest.skip("no IPv6 loopback on this machine")
    try:
        with resolver_shim(_proxy_env(proxy)):
            _send(kind, f"https://[::1]:{listener.port}/")
        assert listener.connections >= 1
        assert proxy.connections == 0 and proxy.marker_bytes == 0
    finally:
        listener.close()


@pytest.mark.parametrize("kind", SENDERS)
def test_a_proxy_setting_that_cannot_be_read_does_not_stop_a_direct_loopback_request(kind, target, proxy):
    env = {**_proxy_env(proxy), "NO_PROXY": ".::1"}
    with resolver_shim(env):
        _send(kind, f"https://127.0.0.1:{target.port}/")
    assert target.connections >= 1 and proxy.connections == 0
