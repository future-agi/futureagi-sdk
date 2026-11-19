"""The four retry classes, read from the contract, on the platform executor.

keyed (same key on every attempt, a 409 in progress waits); keyed-not-durable (no 5xx retry);
http-idempotent (the core clients' default); unsafe (429 only, plus pre-send connect errors); a 404 on a retry
of sandboxes.kill is success; Retry-After is honoured. Sync and async."""

from __future__ import annotations

import uuid

import httpx
import pytest

import fi.errors as errors
from fi._core.policy import counts, retry_class_of
from tests.core._support import OPS, Recorder, make_async_core, make_core, respond

IN_PROGRESS = {"code": "idempotency_key_in_progress", "message": "still running"}


def test_retry_class_comes_from_the_contract_flags():
    assert retry_class_of(OPS["runs.create"]) == "keyed"
    assert retry_class_of(OPS["environments.create"]) == "keyed-not-durable"
    assert retry_class_of(OPS["runs.get"]) == "http-idempotent"
    assert retry_class_of(OPS["sandboxes.kill"]) == "http-idempotent"
    assert retry_class_of(OPS["files.write"]) == "http-idempotent"
    assert retry_class_of(OPS["sandboxes.create"]) == "unsafe"
    assert counts(OPS)["keyed"] == 1 and counts(OPS)["stream"] == 1 and counts(OPS)["paginated"] == 2


def test_the_retry_class_reaches_the_transport_on_every_request():
    rec = Recorder(respond(200, {}))
    core = make_core(rec)
    core.call("runs.get", path={"id": "c1"})
    core.call("sandboxes.create", body={})
    assert [r.extensions["fi.retry"]["class"] for r in rec.requests] == ["http-idempotent", "unsafe"]


@pytest.mark.parametrize("status", [429, 502, 503, 504])
def test_keyed_retries_with_the_same_key_on_every_attempt(status):
    rec, sleeps = Recorder(respond(status), respond(status), respond(201, {"id": "c1"})), []
    data, meta = make_core(rec, sleeps=sleeps).call_with_meta("runs.create", body={"agentId": "a"})
    assert data == {"id": "c1"} and len(rec.requests) == 3
    key = rec.keys[0]
    assert uuid.UUID(key).version == 4 and rec.keys == [key, key, key]
    assert meta.idempotency_key == key and meta.attempts == 3 and len(sleeps) == 2


def test_keyed_uses_the_callers_key_and_refuses_one_on_an_operation_without_keys():
    rec = Recorder(respond(201, {"id": "c1"}))
    core = make_core(rec)
    core.call("runs.create", body={}, idempotency_key="ci-abc123")
    assert rec.keys == ["ci-abc123"]
    with pytest.raises(errors.ConfigurationError) as info:
        core.call("sandboxes.create", body={}, idempotency_key="ci-abc123")
    assert info.value.code == "idempotency_not_supported" and len(rec.requests) == 1
    with pytest.raises(errors.ConfigurationError):
        core.call("runs.create", body={}, idempotency_key="has a space")


def test_keyed_409_in_progress_waits_for_retry_after_then_resends_the_same_key():
    rec, sleeps = (
        Recorder(
            respond(409, IN_PROGRESS, {"Retry-After": "2"}), respond(409, IN_PROGRESS), respond(201, {"id": "c1"})
        ),
        [],
    )
    data, meta = make_core(rec, sleeps=sleeps).call_with_meta("runs.create", body={})
    assert data == {"id": "c1"}
    assert sleeps == [2.0, 1.0]  # Retry-After, then the 1 s default
    assert len(set(rec.keys)) == 1 and len(rec.requests) == 3 and meta.attempts == 3


def test_a_409_in_progress_past_the_wait_cap_raises_with_the_key():
    rec = Recorder(respond(409, IN_PROGRESS, {"Retry-After": "600"}))
    with pytest.raises(errors.IdempotencyKeyInProgressError) as info:
        make_core(rec).call("runs.create", body={})
    assert info.value.retry_after == 600.0 and info.value.idempotency_key == rec.keys[0]
    assert len(rec.requests) == 1


def test_a_409_in_progress_on_an_unkeyed_call_is_not_waited_out():
    rec = Recorder(respond(409, IN_PROGRESS))
    with pytest.raises(errors.IdempotencyKeyInProgressError):
        make_core(rec).call("sandboxes.create", body={})
    assert len(rec.requests) == 1


@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_keyed_not_durable_never_retries_a_5xx(status):
    rec = Recorder(respond(status), respond(201, {}))
    with pytest.raises(errors.ServerError) as info:
        make_core(rec).call("environments.create", body={})
    assert len(rec.requests) == 1 and info.value.idempotency_key == rec.keys[0]


def test_keyed_not_durable_retries_429_and_pre_send_errors_with_the_same_key():
    connect = httpx.ConnectError("refused")
    rec = Recorder(connect, respond(429, None, {"Retry-After": "0"}), respond(201, {"id": "e1"}))
    assert make_core(rec).call("environments.create", body={}) == {"id": "e1"}
    assert len(rec.requests) == 3 and len(set(rec.keys)) == 1


