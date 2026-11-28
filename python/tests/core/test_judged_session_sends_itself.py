"""The session ``HttpClient`` judges is the session that sends. A ``FuturesSession`` hands each request to the session in
its ``session`` attribute, so that session is judged and the outer one's unsent headers are not. Any other object sends
through itself whatever its ``session`` attribute holds, so its own headers are judged; an object whose ``request`` the SDK
cannot see into may send through itself or through its ``session``, so both are judged.

Host names resolve to the loopback address (``getaddrinfo`` is replaced for the test); the loopback listeners (the target
and a ``CONNECT``-aware proxy sink) count connections and the planted marker, Basic credentials decoded."""

import pytest
import requests
from requests_futures.sessions import FuturesSession

from fi._core.http_security import ALLOW_INSECURE_HTTP_ENV
from fi.api.auth import HttpClient
from fi.errors import KeyedProxyRefusedError
from fi.utils.executor import BoundedExecutor
from tests.experiments.unit.test_header_key_senders import (  # noqa: F401  (pytest resolves rig by name)
    MARKER, outcome, proxied, refused, remote, rig, send, wire_count,
)


class SendsItself(requests.Session):
    """A session that keeps a helper session in ``session`` and sends every request through itself."""

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.sent = 0

    def send(self, request, **kwargs):
        self.sent += 1
        return super().send(request, **kwargs)


class RequestsItself(SendsItself):
    """The same, with its own ``request`` that sends through itself."""

    def request(self, *args, **kwargs):
        return requests.Session.request(self, *args, **kwargs)


class HandsOn(requests.Session):
    """A session whose own ``request`` hands the call to the session in ``session``."""

    def __init__(self, inner):
        super().__init__()
        self.session = inner

    def request(self, *args, **kwargs):
        return self.session.request(*args, **kwargs)


def _keyed(session):
    session.headers["X-Api-Key"] = MARKER
    return session


def _client(build):
    return lambda base, mp: (HttpClient(base_url=base, session=build()), {})


SELF_SENDERS = {"own send": lambda: _keyed(SendsItself()), "own request": lambda: _keyed(RequestsItself())}


@pytest.mark.parametrize("kind", list(SELF_SENDERS))
def test_a_session_that_sends_itself_is_judged_on_its_own_headers(rig, monkeypatch, kind):
    error = outcome(_client(SELF_SENDERS[kind]), remote(rig.target), monkeypatch)
    assert refused(error), error
    assert (rig.target.connections, wire_count(rig.target)) == (0, 0)
    assert rig.connections() == 0 and rig.bytes() == 0


@pytest.mark.parametrize("kind", list(SELF_SENDERS))
def test_the_same_session_reaches_no_environment_proxy(rig, monkeypatch, kind):
    proxied(rig, monkeypatch)
    error = outcome(_client(SELF_SENDERS[kind]), remote(rig.target), monkeypatch)
    assert refused(error), error
    assert (rig.proxy.connections, wire_count(rig.proxy)) == (0, 0)
    assert rig.connections() == 0 and rig.bytes() == 0


@pytest.mark.parametrize("kind", list(SELF_SENDERS))
def test_with_the_opt_in_the_session_delivers_its_key_to_the_target(rig, monkeypatch, kind):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    session = SELF_SENDERS[kind]()
    response = send(lambda base, mp: (HttpClient(base_url=base, session=session), {}), remote(rig.target), monkeypatch)
    assert isinstance(response, requests.Response)
    assert session.sent == 1
    assert rig.target.connections == 1 and wire_count(rig.target) > 0
    assert rig.proxy.connections == 0 and wire_count(rig.proxy) == 0


@pytest.mark.parametrize("kind", list(SELF_SENDERS))
def test_with_the_opt_in_and_an_environment_proxy_the_key_reaches_no_proxy(rig, monkeypatch, kind):
    proxied(rig, monkeypatch)
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    error = outcome(_client(SELF_SENDERS[kind]), remote(rig.target), monkeypatch)
    assert isinstance(error, KeyedProxyRefusedError), error
    assert rig.connections() == 0 and rig.bytes() == 0


def test_a_key_on_the_session_a_handing_session_calls_is_judged(rig, monkeypatch):
    error = outcome(_client(lambda: HandsOn(_keyed(requests.Session()))), remote(rig.target), monkeypatch)
    assert refused(error), error
    assert rig.connections() == 0 and rig.bytes() == 0


def test_a_key_on_a_handing_session_itself_is_judged(rig, monkeypatch):
    error = outcome(_client(lambda: _keyed(HandsOn(requests.Session()))), remote(rig.target), monkeypatch)
    assert refused(error), error
    assert rig.connections() == 0 and rig.bytes() == 0


def test_a_futures_session_over_a_clean_session_is_not_refused_for_its_unsent_headers(rig, monkeypatch):
    def build():
        return _keyed(FuturesSession(executor=BoundedExecutor(bound=4, max_workers=1), session=requests.Session()))

    error = outcome(_client(build), remote(rig.target), monkeypatch)
    assert not refused(error), error
    assert wire_count(rig.target) == 0 and rig.proxy.connections == 0
