"""Credential isolation and bounded registry caching; HTTP is entirely synthetic.

EXPECTED_RED on the pre-fix source: prefix collisions, changed secrets, raw key
material, digest framing, TTL expiry, redirects, unsuccessful/malformed bodies,
and a failed forced refresh retaining an earlier successful entry.
EXPECTED_RED on round 1: overlapping fills can publish after a refresh/rejection,
and a late rejection leaves a concurrently published success available.
EXPECTED_RED on round 2: explicit clears and session close do not revoke fills,
so in-flight successes repopulate the cleared cache (including a closed session).
"""
import hashlib
import inspect
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from types import SimpleNamespace

import httpx
import pytest
import requests

from fi.evals._client_transport import _BorrowedSession
from fi.evals.core import cloud_registry as registry


BASE = "http://127.0.0.1:9"
KEY_A = "test-api-000" + "a" * 20
KEY_B = "test-api-000" + "b" * 20
SECRET_A = "test-secret-" + "c" * 20
SECRET_B = "test-secret-" + "d" * 20


def _digest(api_key, secret_key):
    parts = [(value or "").encode("utf-8") for value in (api_key, secret_key)]
    return hashlib.sha256(b"".join(len(part).to_bytes(8, "big") + part for part in parts)).hexdigest()


@pytest.fixture(params=["module", "session"])
def cache_io(request, monkeypatch):
    """Exercise both requests and the real borrowed-session cache path offline."""
    state = SimpleNamespace(calls=[], replies=[], now=100.0)
    monkeypatch.setattr(registry, "_CACHE", getattr(registry, "_RegistryCache", dict)())
    monkeypatch.setattr(registry, "_PENDING_FILLS", {}, raising=False)
    # raising=False lets the expiry assertion, not fixture setup, fail on the old source.
    monkeypatch.setattr(registry, "monotonic", lambda: state.now, raising=False)

    def respond(url, headers):
        state.calls.append((str(url), dict(headers)))
        reply = state.replies.pop(0) if state.replies else (
            200, {"status": True, "result": [{"name": f"template-{len(state.calls)}"}]}
        )
        if callable(reply):
            reply = reply()
        if isinstance(reply, Exception):
            raise reply
        status, body = reply
        response = requests.Response()
        response.status_code = status
        response.url = str(url)
        response._content = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        response.headers["Content-Type"] = "application/json"
        return response

    def get(url, *, headers, timeout):
        assert timeout == 30
        return respond(url, headers)

    def send(request):
        response = respond(request.url, request.headers)
        return httpx.Response(response.status_code, content=response.content,
                              headers=response.headers, request=request)

    monkeypatch.setattr(requests, "get", get)
    with httpx.Client(transport=httpx.MockTransport(send)) as client:
        session = _BorrowedSession(lambda: client) if request.param == "session" else None
        state.session = session
        state.cache = registry._CACHE if session is None else session.registry_cache

        def load(api_key=KEY_A, secret_key=SECRET_A, base_url=BASE, **kwargs):
            return registry.load_registry(base_url, api_key, secret_key, session=session, **kwargs)

        state.load = load
        yield state
        if session is not None:
            session.close()


def _assert_credentials(call, api_key, secret_key):
    headers = {key.lower(): value for key, value in call[1].items()}
    assert headers["x-api-key"] == api_key
    assert headers["x-secret-key"] == secret_key


def test_same_prefix_full_api_keys_are_isolated(cache_io):
    # EXPECTED_RED: the old cache keeps only the first twelve API-key characters.
    assert KEY_A[:12] == KEY_B[:12] and KEY_A != KEY_B
    first = cache_io.load()
    second = cache_io.load(api_key=KEY_B)
    assert first == {"template-1": {"name": "template-1"}}
    assert second == {"template-2": {"name": "template-2"}}
    assert len(cache_io.calls) == 2
    _assert_credentials(cache_io.calls[0], KEY_A, SECRET_A)
    _assert_credentials(cache_io.calls[1], KEY_B, SECRET_A)


def test_full_secret_keys_are_isolated(cache_io):
    # EXPECTED_RED: the old cache ignores the secret entirely.
    first = cache_io.load()
    second = cache_io.load(secret_key=SECRET_B)
    assert first != second
    assert len(cache_io.calls) == 2
    _assert_credentials(cache_io.calls[0], KEY_A, SECRET_A)
    _assert_credentials(cache_io.calls[1], KEY_A, SECRET_B)


