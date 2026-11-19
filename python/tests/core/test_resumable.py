"""Resumable streams. Resume with no loss or duplication (durable ids
and live deltas); the idle timeout; the reconnect bound; the long-poll fallback; terminal statuses.
Sync and async."""

from __future__ import annotations

import json

import httpx
import pytest

import fi.errors as errors
from fi._core.resumable import (
    DeltaReconciler,
    StreamBounds,
    resumable_events,
    resumable_events_sync,
)
from fi._core.sse import iter_frames
from tests.core._support import Recorder, make_async_core, make_core, respond, sse

DONE = (None, "done", {"type": "done"})


class Broken(httpx.SyncByteStream, httpx.AsyncByteStream):
    """A body that sends some bytes, then fails the way a dropped connection or a stall does."""

    def __init__(self, data: bytes, error: Exception) -> None:
        self.data, self.error = data, error

    def __iter__(self):
        yield self.data
        raise self.error

    async def __aiter__(self):
        yield self.data
        raise self.error


def frames(*items) -> bytes:
    out = []
    for frame_id, event, data in items:
        if frame_id is not None:
            out.append(f"id: {frame_id}")
        out += [f"event: {event}", f"data: {json.dumps(data)}", ""]
    return ("\n".join(out) + "\n").encode()


def dropped(*items, error=None) -> httpx.Response:
    return httpx.Response(
        200,
        stream=Broken(frames(*items), error or httpx.ReadError("connection reset")),
        headers={"content-type": "text/event-stream"},
    )


def status(seq, value):
    return (str(seq), "status", {"seq": seq, "status": value})


def _events(core, **kw):
    return list(
        resumable_events_sync(core, "runs.events", path={"id": "c1"}, is_end=lambda e: e["type"] == "done", **kw)
    )


def test_resume_after_a_drop_loses_nothing_and_repeats_nothing():
    rec = Recorder(dropped(status(1, "a"), status(2, "b")), sse(status(2, "b"), status(3, "c"), DONE))
    events = _events(make_core(rec))
    assert [e.get("seq") for e in events] == [1, 2, 3, None] and events[-1]["type"] == "done"
    assert rec.requests[0].headers.get("Last-Event-ID") is None
    assert rec.requests[1].headers["Last-Event-ID"] == "2"
    assert all(r.headers["Accept"] == "text/event-stream" for r in rec.requests)


def test_a_caller_resumes_from_its_own_last_event_id():
    rec = Recorder(sse(status(8, "x"), DONE))
    _events(make_core(rec), last_event_id="7")
    assert rec.requests[0].headers["Last-Event-ID"] == "7"


def test_live_deltas_are_reconciled_across_a_reconnect():
    first = dropped((None, "message_delta", {"messageId": "m1", "delta": "Hel"}))
    second = sse(
        (None, "message_delta", {"messageId": "m1", "delta": "Hello"}),  # the server re-seeds cumulatively
        (None, "message_delta", {"messageId": "m1", "delta": " world"}),
        DONE,
    )
    events = _events(make_core(Recorder(first, second)))
    assert "".join(e["delta"] for e in events if e["type"] == "message_delta") == "Hello world"


def test_a_regenerated_message_is_a_message_reset():
    rec = DeltaReconciler()
    rec.push({"type": "message_delta", "messageId": "m", "delta": "draft"})
    rec.new_connection()
    assert rec.push({"type": "message_delta", "messageId": "m", "delta": "final"}) == [
        {"type": "message_reset", "messageId": "m", "text": "final"}
    ]
    assert rec.push({"type": "message_delta", "messageId": "m", "delta": "!"})[0]["delta"] == "!"
    rec.push({"type": "activity_output", "stepId": "s", "stream": "stdout", "chunk": "abcdef"})
    rec.new_connection()
    assert (
        rec.push({"type": "activity_output", "stepId": "s", "stream": "stdout", "chunk": "defgh"})[0]["chunk"] == "gh"
    )
    rec.new_connection()
    out = rec.push({"type": "activity_output", "stepId": "s", "stream": "stdout", "chunk": "zzz"})[0]
    assert out["chunk"] == "zzz" and out["truncated"] is True


def test_the_idle_timeout_is_the_read_timeout_and_a_stall_raises_api_timeout():
    rec = Recorder(sse(DONE))
    _events(make_core(rec), bounds=StreamBounds(idle_timeout=12.5, transport="sse"))
    assert rec.requests[0].extensions["timeout"]["read"] == 12.5
    stalled = dropped(status(1, "a"), error=httpx.ReadTimeout("no data"))
    with pytest.raises(errors.APITimeoutError) as info:
        list(
            iter_frames(
                make_core(Recorder(stalled)).open_stream("runs.events", path={"id": "c1"}).response,
                operation="runs.events",
            )
        )
    assert "idle timeout" in str(info.value)


