"""A ``requests`` session decides proxy routing with its own rule, so the SDK judges a key-carrying plain-http request by the
same rule: ``NO_PROXY`` entries (a host, a ``*``, a CIDR range) that make requests send direct make the request go, and a
proxy for another scheme does not matter. A proxy that requests would use refuses the request before any byte. Marker keys
are counted at the loopback listeners (the target and two proxy sinks)."""

from __future__ import annotations

import os
from unittest import mock

import pytest
from requests_futures.sessions import FuturesSession

import fi
from tests.core._plaintext_oracle import PROXY_NAMES
from tests.core._plaintext_oracle import sinks  # noqa: F401  (the fixture)
from tests.core.test_sender_rules import KEYS, _get, _seen, resolver  # noqa: F401  (the fixture)


def _client():
    from fi.api.auth import HttpClient

    return HttpClient(base_url="https://fi.example.invalid", session=FuturesSession(), default_headers=dict(KEYS))


def _env(sinks_, **extra):
    clean = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    proxy = f"http://127.0.0.1:{sinks_['sinkA'].port}"
    return {**clean, **{k: v.replace("PROXY", proxy).replace("PORT", str(sinks_["target"].port)) for k, v in extra.items()}}


SENDS = {
    "NO_PROXY alone": {"NO_PROXY": "127.0.0.1"},
    "HTTPS_PROXY alone": {"HTTPS_PROXY": "PROXY"},
    "HTTP_PROXY and NO_PROXY host": {"HTTP_PROXY": "PROXY", "NO_PROXY": "127.0.0.1"},
    "HTTP_PROXY and NO_PROXY star": {"HTTP_PROXY": "PROXY", "NO_PROXY": "*"},
    "HTTP_PROXY and NO_PROXY cidr": {"HTTP_PROXY": "PROXY", "NO_PROXY": "127.0.0.0/8"},
    "HTTP_PROXY and NO_PROXY list with cidr": {"HTTP_PROXY": "PROXY", "NO_PROXY": "example.test,192.0.2.0/24,127.0.0.0/8"},
}
REFUSED = {
    "HTTP_PROXY alone": {"HTTP_PROXY": "PROXY"},
    "HTTP_PROXY and NO_PROXY for another host": {"HTTP_PROXY": "PROXY", "NO_PROXY": "other.example"},
    "HTTP_PROXY and NO_PROXY cidr that does not hold the host": {"HTTP_PROXY": "PROXY", "NO_PROXY": "192.0.2.0/24"},
    "ALL_PROXY alone": {"ALL_PROXY": "PROXY"},
}


@pytest.mark.parametrize("case", sorted(SENDS))
def test_a_caller_session_sends_when_requests_would_send_direct(sinks, resolver, case):
    for each in sinks.values():
        each.reset()
    with mock.patch.dict(os.environ, _env(sinks, **SENDS[case]), clear=True):
        _get(_client(), f"http://127.0.0.1:{sinks['target'].port}/x")
    assert sinks["target"].marker_bytes > 0 and sinks["sinkA"].marker_bytes == 0


@pytest.mark.parametrize("case", sorted(REFUSED))
def test_a_caller_session_is_refused_when_requests_would_use_a_proxy(sinks, resolver, case):
    for each in sinks.values():
        each.reset()
    with mock.patch.dict(os.environ, _env(sinks, **REFUSED[case]), clear=True):
        with pytest.raises(fi.KeyedProxyRefusedError):
            _get(_client(), f"http://127.0.0.1:{sinks['target'].port}/x")
    assert _seen(sinks) == {"target": 0, "sinkA": 0, "sinkB": 0}