def test_wrong_secret_reaches_server_instead_of_cached_templates(cache_io):
    # EXPECTED_RED: the old cache bypasses authentication for a different secret.
    assert cache_io.load()
    cache_io.replies.append((403, {"detail": "synthetic denial"}))
    assert cache_io.load(secret_key=SECRET_B) == {}
    assert len(cache_io.calls) == 2
    _assert_credentials(cache_io.calls[1], KEY_A, SECRET_B)
    assert cache_io.load(secret_key=SECRET_B) == {"template-3": {"name": "template-3"}}
    assert len(cache_io.calls) == 3


@pytest.mark.parametrize("suffix", ["", "/", "///"])
def test_identical_credentials_and_normalized_url_hit(cache_io, suffix):
    first = cache_io.load()
    assert cache_io.load(base_url=BASE + suffix) is first
    assert len(cache_io.calls) == 1
    assert cache_io.calls[0][0] == BASE + "/sdk/api/v1/get-evals/"
    assert len(cache_io.cache) == 1


def test_different_base_urls_are_isolated(cache_io):
    first = cache_io.load()
    other_base = BASE + "/other"
    second = cache_io.load(base_url=other_base + "/")
    assert second != first
    assert cache_io.load(base_url=other_base) is second
    assert len(cache_io.calls) == 2
    assert cache_io.calls[1][0] == other_base + "/sdk/api/v1/get-evals/"


def test_cache_keys_retain_no_raw_credential_material(cache_io):
    # EXPECTED_RED: the old tuple contains a raw twelve-character API-key prefix.
    cache_io.load()
    assert len(cache_io.cache) == 1
    forbidden = {value for value in (KEY_A, SECRET_A)}
    forbidden.update(value[i:i + 8] for value in (KEY_A, SECRET_A)
                     for i in range(len(value) - 7))
    for key in cache_io.cache:
        # Exact built-in types make this exhaustive: no object attributes hide credentials.
        assert type(key) is tuple and len(key) == 2
        assert all(type(part) is str for part in key)
        for part in key:
            assert all(fragment not in part for fragment in forbidden)
        assert key == (BASE, _digest(KEY_A, SECRET_A))


def test_digest_frames_full_credentials_unambiguously():
    # EXPECTED_RED: the old helper neither accepts nor hashes a secret.
    cache_key = getattr(registry, "_cache_key", None)
    assert callable(cache_key), "registry must provide a callable _cache_key"
    assert "secret_key" in inspect.signature(cache_key).parameters, "cache key must accept the secret"
    pairs = [("a", "bc"), ("ab", "c"), ("a\0", "b"), ("a", "\0b"), ("é", "密")]
    keys = [registry._cache_key(BASE + "/", api, secret) for api, secret in pairs]
    assert len(set(keys)) == len(pairs)
    for key, (api, secret) in zip(keys, pairs):
        assert key == (BASE, _digest(api, secret))
    assert registry._cache_key(BASE, None, None) == registry._cache_key(BASE, "", "")


def test_cache_expires_at_monotonic_ttl_without_sleep(cache_io):
    # EXPECTED_RED: the old cache has no expiration.
    first = cache_io.load()
    ttl = getattr(registry, "CACHE_TTL_SECONDS", 300)
    assert 0 < ttl <= 300
    cache_io.now += ttl - 1
    assert cache_io.load() is first
    assert len(cache_io.calls) == 1
    cache_io.now += 1
    second = cache_io.load()
    assert second != first
    assert len(cache_io.calls) == 2
    assert cache_io.load() is second
    assert len(cache_io.calls) == 2


def test_force_refresh_bypasses_live_entry(cache_io):
    first = cache_io.load()
    second = cache_io.load(force_refresh=True)
    assert second != first
    assert cache_io.load() is second
    assert len(cache_io.calls) == 2


@pytest.mark.parametrize("status", [401, 403, 429, 500, 503])
def test_http_failures_are_never_cached(cache_io, status):
    cache_io.replies.append((status, {"detail": "synthetic failure"}))
    assert cache_io.load() == {}
    assert cache_io.cache == {}
    assert cache_io.load() == {"template-2": {"name": "template-2"}}
    assert len(cache_io.calls) == 2


