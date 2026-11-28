"""The header judgement of ``HttpClient``: a header value that holds an environment key in base64 or percent-encoded form
is a key; the session that sends the request is the one judged; a plain ``requests.Session`` sends and answers directly."""

import base64
import urllib.parse

import pytest
import requests

from fi._core.proxy_routing import carries_credentials
from tests.experiments.unit.oracle_probe import KEY
from tests.experiments.unit.test_header_key_senders import (  # noqa: F401 - fixtures and helpers
    MARKER,
    caller_session,
    outcome,
    refused,
    remote,
    rig,
)

SPECIAL = "ab+/=cd:ef gh1234"


def encoded(value, form):
    if form == "base64":
        return base64.b64encode(value.encode()).decode()
    if form == "urlsafe-base64":
        return base64.urlsafe_b64encode(value.encode()).decode()
    if form == "quoted":
        return urllib.parse.quote(value, safe="")
    return urllib.parse.quote_plus(value)


FORMS = ["base64", "urlsafe-base64", "quoted", "quoted-plus"]


@pytest.mark.parametrize("form", FORMS)
@pytest.mark.parametrize("name", ["FI_API_KEY", "FI_SECRET_KEY"])
def test_a_header_value_holding_an_encoded_environment_key_is_a_key(monkeypatch, name, form):
    monkeypatch.setenv(name, SPECIAL)
    assert carries_credentials({"X-Trace": f"pre-{encoded(SPECIAL, form)}-post"})


def test_an_unrelated_value_is_not_a_key_in_any_form(monkeypatch):
    monkeypatch.setenv("FI_API_KEY", SPECIAL)
    assert not carries_credentials({"X-Trace": "plain value"})


def test_a_short_environment_key_is_not_looked_for_in_encoded_form(monkeypatch):
    monkeypatch.setenv("FI_API_KEY", "a b+c")
    assert not carries_credentials({"X-Trace": encoded("a b+c", "quoted")})


@pytest.mark.parametrize("form", FORMS)
def test_an_encoded_environment_key_in_a_header_is_refused_by_the_client(rig, monkeypatch, form):
    from fi.api.auth import HttpClient

    monkeypatch.setenv("FI_API_KEY", MARKER + "+/ x")
    value = encoded(MARKER + "+/ x", form)

    def make(base, mp):
        return HttpClient(base_url=base, default_headers={"X-Trace": value}), {}

    error = outcome(make, remote(rig.target), monkeypatch)
    assert refused(error), error
    assert rig.connections() == 0 and rig.bytes() == 0


def _stack(configure_outer, configure_inner=None, middle=False):
    """A ``FuturesSession`` (optionally through a middle one) that hands its requests to a ``requests.Session``."""
    from requests_futures.sessions import FuturesSession

    from fi.utils.executor import BoundedExecutor

    inner = requests.Session()
    if configure_inner:
        configure_inner(inner)
    handed = inner
    if middle:
        handed = FuturesSession(executor=BoundedExecutor(bound=4, max_workers=1), session=inner)
        configure_outer(handed)
    outer = FuturesSession(executor=BoundedExecutor(bound=4, max_workers=1), session=handed)
    configure_outer(outer)
    return outer


def _client_on(session):
    from fi.api.auth import HttpClient

    return lambda base, mp: (HttpClient(base_url=base, session=session), {})


def _outer_header(session):
    session.headers["X-Api-Key"] = MARKER


def _outer_basic(session):
    session.auth = ("user", MARKER)


def _outer_hook(session):
    def hook(request):
        request.headers["X-Api-Key"] = MARKER
        return request

    session.auth = hook


def _outer_cookie(session):
    session.cookies.set("sid", MARKER)


@pytest.mark.parametrize("middle", [False, True])
@pytest.mark.parametrize("configure", [_outer_header, _outer_basic, _outer_hook, _outer_cookie])
def test_a_setting_held_only_by_an_outer_futures_session_is_not_judged(rig, monkeypatch, configure, middle):
    monkeypatch.setenv("FI_API_KEY", MARKER)
    session = _stack(configure, middle=middle)
    error = outcome(_client_on(session), remote(rig.target), monkeypatch)
    assert not refused(error), error  # a nested FuturesSession answers with a Future: only the refusal is read
    assert rig.target.marker_bytes == 0


@pytest.mark.parametrize("middle", [False, True])
def test_a_key_held_by_the_sending_session_is_refused_under_outer_sessions(rig, monkeypatch, middle):
    session = _stack(lambda s: None, lambda inner: inner.headers.update({"X-Api-Key": MARKER}), middle=middle)
    error = outcome(_client_on(session), remote(rig.target), monkeypatch)
    assert refused(error), error
    assert rig.connections() == 0 and rig.bytes() == 0


def test_a_callable_auth_on_the_sending_session_is_judged_as_a_key(rig, monkeypatch):
    session = _stack(lambda s: None, _outer_hook)
    error = outcome(_client_on(session), remote(rig.target), monkeypatch)
    assert refused(error), error
    assert rig.connections() == 0 and rig.bytes() == 0


def _plain_client(configure=None):
    from fi.api.auth import HttpClient

    def make(base, mp):
        session = requests.Session()
        if configure:
            configure(session)
        return HttpClient(base_url=base, session=session), {}

    return make


def test_a_plain_requests_session_sends_and_answers_with_the_response(rig, monkeypatch):
    from tests.experiments.unit.test_header_key_senders import send

    response = send(_plain_client(), f"http://127.0.0.1:{rig.target.port}", monkeypatch)
    assert isinstance(response, requests.Response)
    assert rig.target.connections == 1


def test_a_plain_requests_session_holding_a_key_is_refused_for_a_plain_remote_host(rig, monkeypatch):
    error = outcome(_plain_client(lambda s: s.headers.update({"X-Api-Key": MARKER})), remote(rig.target), monkeypatch)
    assert refused(error), error
    assert rig.connections() == 0 and rig.bytes() == 0


def test_a_plain_requests_session_with_a_key_and_the_opt_in_sends_directly(rig, monkeypatch):
    from fi._core.http_security import ALLOW_INSECURE_HTTP_ENV
    from tests.experiments.unit.test_header_key_senders import send

    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    response = send(_plain_client(lambda s: s.headers.update({"X-Api-Key": MARKER})), remote(rig.target), monkeypatch)
    assert isinstance(response, requests.Response)
    assert rig.target.marker_bytes > 0 and rig.proxy.marker_bytes == 0
