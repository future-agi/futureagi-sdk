"""The Responses API through agentcc-gateway the recorded source (D-17: typed events and errors).

The gateway relays /v1/responses to the provider as written (handlers_responses.go).
Its output checks run on the assembled answer after the stream ends, so a refused
answer reaches the client in full, blocked text included, and the gateway then
appends its own ``event: error`` frame (responsesStreamErrorEvent): the answer is not
withheld. An upstream's own ``event: error`` is relayed unchanged. fi.gateway must
yield typed ResponseStreamEvent items and raise StreamError, with type, code and
param, on either error frame.
"""

from __future__ import annotations

import pytest

from ._live import Live, data_frames

MODEL = "gpt-4o-mini"


def _events(stream) -> tuple[list[str], object]:
    from fi.gateway import StreamError

    types = []
    try:
        for ev in stream:
            types.append(ev.type)
    except StreamError as e:
        return types, e
    return types, None


def test_responses_create(live: Live, client) -> None:
    r = client.responses.create(model=MODEL, input=f"hi {live.marker()}")
    text = "".join(p.text or "" for o in r.output for p in o.content)
    live.record("d17_responses_create", {"id": r.id, "status": r.status, "text": text,
                                         "usage": r.usage and r.usage.model_dump()})
    assert r.status == "completed"
    assert text == "Hi there"


def test_responses_stream_yields_typed_events_d17(live: Live, client) -> None:
    types, err = _events(client.responses.create(model=MODEL, input=f"hi {live.marker()}", stream=True))
    live.record("d17_responses_stream", {"types": types, "error": err and str(err)})
    assert err is None
    assert types == ["response.created", "response.output_text.delta", "response.output_text.delta",
                     "response.output_text.done", "response.completed"]


def test_upstream_event_error_raises_stream_error_d17(live: Live, client) -> None:
    types, err = _events(client.responses.create(model=MODEL, input=f"[[mock:resp-error]] {live.marker()}",
                                                 stream=True))
    live.record("d17_upstream_event_error", {"types": types, "error": err and {
        "message": str(err), "type": err.type, "code": err.code, "param": err.param, "body": err.body}})
    assert err is not None
    assert (err.type, err.code, err.param) == ("error", "mock_upstream_error", None)
    assert str(err) == "the mock upstream failed mid-stream"
    assert types == ["response.created", "response.output_text.delta"]


def test_gateway_event_error_after_the_relayed_blocked_answer_raises_stream_error_d17(live: Live, client) -> None:
    """The gateway's own frame: the keyword guardrail reads the assembled answer at the
    end, after the whole answer, blocked word included, was relayed; then its flat
    ``event: error`` frame (code content_blocked) raises StreamError(type, code, param)."""
    m = live.marker()
    status, headers, lines = live.sse("/v1/responses", {"model": MODEL, "input": f"[[mock:block]] {m}",
                                                        "stream": True})
    raw_error = [ln for ln in lines if ln.startswith("event: error")]
    types, err = _events(client.responses.create(model=MODEL, input=f"[[mock:block]] {live.marker()}", stream=True))
    live.record("d17_gateway_event_error", {
        "status": status, "raw_lines": lines, "raw_error_events": raw_error, "data_frames": data_frames(lines),
        "sdk_types": types, "sdk_error": err and {"message": str(err), "type": err.type, "code": err.code,
                                                   "param": err.param, "body": err.body}})
    assert status == 200 and len(raw_error) == 1
    assert err is not None
    assert (err.type, err.code, err.param) == ("error", "content_blocked", None)
    assert err.body.get("type") == "error"
    assert "response.completed" in types  # the frame comes after the relayed stream, at its end
    error_at = next(i for i, ln in enumerate(lines) if ln.startswith("event: error"))
    assert any(live.block_word in ln for ln in lines[:error_at])  # relayed before the error


def test_responses_block_word_in_a_plain_answer_is_refused(live: Live, client) -> None:
    from fi.gateway import APIStatusError

    with pytest.raises(APIStatusError) as ei:
        client.responses.create(model=MODEL, input=f"[[mock:block]] {live.marker()}")
    live.record("responses_nonstream_block", {"class": type(ei.value).__name__, "status": ei.value.status_code,
                                              "body": ei.value.body})
    assert ei.value.status_code == 403