def test_a_stall_reconnects_and_resumes():
    rec = Recorder(dropped(status(1, "a"), error=httpx.ReadTimeout("no data")), sse(status(2, "b"), DONE))
    assert [e.get("seq") for e in _events(make_core(rec))] == [1, 2, None]
    assert rec.requests[1].headers["Last-Event-ID"] == "1"


def test_the_reconnect_bound_raises_stream_interrupted_with_the_last_sequence():
    rec, sleeps = Recorder(dropped(status(4, "a")), dropped(), dropped(), dropped()), []
    with pytest.raises(errors.StreamInterruptedError) as info:
        _events(make_core(rec, sleeps=sleeps), bounds=StreamBounds(max_consecutive_failures=3, transport="sse"))
    assert info.value.last_sequence == "4" and len(rec.requests) == 4
    assert len(sleeps) == 2 and all(0 <= s <= 8 for s in sleeps)  # jittered backoff between failures
    rec = Recorder(*[dropped(status(n, "x")) for n in range(1, 20)])
    with pytest.raises(errors.StreamInterruptedError) as info:
        _events(make_core(rec), bounds=StreamBounds(max_reconnects=5, transport="sse"))
    assert info.value.last_sequence == "6"


def test_auto_switches_to_long_poll_after_two_silent_sse_attempts():
    def empty(request):
        return httpx.Response(200, content=b"", headers={"content-type": "text/event-stream"})

    rec = Recorder(empty, empty, sse(status(1, "a"), DONE))
    events = _events(make_core(rec))
    assert [e.get("seq") for e in events] == [1, None]
    assert [r.url.params.get("transport") for r in rec.requests] == [None, None, "poll"]
    assert rec.requests[2].url.params["wait"] == "25000"
    assert rec.requests[2].extensions["timeout"]["read"] == 45.0 + 25.0  # idle plus the poll window


def test_poll_can_be_forced():
    rec = Recorder(sse(DONE))
    _events(make_core(rec), bounds=StreamBounds(transport="poll", poll_wait=10))
    assert rec.requests[0].url.params["transport"] == "poll" and rec.requests[0].url.params["wait"] == "10000"


@pytest.mark.parametrize(
    "code, cls", [(401, errors.AuthenticationError), (403, errors.PermissionDeniedError), (404, errors.NotFoundError)]
)
def test_a_401_403_or_404_on_reconnect_is_terminal(code, cls):
    rec = Recorder(dropped(status(1, "a")), respond(code, {"code": "nope"}))
    with pytest.raises(cls):
        _events(make_core(rec))
    assert len(rec.requests) == 2


def test_unknown_events_are_yielded_never_raised():
    rec = Recorder(sse(("1", "hologram", {"a": 1}), DONE))
    events = _events(make_core(rec))
    assert events[0] == {"type": "unknown", "eventType": "hologram", "raw": {"a": 1}}


def test_streams_are_never_retried_by_the_transport():
    rec = Recorder(respond(503), sse(DONE))
    with pytest.raises(errors.ServerError):
        make_core(rec).open_stream("runs.events", path={"id": "c1"})
    assert len(rec.requests) == 1 and rec.requests[0].extensions["fi.retry"]["retries"] == 0


def test_a_non_stream_operation_is_refused():
    with pytest.raises(errors.ConfigurationError):
        list(resumable_events_sync(make_core(Recorder(sse(DONE))), "runs.get"))


@pytest.mark.anyio
async def test_async_resume_and_bound():
    rec = Recorder(dropped(status(1, "a"), status(2, "b")), sse(status(2, "b"), status(3, "c"), DONE))
    core = make_async_core(rec)
    seen = [
        e.get("seq")
        async for e in resumable_events(core, "runs.events", path={"id": "c1"}, is_end=lambda e: e["type"] == "done")
    ]
    assert seen == [1, 2, 3, None] and rec.requests[1].headers["Last-Event-ID"] == "2"
    rec = Recorder(dropped(), dropped(), dropped())
    with pytest.raises(errors.StreamInterruptedError):
        async for _ in resumable_events(
            make_async_core(rec),
            "runs.events",
            path={"id": "c1"},
            bounds=StreamBounds(max_consecutive_failures=2, transport="sse"),
        ):
            pass
