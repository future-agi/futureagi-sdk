"""A judge given a caller transport that routes through a proxy refuses a plain-http keyed request: the proxy is asked.

The judge's own client sends a plain ``http://`` base URL directly. A transport the caller hands to ``Judge(transport=)``
is the caller's: when it carries a ``proxy=``, the request with the key goes to that proxy, so the judge refuses it
with ``KeyedProxyRefusedError`` before a connection, for a loopback base URL and for an opted-in one. Requests to
an ``https`` base URL use a tunnel through the proxy. A transport without a proxy sends requests directly.

Host names resolve to the loopback address (``getaddrinfo`` is replaced by the ``rig`` helper); every listener counts
its connections and the marker occurrences it received (a Basic credential decoded too).
"""

import asyncio
import types

import httpx

from fi.errors import KeyedProxyRefusedError
from fi.experiments.evaluators.judge import Judge
from tests.experiments.unit.test_header_key_senders import MARKER, proxied, remote, rig, wire_count  # noqa: F401  (rig is requested by name)


def chat(base, transport=None):
    judge = Judge("is it right", model="m", base_url=base, timeout_s=3, transport=transport)
    ec = types.SimpleNamespace(usage=[])
    try:
        asyncio.run(judge._chat(ec, MARKER, "system", "user"))
    except Exception as error:  # noqa: BLE001 - a listener's reply is not a completion
        return error
    return None


def through(rig):
    return httpx.AsyncHTTPTransport(proxy=f"http://127.0.0.1:{rig.proxy.port}")


def test_a_loopback_base_url_through_a_caller_proxy_is_refused_before_a_connection(rig):
    error = chat(f"http://localhost:{rig.target.port}/v1", through(rig))
    assert isinstance(error, KeyedProxyRefusedError), repr(error)
    assert rig.proxy.connections == 0 and wire_count(rig.proxy) == 0
    assert rig.connections() == 0 and rig.bytes() == 0


def test_an_opted_in_base_url_through_a_caller_proxy_is_refused_before_a_connection(rig, monkeypatch):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    error = chat(f"{remote(rig.target)}/v1", through(rig))
    assert isinstance(error, KeyedProxyRefusedError), repr(error)
    assert rig.proxy.connections == 0 and wire_count(rig.proxy) == 0
    assert rig.connections() == 0 and rig.bytes() == 0


def test_an_https_base_url_through_a_caller_proxy_is_tunnelled_as_before(rig):
    error = chat(f"https://api.example.test:{rig.target.port}/v1", through(rig))
    assert not isinstance(error, KeyedProxyRefusedError), repr(error)
    assert rig.proxy.connections >= 1  # the CONNECT tunnel; the key travels inside TLS only
    assert rig.bytes() == 0


def test_a_caller_transport_without_a_proxy_delivers_to_a_loopback_base_url(rig):
    error = chat(f"http://localhost:{rig.target.port}/v1", httpx.AsyncHTTPTransport())
    assert not isinstance(error, KeyedProxyRefusedError), repr(error)
    assert rig.proxy.connections == 0 and wire_count(rig.proxy) == 0
    assert wire_count(rig.target) > 0


def test_a_caller_transport_without_a_proxy_delivers_to_an_opted_in_base_url(rig, monkeypatch):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    error = chat(f"{remote(rig.target)}/v1", httpx.AsyncHTTPTransport())
    assert not isinstance(error, KeyedProxyRefusedError), repr(error)
    assert rig.proxy.connections == 0 and wire_count(rig.proxy) == 0
    assert wire_count(rig.target) > 0


def test_the_judge_s_own_transport_with_an_environment_proxy_delivers_directly(rig, monkeypatch):
    proxied(rig, monkeypatch)
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    error = chat(f"{remote(rig.target)}/v1")
    assert not isinstance(error, KeyedProxyRefusedError), repr(error)
    assert rig.proxy.connections == 0 and wire_count(rig.proxy) == 0
    assert wire_count(rig.target) > 0
