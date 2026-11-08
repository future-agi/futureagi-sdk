"""Tests for streaming wiring -- create(stream=True) and .stream() method."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
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
    # The split transport opens the public Stream and owns its lifecycle.
    from fi.gateway import Stream

    mock_base._open_stream.side_effect = lambda opts, params, chunk_cls: Stream(
        mock_base._stream_request(opts, params), chunk_cls
    )

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
    result = comp.create(
        model="gpt-4o", messages=[{"role": "user", "content": "Hi"}], stream=True
    )
    assert type(result).__qualname__ == "Stream"
    assert type(result).__module__.startswith("fi.gateway._streaming")
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
    assert type(mgr).__module__.startswith("fi.gateway._streaming")


def test_stream_method_context_manager():
    mock_client = _make_mock_client_with_stream_response([CHUNK, CHUNK_DONE])
    comp = ChatCompletions(mock_client)
    with comp.stream(
        model="gpt-4o", messages=[{"role": "user", "content": "Hi"}]
    ) as mgr:
        texts = list(mgr.text_stream)
    assert texts == ["Hello", "!"]


def test_stream_method_get_final_text():
    mock_client = _make_mock_client_with_stream_response([CHUNK, CHUNK_DONE])
    comp = ChatCompletions(mock_client)
    with comp.stream(
        model="gpt-4o", messages=[{"role": "user", "content": "Hi"}]
    ) as mgr:
        text = mgr.get_final_text()
    assert text == "Hello!"


def test_create_sends_stream_true_in_body():
    """Verify that stream=True is included in the request body."""
    mock_client = _make_mock_client_with_stream_response([CHUNK_DONE])
    comp = ChatCompletions(mock_client)
    comp.create(
        model="gpt-4o", messages=[{"role": "user", "content": "Hi"}], stream=True
    )
    # Check the body that was passed to _stream_request
    call_args = mock_client._get_base_client()._stream_request.call_args
    opts = call_args[0][0]  # First positional arg is RequestOptions
    assert opts.body["stream"] is True


def test_wire_snapshot_preserves_duplicate_headers_and_body(wire_snapshot):
    request = httpx.Request(
        "POST", "https://gateway.example.test/v1/chat/completions?q=1&q=2",
        headers=[
            ("Authorization", "Bearer synthetic-key"),
            ("x-agentcc-metadata", '{"tenant":"sample"}'),
            ("X-Extra", "first"), ("x-extra", "second"),
        ],
        content=b"binary\x00body\xff", extensions={"timeout": {"read": 7.0}},
    )
    original_headers = list(request.headers.raw)
    snapshot = wire_snapshot(request)
    assert snapshot is not request
    assert snapshot.headers is not request.headers
    assert snapshot.method == request.method
    assert snapshot.url == request.url
    assert snapshot.content == request.content == b"binary\x00body\xff"
    assert snapshot.headers.raw == request.headers.raw == original_headers
    assert snapshot.headers.get_list("x-extra") == ["first", "second"]
    assert snapshot.extensions["timeout"]["read"] == 7.0
    request.headers["authorization"] = "[REDACTED]"
    request.headers["x-agentcc-metadata"] = "[REDACTED]"
    assert snapshot.headers.raw == original_headers


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("stream", [False, True], ids=["json", "stream"])
async def test_wire_capture_does_not_prevent_retained_request_scrubbing(
    wire_snapshot, async_mode, stream
):
    seen, retained = [], []

    def handler(request):
        seen.append(wire_snapshot(request))
        retained.append(request)
        if stream:
            return httpx.Response(
                200, headers={"content-type": "text/event-stream"},
                content=f"data: {json.dumps(CHUNK_DONE)}\n\ndata: [DONE]\n\n",
            )
        return httpx.Response(200, json={
            "id": "reply", "object": "chat.completion", "created": 1, "model": "m",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "!"}}],
        })

    http = (httpx.AsyncClient if async_mode else httpx.Client)(
        transport=httpx.MockTransport(handler)
    )
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key="synthetic-key", base_url="https://gateway.example.test",
        http_client=http, max_retries=0, metadata={"tenant": "sample"},
        default_headers={"x-agentcc-trace-id": "synthetic-trace"},
    )
    try:
        result = client.chat.completions.create(model="m", messages=[], stream=stream)
        if async_mode:
            result = await result
        if stream:
            chunks = [chunk async for chunk in result] if async_mode else list(result)
            assert [chunk.choices[0].delta.content for chunk in chunks] == ["!"]
        else:
            assert result.choices[0].message.content == "!"
        assert len(seen) == len(retained) == 1
        snapshot, original = seen[0], retained[0]
        assert snapshot.method == "POST"
        assert str(snapshot.url) == "https://gateway.example.test/v1/chat/completions"
        assert json.loads(snapshot.content) == {"model": "m", "messages": [], "stream": stream}
        assert snapshot.headers["authorization"] == "Bearer synthetic-key"
        assert json.loads(snapshot.headers["x-agentcc-metadata"]) == {"tenant": "sample"}
        assert snapshot.headers["x-agentcc-trace-id"] == "synthetic-trace"
        for name in ("authorization", "x-agentcc-metadata", "x-agentcc-trace-id"):
            assert original.headers[name] == "[REDACTED]"
    finally:
        if async_mode:
            await client.aclose()
            await http.aclose()
        else:
            client.close()
            http.close()
