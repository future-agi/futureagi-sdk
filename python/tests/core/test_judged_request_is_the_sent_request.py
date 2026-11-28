"""A request is judged from what the session sends, once: a callable ``auth`` that adds a key on a later call, or on a
retry, is judged as a key before the first byte, and runs once for the send."""

import pytest
from requests.auth import AuthBase, HTTPDigestAuth

from fi._core.http_security import ALLOW_INSECURE_HTTP_ENV
from fi.errors import ConfigurationError
from tests.experiments.unit.oracle_probe import Sink
from tests.experiments.unit.test_header_key_senders import (  # noqa: F401  (fixture)
    MARKER, caller_session, outcome, proxied, remote, rig,
)
from fi.api.auth import HttpClient


class LaterKey(AuthBase):
    """Clean on its first call; adds the key on every later call."""

    def __init__(self):
        self.calls = 0

    def __call__(self, request):
        self.calls += 1
        if self.calls > 1:
            request.headers["X-Api-Key"] = MARKER
        return request


def with_auth(auth):
    def make(base, monkeypatch):
        session = caller_session()
        session.auth = auth
        return HttpClient(base_url=base, session=session), {}

    return make


def refused(error):
    return isinstance(error, ConfigurationError) and error.code == "insecure_http_origin"


def test_a_callable_auth_that_adds_a_key_on_a_later_call_is_refused_on_a_non_loopback_host(rig, monkeypatch):
    error = outcome(with_auth(LaterKey()), remote(rig.target), monkeypatch)
    assert refused(error), error
    assert rig.connections() == 0 and rig.bytes() == 0


def test_the_same_auth_reaches_no_proxy(rig, monkeypatch):
    proxied(rig, monkeypatch)
    error = outcome(with_auth(LaterKey()), remote(rig.target), monkeypatch)
    assert refused(error), error
    assert rig.connections() == 0 and rig.bytes() == 0


def test_the_same_auth_with_the_opt_in_and_an_environment_proxy_reaches_no_proxy(rig, monkeypatch):
    proxied(rig, monkeypatch)
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    outcome(with_auth(LaterKey()), remote(rig.target), monkeypatch)
    assert rig.proxy.connections == 0 and rig.proxy.marker_bytes == 0


def test_a_retry_that_adds_a_key_is_judged(rig, monkeypatch):
    from fi.api.types import HttpMethod, RequestConfig

    client, _ = with_auth(LaterKey())(remote(rig.target), monkeypatch)
    config = RequestConfig(method=HttpMethod.GET, url=f"{remote(rig.target)}/probe", retry_attempts=3, retry_delay=0)
    try:
        client.request(config)
    except Exception as error:  # noqa: BLE001
        assert refused(error), error
    assert rig.connections() == 0 and rig.bytes() == 0


def test_a_digest_auth_second_request_is_judged(rig, monkeypatch):
    challenge = (b"HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: Digest realm=\"r\", nonce=\"n\", qop=\"auth\"\r\n"
                 b"Content-Length: 0\r\n\r\n")
    digest = Sink(False, reply=challenge)
    try:
        error = outcome(with_auth(HTTPDigestAuth(MARKER, "pw")), remote(digest), monkeypatch)
        assert refused(error), error
        assert digest.connections == 0 and digest.marker_bytes == 0
    finally:
        digest.close()


def test_a_callable_auth_runs_once_for_a_send_to_loopback(rig, monkeypatch):
    auth = LaterKey()
    outcome(with_auth(auth), f"http://localhost:{rig.target.port}", monkeypatch)
    assert auth.calls == 1


def test_a_callable_auth_to_loopback_reaches_no_proxy(rig, monkeypatch):
    proxied(rig, monkeypatch)
    outcome(with_auth(LaterKey()), f"http://localhost:{rig.target.port}", monkeypatch)
    assert rig.proxy.connections == 0 and rig.proxy.marker_bytes == 0


def test_a_tuple_auth_is_unchanged(rig, monkeypatch):
    def make(base, monkeypatch):
        session = caller_session()
        session.auth = ("user", MARKER)
        return HttpClient(base_url=base, session=session), {}

    assert refused(outcome(make, remote(rig.target), monkeypatch))
    assert rig.connections() == 0 and rig.bytes() == 0


class CallableTuple(tuple):
    """A three-item tuple that is also callable: ``requests`` calls it, and it adds the key on its second call."""

    calls = 0

    def __call__(self, request):
        type(self).calls += 1
        if type(self).calls > 1:
            request.headers["X-Api-Key"] = MARKER
        return request


class CallableList(list):
    calls = 0

    def __call__(self, request):
        type(self).calls += 1
        if type(self).calls > 1:
            request.headers["X-Api-Key"] = MARKER
        return request


@pytest.mark.parametrize("auth_class", [CallableTuple, CallableList])
def test_a_tuple_or_list_that_is_callable_is_judged_as_a_key(rig, monkeypatch, auth_class):
    auth_class.calls = 0
    error = outcome(with_auth(auth_class(("a", "b", "c"))), remote(rig.target), monkeypatch)
    assert refused(error), error
    assert rig.connections() == 0 and rig.bytes() == 0
