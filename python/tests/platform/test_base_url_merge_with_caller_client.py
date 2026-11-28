"""Platform base URL merging with caller-owned HTTPX clients.

Both named hosts resolve to loopback through the shared lookup shim.
Separate target and proxy listeners record HTTP requests and CONNECT handshakes.
"""
# ruff: noqa: F811

from __future__ import annotations

import pytest
from fi.errors import (
    ConfigurationError,
    InsecureHttpRefusedError,
    KeyedProxyRefusedError,
)
from fi.platform import APIConnectionError

from tests.platform.test_sent_url_judgement import (
    TRANSPORTS,
    _coded_refusal,
    caller_client,
    send,
)
from tests.test_plain_http_key_guards import CODE, net, use_proxy  # noqa: F401

PLAIN_HOST = "plain.example.test"
FUTURE_AGI_HOST = "api.futureagi.com"
HOST_REFUSALS = pytest.mark.parametrize(
    ("host", "error", "code"),
    [
        pytest.param(PLAIN_HOST, ConfigurationError, CODE, id="plain-host"),
        pytest.param(FUTURE_AGI_HOST, InsecureHttpRefusedError, "INSECURE_HTTP_REFUSED", id="future-agi-host"),
    ],
)


@TRANSPORTS
@HOST_REFUSALS
def test_root_with_caller_http_base_and_environment_proxy_is_refused(monkeypatch, net, transport, host, error, code):
    use_proxy(monkeypatch, net)
    exc = send(transport, "/", caller_client(f"http://{host}:{net.target.port}"))
    net.nothing_sent()
    _coded_refusal(exc, error, code)


@TRANSPORTS
@HOST_REFUSALS
def test_root_with_caller_http_base_and_no_proxy_is_refused(net, transport, host, error, code):
    exc = send(transport, "/", caller_client(f"http://{host}:{net.target.port}", trust_env=False))
    net.nothing_sent()
    _coded_refusal(exc, error, code)


@TRANSPORTS
def test_network_path_with_opt_in_and_environment_proxy_is_refused(monkeypatch, net, transport):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    use_proxy(monkeypatch, net)
    authority = f"{PLAIN_HOST}:{net.target.port}"
    exc = send(transport, f"//{authority}", caller_client(f"http://{authority}"))
    net.nothing_sent()
    _coded_refusal(exc, KeyedProxyRefusedError, "KEYED_PROXY_REFUSED")


@TRANSPORTS
def test_root_with_caller_loopback_base_sends_directly(net, transport):
    exc = send(transport, "/", caller_client(f"http://127.0.0.1:{net.target.port}"))
    net.delivered_direct()
    assert net.target.connections == 1, net.report()
    assert exc is None, repr(exc)


@TRANSPORTS
def test_root_with_caller_https_base_reaches_the_connect_proxy(monkeypatch, net, transport):
    use_proxy(monkeypatch, net, names=("HTTPS_PROXY",))
    authority = f"{PLAIN_HOST}:{net.target.port}"
    exc = send(transport, "/", caller_client(f"https://{authority}"))
    assert (net.target.connections, net.target.marker_bytes()) == (0, 0), net.report()
    assert (net.proxy.connections, net.proxy.marker_bytes()) == (1, 0), net.report()
    assert net.proxy.raw.startswith(f"CONNECT {authority} HTTP/1.1\r\n".encode()), net.report()
    assert isinstance(exc, APIConnectionError), repr(exc)
