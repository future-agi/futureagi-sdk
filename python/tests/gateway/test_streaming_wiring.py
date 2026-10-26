"""Tests for streaming wiring -- create(stream=True) and .stream() method."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from fi.gateway.resources.chat.completions import ChatCompletions


def _make_mock_client_with_stream_response(chunks):
    """Create a mock AgentCC client that returns an SSE stream response."""
    sse_lines = []
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

    mock_base = MagicMock()
    mock_base._stream_request.return_value = resp

    mock_client = MagicMock()
    mock_client._get_base_client.return_value = mock_base

    return mock_client


CHUNK = {
    "id": "chatcmpl-abc",
    "object": "chat.completion.chunk",
    "created": 1709000000,
    "model": "gpt-4o",
    "choices": [{"index": 0, "delta": {"content": "Hello"}, "finish_reason": None}],
}

CHUNK_DONE = {
    "id": "chatcmpl-abc",
    "object": "chat.completion.chunk",
    "created": 1709000000,
    "model": "gpt-4o",
    "choices": [{"index": 0, "delta": {"content": "!"}, "finish_reason": "stop"}],
}


def test_create_stream_true_returns_stream():
    mock_client = _make_mock_client_with_stream_response([CHUNK, CHUNK_DONE])
    comp = ChatCompletions(mock_client)
    result = comp.create(model="gpt-4o", messages=[{"role": "user", "content": "Hi"}], stream=True)
    assert type(result).__qualname__ == "Stream"
    assert type(result).__module__ == "fi.gateway._streaming"
    chunks = list(result)
    assert len(chunks) == 2
    assert chunks[0].choices[0].delta.content == "Hello"


def test_create_stream_false_does_not_return_stream():
    """When stream is not True, create() goes through normal request path."""
    mock_base = MagicMock()
    mock_base._request_with_retry.return_value = MagicMock()
    mock_client = MagicMock()
    mock_client._get_base_client.return_value = mock_base

    comp = ChatCompletions(mock_client)
    comp.create(model="gpt-4o", messages=[{"role": "user", "content": "Hi"}])
    mock_base._request_with_retry.assert_called_once()


def test_stream_method_returns_stream_manager():
    mock_client = _make_mock_client_with_stream_response([CHUNK, CHUNK_DONE])
    comp = ChatCompletions(mock_client)
    mgr = comp.stream(model="gpt-4o", messages=[{"role": "user", "content": "Hi"}])
    assert type(mgr).__qualname__ == "StreamManager"
    assert type(mgr).__module__ == "fi.gateway._streaming"


def test_stream_method_context_manager():
    mock_client = _make_mock_client_with_stream_response([CHUNK, CHUNK_DONE])
    comp = ChatCompletions(mock_client)
    with comp.stream(model="gpt-4o", messages=[{"role": "user", "content": "Hi"}]) as mgr:
        texts = list(mgr.text_stream)
    assert texts == ["Hello", "!"]


def test_stream_method_get_final_text():
    mock_client = _make_mock_client_with_stream_response([CHUNK, CHUNK_DONE])
    comp = ChatCompletions(mock_client)
    with comp.stream(model="gpt-4o", messages=[{"role": "user", "content": "Hi"}]) as mgr:
        text = mgr.get_final_text()
    assert text == "Hello!"


def test_create_sends_stream_true_in_body():
    """Verify that stream=True is included in the request body."""
    mock_client = _make_mock_client_with_stream_response([CHUNK_DONE])
    comp = ChatCompletions(mock_client)
    comp.create(model="gpt-4o", messages=[{"role": "user", "content": "Hi"}], stream=True)
    # Check the body that was passed to _stream_request
    call_args = mock_client._get_base_client()._stream_request.call_args
    opts = call_args[0][0]  # First positional arg is RequestOptions
    assert opts.body["stream"] is True
