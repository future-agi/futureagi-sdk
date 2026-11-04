"""Tests for StreamManager — context manager, text_stream, get_final_completion."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from fi.gateway._streaming import Stream, StreamManager


def _make_sse_response(chunks: list[dict[str, object]]) -> MagicMock:
    sse_lines: list[str] = []
    for chunk in chunks:
        sse_lines.append(f"data: {json.dumps(chunk)}")
        sse_lines.append("")
    sse_lines.append("data: [DONE]")
    sse_lines.append("")

    raw_bytes = ("\n".join(sse_lines) + "\n").encode("utf-8")

    resp = MagicMock()
    resp.headers = {
        "content-type": "text/event-stream",
        "x-agentcc-request-id": "req-1",
        "x-agentcc-trace-id": "trace-1",
        "x-agentcc-provider": "openai",
        "x-agentcc-latency-ms": "50",
    }
    resp.iter_bytes.return_value = iter([raw_bytes])
    resp.close = MagicMock()
    return resp


CHUNK_TEMPLATE = {
    "id": "chatcmpl-abc",
    "object": "chat.completion.chunk",
    "created": 1709000000,
    "model": "gpt-4o",
}


def _make_chunk(content: str | None = None, finish_reason: str | None = None, role: str | None = None) -> dict[str, object]:
    delta: dict[str, object] = {}
    if role:
        delta["role"] = role
    if content is not None:
        delta["content"] = content
    return {
        **CHUNK_TEMPLATE,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    }


def test_context_manager() -> None:
    resp = _make_sse_response([_make_chunk(role="assistant"), _make_chunk("Hi", "stop")])
    stream = Stream(resp)
    with StreamManager(stream) as mgr:
        texts = list(mgr.text_stream)
    assert texts == ["Hi"]
    resp.close.assert_called_once()


def test_text_stream_yields_only_text() -> None:
    resp = _make_sse_response([
        _make_chunk(role="assistant"),
        _make_chunk("Hello"),
        _make_chunk(" world"),
        _make_chunk("!", "stop"),
    ])
    stream = Stream(resp)
    with StreamManager(stream) as mgr:
        texts = list(mgr.text_stream)
    assert texts == ["Hello", " world", "!"]


def test_get_final_completion() -> None:
    resp = _make_sse_response([
        _make_chunk(role="assistant"),
        _make_chunk("Hello"),
        _make_chunk(" world", "stop"),
    ])
    stream = Stream(resp)
    with StreamManager(stream) as mgr:
        # Drain text_stream first
        list(mgr.text_stream)
        comp = mgr.get_final_completion()
    assert comp.choices[0].message.content == "Hello world"
    assert comp.choices[0].finish_reason == "stop"
    assert comp.agentcc is not None
    assert comp.agentcc.request_id == "req-1"


def test_get_final_text() -> None:
    resp = _make_sse_response([
        _make_chunk(role="assistant"),
        _make_chunk("Hi"),
        _make_chunk("!", "stop"),
    ])
    stream = Stream(resp)
    with StreamManager(stream) as mgr:
        list(mgr.text_stream)
        text = mgr.get_final_text()
    assert text == "Hi!"


def test_get_final_completion_without_draining() -> None:
    """get_final_completion() should auto-drain if not already done."""
    resp = _make_sse_response([
        _make_chunk(role="assistant"),
        _make_chunk("Auto"),
        _make_chunk("-drain", "stop"),
    ])
    stream = Stream(resp)
    with StreamManager(stream) as mgr:
        comp = mgr.get_final_completion()
    assert comp.choices[0].message.content == "Auto-drain"


def test_agentcc_available_immediately() -> None:
    resp = _make_sse_response([_make_chunk("Hi", "stop")])
    stream = Stream(resp)
    with StreamManager(stream) as mgr:
        assert mgr.agentcc.provider == "openai"
        assert mgr.agentcc.request_id == "req-1"


def test_stream_events() -> None:
    resp = _make_sse_response([
        _make_chunk(role="assistant"),
        _make_chunk("Hello"),
        _make_chunk(" world", "stop"),
    ])
    stream = Stream(resp)
    with StreamManager(stream) as mgr:
        events = list(mgr)
    content_events = [e for e in events if e.type == "content"]
    assert len(content_events) == 2
    assert content_events[0].text == "Hello"
    assert content_events[1].text == " world"
    assert events[-1].type == "done"
