"""Credential isolation regressions using synthetic keys and stub transports only.

Expected RED before the fix:
- test_class_reads_are_value_free (all parameters): class access exposes keys.
- test_uninitialized_subclass_class_reads_are_value_free (all parameters): an
  uninitialized subclass inherits the last base client's keys.
- test_instances_keep_their_own_credentials (all parameters): instance lookup
  returns the most recently constructed same-class client's credentials.
- test_knowledge_base_sends_its_own_headers: direct KB requests read those keys
  at send time, unlike HttpClient's already-snapshotted default headers.
The remaining cases protect existing headers, environment fallback and errors.
"""

import json
import warnings
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Barrier, Lock

import pytest
from requests import Request, Response

from fi.api.auth import APIKeyAuth
from fi.api.types import HttpMethod, RequestConfig
from fi.kb.client import KnowledgeBase
from fi.utils.errors import MissingAuthError

BASE = "http://127.0.0.1:9"
KEYS_A = ("synthetic-a-api", "synthetic-a-secret")
KEYS_B = ("synthetic-b-api", "synthetic-b-secret")
ENV_KEYS = ("synthetic-env-api", "synthetic-env-secret")
CREDENTIAL_NAMES = ("_fi_api_key", "_fi_secret_key")


class DerivedAuth(APIKeyAuth):
    pass


CLIENT_TYPES = (APIKeyAuth, DerivedAuth, KnowledgeBase)


@pytest.fixture(autouse=True)
def _isolate_auth_state(monkeypatch):
    monkeypatch.delenv("FI_API_KEY", raising=False)
    monkeypatch.delenv("FI_SECRET_KEY", raising=False)

    def no_network(*args, **kwargs):
        raise AssertionError("Unexpected real HTTP transport in isolation tests")

    monkeypatch.setattr("requests.sessions.Session.send", no_network)
    # Restore raw class dictionaries even when a test fails on the old code.
    # getattr would itself invoke the new warning-emitting descriptor.
    missing = object()
    saved = [
        (owner, name, vars(owner).get(name, missing))
        for owner in CLIENT_TYPES
        for name in CREDENTIAL_NAMES
    ]
    try:
        yield
    finally:
        for owner, name, value in saved:
            if value is missing:
                if name in vars(owner):
                    delattr(owner, name)
            else:
                setattr(owner, name, value)


class StubTransport:
    """FuturesSession-shaped transport recording prepared outbound headers."""

    def __init__(self, body=None, barrier=None):
        self.body = {} if body is None else body
        self.barrier = barrier
        self.calls = []
        self.lock = Lock()

    def respond(self, method, url, **kwargs):
        request = Request(
            method, url, headers=kwargs.get("headers"), params=kwargs.get("params"),
        ).prepare()
        if self.barrier is not None:
            self.barrier.wait()
        with self.lock:
            self.calls.append(request)
        response = Response()
        response.status_code = 200
        response.url = request.url
        response.request = request
        response._content = json.dumps(self.body).encode("utf-8")
        return response

    def request(self, method, url, **kwargs):
        future = Future()
        future.set_result(self.respond(method, url, **kwargs))
        return future

    def close(self):
        pass


def _client(client_type, keys, transport):
    return client_type(
        fi_api_key=keys[0], fi_secret_key=keys[1], fi_base_url=BASE, session=transport,
    )


def _send(client, path):
    return client.request(RequestConfig(
        method=HttpMethod.GET, url=f"{BASE}/{path}", retry_attempts=1,
    ))


def _keys(request):
    return (request.headers["X-Api-Key"], request.headers["X-Secret-Key"])


def _assert_value_free_class_read(owner, name):
    # Cover both direct access and the legacy getattr(..., None) idiom.
    for direct in (True, False):
        with pytest.warns(
            DeprecationWarning, match="read credentials from the client instance",
        ) as caught:
            if direct:
                value = owner._fi_api_key if name == "_fi_api_key" else owner._fi_secret_key
            else:
                value = getattr(owner, name, None)
            assert value is None
        assert len(caught) == 1
        assert all(
            key not in str(warning.message)
            for warning in caught
            for key in KEYS_A + KEYS_B + ENV_KEYS
        )


def test_two_clients_send_their_own_headers_in_sequence():
    transport = StubTransport()
    first = _client(APIKeyAuth, KEYS_A, transport)
    second = _client(APIKeyAuth, KEYS_B, transport)
    _send(first, "first")
    _send(second, "second")
    _send(first, "first-again")
    assert [_keys(call) for call in transport.calls] == [KEYS_A, KEYS_B, KEYS_A]


def test_two_clients_send_their_own_headers_on_concurrent_threads():
    # Rendezvous inside every send so the clients overlap, rather than take turns.
    transport = StubTransport(barrier=Barrier(2, timeout=10))
    first = _client(APIKeyAuth, KEYS_A, transport)
    second = _client(APIKeyAuth, KEYS_B, transport)

    def send_many(client, path):
        for _ in range(4):
            _send(client, path)

    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = [
            pool.submit(send_many, first, "first"),
            pool.submit(send_many, second, "second"),
        ]
        for future in pending:
            future.result(timeout=15)
    assert len(transport.calls) == 8
    for path, expected in (("first", KEYS_A), ("second", KEYS_B)):
        calls = [call for call in transport.calls if call.url == f"{BASE}/{path}"]
        assert len(calls) == 4
        assert all(_keys(call) == expected for call in calls)


