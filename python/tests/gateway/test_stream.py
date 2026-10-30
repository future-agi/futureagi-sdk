"""Tests for Stream — iterating over SSE chunks from the gateway."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from fi.gateway._streaming import Stream
from fi.gateway.types.chat.chat_completion_chunk import ChatCompletionChunk


def _make_sse_response(
    chunks: list[dict[str, object]],
    headers: dict[str, str] | None = None,
    content_type: str = "text/event-stream",
) -> MagicMock:
    """Build a mock httpx.Response that yields SSE byte chunks."""
    hdrs = {
        "content-type": content_type,
        "x-agentcc-request-id": "req-1",
        "x-agentcc-trace-id": "trace-1",
        "x-agentcc-provider": "openai",
        "x-agentcc-latency-ms": "100",
    }
    if headers:
        hdrs.update(headers)

    sse_lines: list[str] = []
    for chunk in chunks:
        sse_lines.append(f"data: {json.dumps(chunk)}")
        sse_lines.append("")
    sse_lines.append("data: [DONE]")
    sse_lines.append("")

    raw_bytes = ("\n".join(sse_lines) + "\n").encode("utf-8")

    resp = MagicMock()
    resp.headers = hdrs
    resp.iter_bytes.return_value = iter([raw_bytes])
    resp.json.return_value = None
    resp.close = MagicMock()
    return resp


CHUNK_TEMPLATE = {
    "id": "chatcmpl-abc",
    "object": "chat.completion.chunk",
    "created": 1709000000,
    "model": "gpt-4o",
}


def _make_chunk(content: str, finish_reason: str | None = None) -> dict[str, object]:
    return {
        **CHUNK_TEMPLATE,
        "choices": [{
            "index": 0,
            "delta": {"content": content},
            "finish_reason": finish_reason,
        }],
    }


def test_stream_yields_chunks() -> None:
    resp = _make_sse_response([
        _make_chunk("Hello"),
        _make_chunk(" world"),
        _make_chunk("!", "stop"),
    ])
    stream = Stream(resp)
    chunks = list(stream)
    assert len(chunks) == 3
    assert all(isinstance(c, ChatCompletionChunk) for c in chunks)
    assert chunks[0].choices[0].delta.content == "Hello"
    assert chunks[1].choices[0].delta.content == " world"
    assert chunks[2].choices[0].delta.content == "!"


def test_stream_agentcc_metadata() -> None:
    resp = _make_sse_response([_make_chunk("Hi", "stop")])
    stream = Stream(resp)
    assert stream.agentcc.request_id == "req-1"
    assert stream.agentcc.provider == "openai"
    assert stream.agentcc.latency_ms == 100


def test_stream_close() -> None:
    resp = _make_sse_response([_make_chunk("Hi", "stop")])
    stream = Stream(resp)
    list(stream)  # consume
    stream.close()
    resp.close.assert_called_once()


def test_stream_error_event() -> None:
    error_chunk = {"error": {"message": "Stream broke", "type": "server_error"}}
    sse_lines = [f"data: {json.dumps(error_chunk)}", "", "data: [DONE]", ""]
    raw = ("\n".join(sse_lines) + "\n").encode("utf-8")

    resp = MagicMock()
    resp.headers = {"content-type": "text/event-stream", "x-agentcc-request-id": "req-1"}
    resp.iter_bytes.return_value = iter([raw])
    resp.close = MagicMock()

    stream = Stream(resp)
    with pytest.raises(Exception, match="Stream error"):
        list(stream)


# --- Cache hit tests ---


def test_stream_cache_hit_json() -> None:
    """When Content-Type is application/json, Stream treats it as a cache hit."""
    body = {
        "id": "chatcmpl-cached",
        "object": "chat.completion",
        "created": 1709000000,
        "model": "gpt-4o",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": "Cached response"},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
    }

    resp = MagicMock()
    resp.headers = {
        "content-type": "application/json",
        "x-agentcc-request-id": "req-cached",
        "x-agentcc-cache": "hit_exact",
    }
    resp.read.return_value = json.dumps(body).encode()  # a streamed response is read first
    resp.close = MagicMock()

    stream = Stream(resp)
    chunks = list(stream)
    assert len(chunks) == 1
    assert chunks[0].id == "chatcmpl-cached"
    assert chunks[0].choices[0].delta.content == "Cached response"
    assert chunks[0].choices[0].finish_reason == "stop"
    assert chunks[0].usage is not None
    assert chunks[0].usage.total_tokens == 8
    assert stream.agentcc.cache_status == "hit_exact"
