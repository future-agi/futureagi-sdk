"""A caller session that hands its requests to another session (``FuturesSession(session=inner)``) sends through the inner
one, so the inner session's routing decides whether a key-carrying plain-http request goes through a proxy. Every row below
puts the routing on the inner session (a ``proxies`` entry, an environment proxy it reads with ``trust_env``, or a mounted
adapter that is not requests' own) and expects the request refused with ``KeyedProxyRefusedError`` before any byte: the marker
keys are counted at the loopback listeners (the target and two proxy sinks)."""

from __future__ import annotations

import os
from unittest import mock

import pytest
import requests
from requests.adapters import HTTPAdapter
from requests_futures.sessions import FuturesSession

import fi
from tests.core._plaintext_oracle import PROXY_NAMES, Sink
from tests.core._plaintext_oracle import sinks  # noqa: F401  (the fixture)
from tests.core.test_sender_rules import KEYS, LOOPBACK_HOSTS, _get, _seen, resolver  # noqa: F401  (the fixture)

HOSTS = [*LOOPBACK_HOSTS, "example.com"]


class _OtherAdapter(HTTPAdapter):
    """An adapter that is not requests' own class: the SDK cannot see what it does with a request."""


def _routing(kind: str, session: requests.Session, sinks_: dict[str, Sink]) -> dict[str, str]:
    proxy = f"http://127.0.0.1:{sinks_['sinkA'].port}"
    if kind == "proxies":
        session.proxies.update({"http": proxy})
        return {}
    if kind == "environment":
        session.trust_env = True
        return {"HTTP_PROXY": proxy}
    session.mount("http://", _OtherAdapter())
    return {}


class _Delegating:
    """A session-like object that hands each request to another session, as a wrapper a caller writes does."""

    def __init__(self, session: requests.Session) -> None:
        self.session = session
        self.headers = session.headers

    def request(self, *args, **kwargs):
        return self.session.request(*args, **kwargs)

    def close(self) -> None:
        self.session.close()


def _delegating(depth: int, inner: requests.Session) -> FuturesSession:
    """``FuturesSession(session=inner)``; at depth 2 the inner session sits behind one more delegating object."""
    return FuturesSession(session=inner if depth == 1 else _Delegating(inner))


@pytest.mark.parametrize("depth", [1, 2])
@pytest.mark.parametrize("kind", ["proxies", "environment", "mounted adapter"])
@pytest.mark.parametrize("host", HOSTS)
def test_a_key_carrying_request_through_a_delegating_session_is_refused_when_the_inner_session_is_proxied(sinks, resolver, host, kind, depth):
    from fi.api.auth import HttpClient

    for each in sinks.values():
        each.reset()
    inner = requests.Session()
    env = _routing(kind, inner, sinks)
    clean = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    with mock.patch.dict(os.environ, {**clean, **env, "FI_ALLOW_INSECURE_HTTP": "1"}, clear=True):
        client = HttpClient(base_url="https://fi.example.invalid", session=_delegating(depth, inner), default_headers=dict(KEYS))
        # A host that writes user info is refused for that before routing is looked at.
        with pytest.raises(fi.errors.ConfigurationError if "@" in host else fi.KeyedProxyRefusedError):
            _get(client, f"http://{host}:{sinks['target'].port}/x")
    assert _seen(sinks) == {"target": 0, "sinkA": 0, "sinkB": 0}


def test_a_delegating_session_with_an_inner_session_that_has_no_routing_sends(sinks, resolver):
    from fi.api.auth import HttpClient

    for each in sinks.values():
        each.reset()
    clean = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    with mock.patch.dict(os.environ, clean, clear=True):
        client = HttpClient(base_url="https://fi.example.invalid", session=_delegating(2, requests.Session()), default_headers=dict(KEYS))
        _get(client, f"http://127.0.0.1:{sinks['target'].port}/x")
    assert sinks["target"].marker_bytes > 0 and sinks["sinkA"].marker_bytes == 0


def test_a_delegating_session_whose_chain_loops_is_refused():
    from fi._core.proxy_routing import requests_session_proxied

    class Loop:
        def __init__(self) -> None:
            self.session = self
            self.proxies: dict[str, str] = {}
            self.trust_env = False

    assert requests_session_proxied(Loop(), "http://127.0.0.1:1/x") is True