@pytest.mark.parametrize("status", [301, 302, 304])
def test_non_success_redirects_are_never_cached(cache_io, status):
    # EXPECTED_RED: requests.raise_for_status does not reject 3xx responses.
    cache_io.replies.append((status, {"status": True, "result": [{"name": "not-success"}]}))
    assert cache_io.load() == {}
    assert cache_io.cache == {}
    assert cache_io.load() == {"template-2": {"name": "template-2"}}
    assert len(cache_io.calls) == 2


@pytest.mark.parametrize("body", [
    {"status": False, "result": [{"name": "not-success"}]},
    {"detail": "synthetic failure"},
    {"status": True, "result": {}},
    {"status": True, "result": [None]},
    ["not-an-envelope"],
])
def test_unsuccessful_or_malformed_bodies_are_never_cached(cache_io, body):
    # EXPECTED_RED: old code caches some failures and lets other parsing errors escape.
    cache_io.replies.append((200, body))
    result = None
    error = None
    try:
        result = cache_io.load()
    except AttributeError as exc:
        error = exc
    assert error is None, "malformed registry bodies must return {} without raising AttributeError"
    assert result == {}
    assert cache_io.cache == {}
    assert cache_io.load() == {"template-2": {"name": "template-2"}}
    assert len(cache_io.calls) == 2


def test_invalid_json_is_not_cached(cache_io):
    cache_io.replies.append((200, b"not-json"))
    assert cache_io.load() == {}
    assert cache_io.cache == {}
    assert cache_io.load() == {"template-2": {"name": "template-2"}}
    assert len(cache_io.calls) == 2


def test_successful_empty_registry_is_cached(cache_io):
    cache_io.replies.append((200, {"status": True, "result": []}))
    first = cache_io.load()
    assert first == {}
    assert cache_io.load() is first
    assert len(cache_io.calls) == 1


def test_failed_force_refresh_discards_previous_entry(cache_io):
    # EXPECTED_RED: the old cache retains an earlier success after an explicit denial.
    assert cache_io.load()
    cache_io.replies.append((401, {"detail": "synthetic revocation"}))
    assert cache_io.load(force_refresh=True) == {}
    assert cache_io.cache == {}
    assert cache_io.load() == {"template-3": {"name": "template-3"}}
    assert len(cache_io.calls) == 3


def test_expired_entry_is_not_used_after_failed_fetch(cache_io):
    # EXPECTED_RED: the old cache never reaches the server after expiry.
    assert cache_io.load()
    cache_io.now += getattr(registry, "CACHE_TTL_SECONDS", 300)
    cache_io.replies.append((403, {"detail": "synthetic revocation"}))
    assert cache_io.load() == {}
    assert cache_io.cache == {}
    assert cache_io.load() == {"template-3": {"name": "template-3"}}
    assert len(cache_io.calls) == 3


def test_logs_and_failure_handling_do_not_expose_credentials_or_digest(cache_io, caplog):
    digest = _digest(KEY_A, SECRET_A)
    with caplog.at_level(logging.DEBUG):
        assert cache_io.load()
        cache_io.replies.append(RuntimeError(" ".join((KEY_A, SECRET_A, digest))))
        # No exception containing the injected material may escape the registry call.
        assert cache_io.load(force_refresh=True) == {}
    assert "RuntimeError" in caplog.text
    assert "Loaded 1 cloud eval templates" in caplog.text
    for value in (KEY_A, SECRET_A, digest):
        assert value not in caplog.text
    for value in (KEY_A, SECRET_A):
        assert all(value[i:i + 8] not in caplog.text for i in range(len(value) - 7))
    assert cache_io.load() == {"template-3": {"name": "template-3"}}
    assert len(cache_io.calls) == 3


def _overlapping_loads(cache_io, replies, completion_order, *, force_refresh=True,
                       before_release=None, second_api_key=KEY_A):
    entered, release = [Event(), Event()], [Event(), Event()]
    results = [None, None]

    def gated(index, reply):
        def respond():
            entered[index].set()
            assert release[index].wait(5), "synthetic response was not released"
            return reply
        return respond

    cache_io.replies.extend(gated(index, reply) for index, reply in enumerate(replies))
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(cache_io.load)]
        try:
            assert entered[0].wait(5), "first synthetic request did not start"
            futures.append(pool.submit(cache_io.load, api_key=second_api_key,
                                       force_refresh=force_refresh))
            assert entered[1].wait(5), "second synthetic request did not start"
            if before_release is not None:
                before_release()
            for index in completion_order:
                release[index].set()
                results[index] = futures[index].result(timeout=5)
        finally:
            for event in release:
                event.set()
    assert len(cache_io.calls) == 2
    assert registry._PENDING_FILLS == {}
    return results


