"""Synthetic credentials and stub transports only; no network is needed.

Expected RED before the fix: test_class_reads_are_value_free (every parameter).
The old constructor publishes the last client's keys on its class without warning.
All other tests protect existing instance/header behavior and should already pass.
"""

from concurrent.futures import Future, ThreadPoolExecutor
import json
from threading import Barrier, Lock
from types import SimpleNamespace
import warnings

import pytest
from requests import Request, Response

from fi.api.auth import APIKeyAuth
from fi.api.types import HttpMethod, RequestConfig
from fi.evals.core import cloud_registry
from fi.evals.core.engines import TuringEngine
from fi.evals.evaluator import Evaluator
from fi.kb.client import KnowledgeBase

BASE = "http://127.0.0.1:9"
KEYS_A = ("synthetic-a-api", "synthetic-a-secret")
KEYS_B = ("synthetic-b-api", "synthetic-b-secret")
ENV_KEYS = ("synthetic-env-api", "synthetic-env-secret")
FALLBACK_KEYS = ("synthetic-fallback-api", "synthetic-fallback-secret")


class DerivedEvaluator(Evaluator):
    pass


CLIENT_TYPES = (APIKeyAuth, Evaluator, DerivedEvaluator, KnowledgeBase)


@pytest.fixture(autouse=True)
def _isolate_auth_state(_no_egress, monkeypatch):
    for name in (
        "FI_EXTRA_HEADERS", "LANGFUSE_SECRET_KEY", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_HOST",
    ):
        monkeypatch.delenv(name, raising=False)
    # Restore raw class dictionaries, including on the intentionally failing old code.
    # getattr would invoke the compatibility accessor and warn during fixture setup.
    missing = object()
    saved = [
        (owner, name, vars(owner).get(name, missing))
        for owner in CLIENT_TYPES
        for name in ("_fi_api_key", "_fi_secret_key")
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
    """FuturesSession-shaped transport that records outbound prepared headers."""

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


def test_two_clients_send_their_own_headers_in_sequence():
    transport = StubTransport()
    first = _client(APIKeyAuth, KEYS_A, transport)
    second = _client(APIKeyAuth, KEYS_B, transport)
    _send(first, "first")
    _send(second, "second")
    _send(first, "first-again")
    assert [_keys(call) for call in transport.calls] == [KEYS_A, KEYS_B, KEYS_A]


def test_two_clients_send_their_own_headers_on_concurrent_threads():
    # Rendezvous inside every send: the two clients must overlap, not just take turns.
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


def test_evaluator_subclass_sends_its_own_headers():
    transport = StubTransport(body={"result": []})
    first = _client(DerivedEvaluator, KEYS_A, transport)
    second = _client(DerivedEvaluator, KEYS_B, transport)
    assert first.list_evaluations() == []
    assert second.list_evaluations() == []
    assert first.list_evaluations() == []
    assert [_keys(call) for call in transport.calls] == [KEYS_A, KEYS_B, KEYS_A]


def test_engine_registry_getattr_uses_evaluator_instance_headers(monkeypatch):
    transport = StubTransport(body={"result": [{
        "name": "synthetic_auth_probe", "config": {"required_keys": ["output"]},
    }]})
    evaluator = _client(Evaluator, KEYS_A, transport)
    # A newer evaluator must not change the older evaluator's registry credentials.
    _client(Evaluator, KEYS_B, transport)
    engine = TuringEngine(
        fi_api_key=FALLBACK_KEYS[0], fi_secret_key=FALLBACK_KEYS[1], fi_base_url=BASE,
    )
    engine._evaluator = evaluator
    monkeypatch.setattr(cloud_registry, "_CACHE", {})
    monkeypatch.setattr(
        "requests.get", lambda url, **kwargs: transport.respond("GET", url, **kwargs),
    )
    monkeypatch.setattr(engine, "_resolve_template_class", lambda name: None)

    def evaluate(*, eval_templates, inputs, model_name, eval_config=None, _raise_on_error=False):
        assert eval_templates == "synthetic_auth_probe"
        assert eval_config is None
        assert inputs == {"output": "synthetic-output"}
        return SimpleNamespace(eval_results=[SimpleNamespace(output=1, reason="synthetic")])

    monkeypatch.setattr(evaluator, "evaluate", evaluate)
    result = engine.run("synthetic_auth_probe", {"answer": "synthetic-output"})
    assert result.score == 1.0
    assert len(transport.calls) == 1
    assert transport.calls[0].url == f"{BASE}/sdk/api/v1/get-evals/"
    assert _keys(transport.calls[0]) == KEYS_A


def test_knowledge_base_sends_its_own_headers():
    transport = StubTransport(body={"result": {"table_data": []}})
    first = _client(KnowledgeBase, KEYS_A, transport)
    second = _client(KnowledgeBase, KEYS_B, transport)
    assert first.list_kbs() == []
    assert second.list_kbs() == []
    assert first.list_kbs() == []
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


@pytest.mark.parametrize("owner", CLIENT_TYPES, ids=lambda cls: cls.__name__)
@pytest.mark.parametrize("name", ("_fi_api_key", "_fi_secret_key"))
def test_class_reads_are_value_free(owner, name):
    """Expected RED on the old constructor: class reads expose keys and do not warn."""
    transport = StubTransport()
    first = _client(owner, KEYS_A, transport)
    second = _client(owner, KEYS_B, transport)
    _send(first, "first")
    _send(second, "second")
    assert [_keys(call) for call in transport.calls] == [KEYS_A, KEYS_B]
    with warnings.catch_warnings(record=True) as instance_warnings:
        warnings.simplefilter("always", DeprecationWarning)
        assert (first._fi_api_key, first._fi_secret_key) == KEYS_A
        assert (second._fi_api_key, second._fi_secret_key) == KEYS_B
    assert not instance_warnings

    # Exercise both direct class access and the legacy getattr(..., None) idiom.
    for direct in (True, False):
        with pytest.warns(DeprecationWarning, match="read credentials from the client instance") as caught:
            if direct:
                value = owner._fi_api_key if name == "_fi_api_key" else owner._fi_secret_key
            else:
                value = getattr(owner, name, None)
            assert value is None
        assert len(caught) == 1
        assert all(
            key not in str(warning.message)
            for warning in caught
            for key in KEYS_A + KEYS_B + ENV_KEYS + FALLBACK_KEYS
        )
