"""The generated low-level ``AuthenticatedClient`` keeps its token off plain http the way the rest of the SDK does: it
is refused to a Future AGI host whatever ``FI_ALLOW_INSECURE_HTTP`` says, refused to another non-loopback host without
``FI_ALLOW_INSECURE_HTTP=1``, and refused when an environment proxy would carry it. Loopback, and an opted-in host with
no proxy, are delivered. Every name resolves to this machine through a shim; loopback listeners count the connections
and the marker bytes they receive, so no real host is reached."""

from __future__ import annotations

import os
from unittest import mock

import pytest

import fi
from fi.errors import ConfigurationError, KeyedProxyRefusedError
from fi.generated.openapi_client import AuthenticatedClient
from tests.core._plaintext_oracle import MARKER_KEY, PROXY_NAMES
from tests.core._plaintext_oracle import sinks  # noqa: F401  (requested by name below)
from tests.core.test_sender_rules import resolver  # noqa: F401  (requested by name below)


def _env(flag=None, **extra):
    clean = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES and k != "FI_ALLOW_INSECURE_HTTP"}
    return {**clean, **({} if flag is None else {"FI_ALLOW_INSECURE_HTTP": flag}), **extra}


def _reset(sinks_):
    for each in sinks_.values():
        each.reset()


def _counts(sinks_):
    return {name: (each.requests, each.marker_bytes) for name, each in sinks_.items()}


def _send(base):
    with AuthenticatedClient(base_url=base, token=MARKER_KEY, timeout=None) as client:
        return client.get_httpx_client().get("/probe/").status_code


@pytest.mark.parametrize("flag", [None, "1"])
@pytest.mark.parametrize("host", ["api.futureagi.com", "futureagi.com", "API.FutureAGI.com."])
def test_token_is_refused_over_plain_http_to_a_future_agi_host(sinks, resolver, host, flag):
    _reset(sinks)
    with mock.patch.dict(os.environ, _env(flag), clear=True):
        with pytest.raises(fi.InsecureHttpRefusedError) as info:
            _send(f"http://{host}:{sinks['target'].port}")
    assert MARKER_KEY not in str(info.value)
    assert _counts(sinks) == {name: (0, 0) for name in sinks}


def test_token_is_refused_over_plain_http_to_a_host_not_opted_in(sinks, resolver):
    _reset(sinks)
    with mock.patch.dict(os.environ, _env(), clear=True):
        with pytest.raises(ConfigurationError) as info:
            _send(f"http://collector.example.test:{sinks['target'].port}")
    assert "FI_ALLOW_INSECURE_HTTP" in str(info.value) and MARKER_KEY not in str(info.value)
    assert _counts(sinks) == {name: (0, 0) for name in sinks}


@pytest.mark.parametrize("variable", ["HTTP_PROXY", "http_proxy", "ALL_PROXY"])
def test_opted_in_token_is_not_routed_through_an_environment_proxy(sinks, resolver, variable):
    _reset(sinks)
    proxy = f"http://127.0.0.1:{sinks['sinkA'].port}"
    with mock.patch.dict(os.environ, _env("1", **{variable: proxy}), clear=True):
        with pytest.raises(KeyedProxyRefusedError):
            _send(f"http://collector.example.test:{sinks['target'].port}")
    assert _counts(sinks) == {name: (0, 0) for name in sinks}


@pytest.mark.anyio
async def test_async_client_refuses_before_any_connection(sinks, resolver):
    _reset(sinks)
    with mock.patch.dict(os.environ, _env(), clear=True):
        client = AuthenticatedClient(base_url=f"http://collector.example.test:{sinks['target'].port}", token=MARKER_KEY)
        with pytest.raises(ConfigurationError):
            client.get_async_httpx_client()
        with pytest.raises(fi.InsecureHttpRefusedError):
            AuthenticatedClient(base_url="http://api.futureagi.com", token=MARKER_KEY).get_async_httpx_client()
    assert _counts(sinks) == {name: (0, 0) for name in sinks}


def test_loopback_and_an_opted_in_host_are_delivered(sinks, resolver):
    _reset(sinks)
    with mock.patch.dict(os.environ, _env(), clear=True):
        assert _send(f"http://127.0.0.1:{sinks['target'].port}") == 200
    assert sinks["target"].requests == 1 and sinks["target"].marker_bytes == 1
    assert b"Bearer " + MARKER_KEY.encode() in b"".join(sinks["target"].chunks)
    _reset(sinks)
    with mock.patch.dict(os.environ, _env("1"), clear=True):
        assert _send(f"http://collector.example.test:{sinks['target'].port}") == 200
    assert sinks["target"].requests == 1 and sinks["target"].marker_bytes == 1
    assert (sinks["sinkA"].requests, sinks["sinkB"].requests) == (0, 0)