def test_subclass_sends_its_own_headers():
    transport = StubTransport()
    first = _client(DerivedAuth, KEYS_A, transport)
    second = _client(DerivedAuth, KEYS_B, transport)
    _send(first, "first")
    _send(second, "second")
    _send(first, "first-again")
    assert [_keys(call) for call in transport.calls] == [KEYS_A, KEYS_B, KEYS_A]


def test_knowledge_base_sends_its_own_headers(monkeypatch):
    """Expected RED: create_kb reads shared class credentials at send time."""
    transport = StubTransport(body={"result": {
        "kb_id": "11111111-1111-1111-1111-111111111111",
        "kb_name": "synthetic-kb",
        "file_ids": [],
    }})
    monkeypatch.setattr(
        "requests.post", lambda url, **kwargs: transport.respond("POST", url, **kwargs),
    )
    first = _client(KnowledgeBase, KEYS_A, transport)
    second = _client(KnowledgeBase, KEYS_B, transport)
    assert first.create_kb(name="synthetic-kb") is first
    assert second.create_kb(name="synthetic-kb") is second
    assert first.create_kb(name="synthetic-kb") is first
    assert [_keys(call) for call in transport.calls] == [KEYS_A, KEYS_B, KEYS_A]


@pytest.mark.parametrize("client_type", CLIENT_TYPES, ids=lambda cls: cls.__name__)
def test_explicit_keys_win_over_environment_headers(monkeypatch, client_type):
    monkeypatch.setenv("FI_API_KEY", ENV_KEYS[0])
    monkeypatch.setenv("FI_SECRET_KEY", ENV_KEYS[1])
    transport = StubTransport()
    client = _client(client_type, KEYS_A, transport)
    _send(client, "explicit")
    assert len(transport.calls) == 1
    assert _keys(transport.calls[0]) == KEYS_A


@pytest.mark.parametrize("client_type", CLIENT_TYPES, ids=lambda cls: cls.__name__)
@pytest.mark.parametrize("keys,expected", [
    ((None, None), ENV_KEYS),
    (("", ""), ENV_KEYS),
    ((KEYS_A[0], None), (KEYS_A[0], ENV_KEYS[1])),
    ((None, KEYS_A[1]), (ENV_KEYS[0], KEYS_A[1])),
], ids=["omitted", "empty", "explicit-api", "explicit-secret"])
def test_environment_fallback_headers(monkeypatch, client_type, keys, expected):
    monkeypatch.setenv("FI_API_KEY", ENV_KEYS[0])
    monkeypatch.setenv("FI_SECRET_KEY", ENV_KEYS[1])
    transport = StubTransport()
    client = _client(client_type, keys, transport)
    _send(client, "fallback")
    assert len(transport.calls) == 1
    assert _keys(transport.calls[0]) == expected


@pytest.mark.parametrize("keys,missing_api,missing_secret", [
    ((None, None), True, True),
    ((None, KEYS_A[1]), True, False),
    ((KEYS_A[0], None), False, True),
])
def test_missing_credentials_raise_without_sending(keys, missing_api, missing_secret):
    transport = StubTransport()
    with pytest.raises(MissingAuthError) as caught:
        _client(APIKeyAuth, keys, transport)
    assert caught.value.missing_api_key is missing_api
    assert caught.value.missing_secret_key is missing_secret
    assert transport.calls == []


@pytest.mark.parametrize("client_type", CLIENT_TYPES, ids=lambda cls: cls.__name__)
def test_instances_keep_their_own_credentials(client_type):
    """Expected RED: an older instance reads the newer instance's class keys."""
    transport = StubTransport()
    first = _client(client_type, KEYS_A, transport)
    second = _client(client_type, KEYS_B, transport)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        assert (first._fi_api_key, first._fi_secret_key) == KEYS_A
        assert (second._fi_api_key, second._fi_secret_key) == KEYS_B
    assert not caught


@pytest.mark.parametrize("owner", CLIENT_TYPES, ids=lambda cls: cls.__name__)
@pytest.mark.parametrize("name", CREDENTIAL_NAMES)
def test_class_reads_are_value_free(owner, name):
    """Expected RED: class access exposes the last client's key without warning."""
    transport = StubTransport()
    first = _client(owner, KEYS_A, transport)
    second = _client(owner, KEYS_B, transport)
    _send(first, "first")
    _send(second, "second")
    assert [_keys(call) for call in transport.calls] == [KEYS_A, KEYS_B]
    _assert_value_free_class_read(owner, name)


@pytest.mark.parametrize("name", CREDENTIAL_NAMES)
def test_uninitialized_subclass_class_reads_are_value_free(name):
    """Expected RED: an untouched subclass inherits the base class's key."""
    class UntouchedAuth(APIKeyAuth):
        pass

    _client(APIKeyAuth, KEYS_A, StubTransport())
    _assert_value_free_class_read(UntouchedAuth, name)