def test_keyed_not_durable_does_not_retry_a_lost_connection():
    rec = Recorder(httpx.ReadError("reset"), respond(201, {}))
    with pytest.raises(errors.APIConnectionError) as info:
        make_core(rec).call("environments.create", body={})
    assert len(rec.requests) == 1 and info.value.possibly_applied and info.value.idempotency_key == rec.keys[0]


@pytest.mark.parametrize("status", [502, 503, 504])
def test_http_idempotent_retries_gateway_errors(status):
    rec = Recorder(respond(status), respond(200, {"id": "c1"}))
    assert make_core(rec).call("runs.get", path={"id": "c1"}) == {"id": "c1"}
    assert len(rec.requests) == 2 and rec.keys == [None, None]


def test_http_idempotent_does_not_retry_a_500():
    rec = Recorder(respond(500), respond(200, {}))
    with pytest.raises(errors.ServerError):
        make_core(rec).call("runs.get", path={"id": "c1"})
    assert len(rec.requests) == 1


@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_unsafe_never_retries_a_5xx(status):
    rec = Recorder(respond(status), respond(201, {}))
    with pytest.raises(errors.ServerError):
        make_core(rec).call("sandboxes.create", body={})
    assert len(rec.requests) == 1  # sandboxes.create makes one attempt on a 5xx until EE-1


def test_unsafe_retries_429_and_pre_send_connect_errors_only():
    rec = Recorder(respond(429), httpx.ConnectError("refused"), respond(201, {"id": "s1"}))
    assert make_core(rec).call("sandboxes.create", body={}) == {"id": "s1"}
    assert len(rec.requests) == 3
    for after_send in (httpx.ReadError("reset"), httpx.RemoteProtocolError("closed"), httpx.ReadTimeout("slow")):
        rec = Recorder(after_send, respond(201, {}))
        with pytest.raises(errors.APIConnectionError) as info:
            make_core(rec).call("sandboxes.create", body={})
        assert len(rec.requests) == 1 and info.value.possibly_applied


def test_sandboxes_kill_404_on_a_retry_is_success():
    rec = Recorder(httpx.ReadError("reset after send"), respond(404, {"code": "not_found"}))
    data, meta = make_core(rec).call_with_meta("sandboxes.kill", path={"id": "sb1"})
    assert data is None and meta.already_applied and meta.attempts == 2
    rec = Recorder(respond(503), respond(404, {"code": "not_found"}))
    assert make_core(rec).call_with_meta("sandboxes.kill", path={"id": "sb1"})[1].already_applied


def test_sandboxes_kill_404_on_the_first_attempt_or_after_a_429_is_not_found():
    for answers in ((respond(404, {"code": "not_found"}),), (respond(429), respond(404, {"code": "not_found"}))):
        rec = Recorder(*answers)
        with pytest.raises(errors.NotFoundError):
            make_core(rec).call("sandboxes.kill", path={"id": "sb1"})


def test_a_404_on_a_retry_of_another_operation_is_not_success():
    rec = Recorder(respond(503), respond(404, {"code": "not_found"}))
    with pytest.raises(errors.NotFoundError):
        make_core(rec).call("runs.get", path={"id": "c1"})


def test_retry_after_is_honoured_in_seconds_and_as_a_date():
    rec, sleeps = Recorder(respond(429, None, {"Retry-After": "3"}), respond(200, {})), []
    make_core(rec, sleeps=sleeps).call("runs.get", path={"id": "c1"})
    assert sleeps == [3.0]
    rec, sleeps = Recorder(respond(429, None, {"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"}), respond(200, {})), []
    make_core(rec, sleeps=sleeps).call("runs.get", path={"id": "c1"})
    assert sleeps == [0.0]  # a date in the past: no wait


def test_retries_are_bounded_and_a_spent_429_raises_rate_limit_with_its_hint():
    rec = Recorder(respond(429, {"error": "omega_rate_limited", "requestId": "r-1"}, {"Retry-After": "1"}))
    with pytest.raises(errors.RateLimitError) as info:
        make_core(rec, retries=2).call("runs.get", path={"id": "c1"})
    assert len(rec.requests) == 3 and info.value.retry_after == 1.0 and info.value.request_id == "r-1"
    assert info.value.code == "omega_rate_limited"


def test_per_call_retries_override():
    rec = Recorder(respond(503))
    with pytest.raises(errors.ServerError):
        make_core(rec).call("runs.get", path={"id": "c1"}, retries=0)
    assert len(rec.requests) == 1


@pytest.mark.anyio
async def test_async_twin_keyed_wait_and_kill():
    rec, sleeps = Recorder(respond(503), respond(409, IN_PROGRESS), respond(201, {"id": "c1"})), []
    core = make_async_core(rec, sleeps=sleeps)
    data, meta = await core.call_with_meta("runs.create", body={})
    assert data == {"id": "c1"} and len(set(rec.keys)) == 1 and sleeps[-1] == 1.0 and meta.attempts == 3
    rec = Recorder(httpx.ReadError("reset"), respond(404, {"code": "not_found"}))
    data, meta = await make_async_core(rec).call_with_meta("sandboxes.kill", path={"id": "sb1"})
    assert data is None and meta.already_applied
    rec = Recorder(respond(503), respond(201, {}))
    with pytest.raises(errors.ServerError):
        await make_async_core(rec).call("sandboxes.create", body={})
    assert len(rec.requests) == 1