@pytest.mark.parametrize("second_api_key", [KEY_A, KEY_B])
@pytest.mark.parametrize("force_refresh", [False, True])
@pytest.mark.parametrize("rejection_first", [False, True])
@pytest.mark.parametrize("rejection", [
    pytest.param((401, {"detail": "synthetic denial"}), id="401"),
    pytest.param((403, {"detail": "synthetic denial"}), id="403"),
    pytest.param((500, {"detail": "synthetic failure"}), id="500"),
    pytest.param((302, {"result": []}), id="redirect"),
    pytest.param((200, {"status": False, "result": []}), id="unsuccessful-body"),
    pytest.param(RuntimeError("synthetic failure"), id="transport-error"),
])
def test_inflight_success_cannot_publish_after_rejection(
    cache_io, rejection, rejection_first, force_refresh, second_api_key
):
    # EXPECTED_RED r1: rejection must invalidate successes already in flight,
    # whether the rejected request started before or after the successful one.
    # EXPECTED_RED r2 for distinct keys: rejection must invalidate the whole cache.
    success = (200, {"status": True, "result": [{"name": "stale"}]})
    replies = [rejection, success] if rejection_first else [success, rejection]
    failed = 0 if rejection_first else 1
    results = _overlapping_loads(cache_io, replies, [failed, 1 - failed],
                                 force_refresh=force_refresh, second_api_key=second_api_key)
    assert results[failed] == {}
    assert results[1 - failed] == {"stale": {"name": "stale"}}
    assert cache_io.cache == {}
    fresh = cache_io.load()
    assert fresh == {"template-3": {"name": "template-3"}}
    assert cache_io.load() is fresh
    assert len(cache_io.calls) == 3


def test_inflight_success_cannot_replace_forced_refresh(cache_io):
    # EXPECTED_RED r1: the older fill otherwise overwrites the refreshed result.
    older, newer = _overlapping_loads(cache_io, [
        (200, {"status": True, "result": [{"name": "older"}]}),
        (200, {"status": True, "result": [{"name": "newer"}]}),
    ], [1, 0])
    assert older == {"older": {"name": "older"}}
    assert newer == {"newer": {"name": "newer"}}
    assert cache_io.load() is newer
    assert len(cache_io.calls) == 2


@pytest.mark.parametrize("status", [401, 403])
def test_late_rejection_invalidates_concurrently_published_success(cache_io, status):
    # EXPECTED_RED r1: a failure must also remove a success published while it waited.
    failed, succeeded = _overlapping_loads(cache_io, [
        (status, {"detail": "synthetic denial"}),
        (200, {"status": True, "result": [{"name": "revoked"}]}),
    ], [1, 0])
    assert failed == {}
    assert succeeded == {"revoked": {"name": "revoked"}}
    assert cache_io.cache == {}
    assert cache_io.load() == {"template-3": {"name": "template-3"}}
    assert len(cache_io.calls) == 3


@pytest.mark.parametrize("cache_io,action", [
    ("module", "clear"), ("session", "clear"), ("session", "close"),
], indirect=["cache_io"])
@pytest.mark.parametrize("completion_order", [[0, 1], [1, 0]])
def test_inflight_success_cannot_publish_after_clear_or_close(cache_io, action, completion_order):
    # EXPECTED_RED r2: neither clear nor close revokes these two distinct keys' fills.
    invalidate = cache_io.session.close if action == "close" else cache_io.cache.clear
    older, newer = _overlapping_loads(cache_io, [
        (200, {"status": True, "result": [{"name": "older"}]}),
        (200, {"status": True, "result": [{"name": "newer"}]}),
    ], completion_order, force_refresh=False, before_release=invalidate, second_api_key=KEY_B)
    assert older == {"older": {"name": "older"}}
    assert newer == {"newer": {"name": "newer"}}
    assert cache_io.cache == {}
    if action == "close":
        assert cache_io.session.closed
        assert cache_io.load() == cache_io.load(api_key=KEY_B) == {}
        assert cache_io.cache == {} and len(cache_io.calls) == 2
    else:
        fresh = cache_io.load()
        assert fresh == {"template-3": {"name": "template-3"}}
        assert cache_io.load() is fresh
        assert len(cache_io.calls) == 3
