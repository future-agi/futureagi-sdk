"""A session ``auth`` that is a tuple subclass is judged as what it sends. ``requests`` reads the tuple's length when it
prepares a request, so a subclass can read as empty when ``HttpClient`` judges the request and as a ``(user, password)``
pair when the request is sent: such an auth is judged as a key, the way a callable auth is. A plain ``(user, password)``
tuple is judged from the prepared request.

Host names resolve to the loopback address (``getaddrinfo`` is replaced for the test); the loopback listeners (the target
and a ``CONNECT``-aware proxy sink) count connections and the planted marker, Basic credentials decoded."""

import threading
from collections import namedtuple

import pytest
import requests

from fi._core.http_security import ALLOW_INSECURE_HTTP_ENV
from fi.api.auth import HttpClient
from fi.errors import KeyedProxyRefusedError
from tests.experiments.unit.test_header_key_senders import (  # noqa: F401  (pytest resolves rig by name)
    MARKER, caller_session, outcome, proxied, refused, remote, rig, send, wire_count,
)


class EmptyOnItsOwnThread(tuple):
    """A ``(user, password)`` pair whose length reads 0 on the thread that built it (where ``HttpClient`` judges the
    request) and 2 on any other thread (the executor thread a ``FuturesSession`` sends on)."""

    def __new__(cls, pair):
        made = super().__new__(cls, pair)
        made.owner = threading.get_ident()
        return made

    def __len__(self):
        return 0 if threading.get_ident() == self.owner else 2


Pair = namedtuple("Pair", "user password")


def with_auth(build):
    def make(base, monkeypatch):
        session = caller_session()
        session.auth = build()
        return HttpClient(base_url=base, session=session), {}

    return make


SHIFTING = with_auth(lambda: EmptyOnItsOwnThread(("user", MARKER)))


def test_a_tuple_that_reads_empty_when_judged_is_judged_as_a_key(rig, monkeypatch):
    error = outcome(SHIFTING, remote(rig.target), monkeypatch)
    assert refused(error), error
    assert (rig.target.connections, wire_count(rig.target)) == (0, 0)
    assert rig.connections() == 0 and rig.bytes() == 0


def test_the_same_tuple_reaches_no_environment_proxy(rig, monkeypatch):
    proxied(rig, monkeypatch)
    error = outcome(SHIFTING, remote(rig.target), monkeypatch)
    assert refused(error), error
    assert (rig.proxy.connections, wire_count(rig.proxy)) == (0, 0)
    assert rig.connections() == 0 and rig.bytes() == 0


def test_with_the_opt_in_and_an_environment_proxy_the_tuple_reaches_no_proxy(rig, monkeypatch):
    proxied(rig, monkeypatch)
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    error = outcome(SHIFTING, remote(rig.target), monkeypatch)
    assert isinstance(error, KeyedProxyRefusedError), error
    assert (rig.proxy.connections, wire_count(rig.proxy)) == (0, 0)
    assert rig.connections() == 0 and rig.bytes() == 0


def test_with_the_opt_in_the_tuple_delivers_its_credentials_to_the_target(rig, monkeypatch):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    response = send(SHIFTING, remote(rig.target), monkeypatch)
    assert isinstance(response, requests.Response)
    assert rig.target.connections == 1 and wire_count(rig.target) == 1
    assert rig.proxy.connections == 0 and wire_count(rig.proxy) == 0


@pytest.mark.parametrize("build", [lambda: ("user", MARKER), lambda: Pair("user", MARKER)], ids=["tuple", "namedtuple"])
def test_a_pair_is_refused_without_the_opt_in_and_delivered_with_it(rig, monkeypatch, build):
    assert refused(outcome(with_auth(build), remote(rig.target), monkeypatch))
    assert rig.connections() == 0 and rig.bytes() == 0
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    response = send(with_auth(build), remote(rig.target), monkeypatch)
    assert isinstance(response, requests.Response)
    assert rig.target.connections == 1 and wire_count(rig.target) == 1
    assert rig.proxy.connections == 0
