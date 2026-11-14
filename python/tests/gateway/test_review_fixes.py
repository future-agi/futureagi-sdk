"""Regression tests for the bugs found in code review of the vendored agentcc client."""

from __future__ import annotations

import asyncio
import io
import json
import logging

import httpx
import pytest
import respx

from fi.gateway import AgentCC, AgentCCError, AsyncAgentCC, Gateway
from fi.gateway._exceptions import (
    APIStatusError,
    BadGatewayError,
    NotFoundError,
    RateLimitError,
)
from fi.gateway._streaming import AsyncSSEParser, SSEParser
from fi.gateway.callbacks.base import CallbackRequest, CallbackResponse
from fi.gateway.callbacks.json_logger import JSONLoggingCallbackHandler
from fi.gateway.callbacks.logging import LoggingCallback
from fi.gateway.testing.recorder import RequestRecorder
from fi.gateway.types.agentcc_metadata import AgentCCMetadata

BASE = "http://gw.test"
COMPLETION = {
    "id": "chatcmpl-1",
    "object": "chat.completion",
    "created": 1,
    "model": "gpt-4o-mini",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
}
MSG = [{"role": "user", "content": "hi"}]


def _gw(**kw) -> AgentCC:
    kw.setdefault("max_retries", 0)
    return AgentCC(api_key="sk-agentcc-x", base_url=BASE, **kw)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("FI_GATEWAY_API_KEY", "FI_GATEWAY_URL", "AGENTCC_API_KEY", "AGENTCC_BASE_URL"):
        monkeypatch.delenv(name, raising=False)


# --- streaming ---------------------------------------------------------------


def _chunk_bytes(event: dict) -> list[bytes]:
    """One SSE event cut in the middle of its JSON and in the middle of a multibyte character."""
    raw = f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode()
    cut = raw.index("é".encode()) + 1  # inside the two-byte é
    return [raw[:cut], raw[cut:]]


def test_sse_line_split_across_chunks_is_reassembled() -> None:
    event = {"id": "1", "choices": [{"delta": {"content": "café"}}]}
    events = list(SSEParser(iter(_chunk_bytes(event) + [b"data: [DONE]\n\n"])))
    assert [e.data for e in events] == [json.dumps(event, ensure_ascii=False), "[DONE]"]


def test_async_sse_line_split_across_chunks_is_reassembled() -> None:
    event = {"id": "1", "choices": [{"delta": {"content": "café"}}]}

    async def gen():
        for chunk in _chunk_bytes(event) + [b"data: [DONE]\n\n"]:
            yield chunk

    async def run():
        return [e.data async for e in AsyncSSEParser(gen())]

    assert asyncio.run(run()) == [json.dumps(event, ensure_ascii=False), "[DONE]"]


def test_sse_crlf_and_trailing_line_without_newline() -> None:
    events = list(SSEParser(iter([b"data: a\r\n\r\ndata: b"])))
    assert [e.data for e in events] == ["a", "b"]


@respx.mock
def test_stream_cache_hit_on_a_real_streamed_response() -> None:
    respx.post(f"{BASE}/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=COMPLETION, headers={"content-type": "application/json", "x-agentcc-cache": "hit_exact"})
    )
    chunks = list(_gw().chat.completions.create(model="gpt-4o-mini", messages=MSG, stream=True))
    assert len(chunks) == 1 and chunks[0].choices[0].delta.content == "hi"


@respx.mock
def test_stream_error_response_is_closed() -> None:
    respx.post(f"{BASE}/v1/chat/completions").mock(return_value=httpx.Response(429, json={"error": {"message": "slow down"}}))
    with pytest.raises(RateLimitError) as exc:
        _gw().chat.completions.create(model="gpt-4o-mini", messages=MSG, stream=True)
    assert exc.value.response.is_closed


# --- errors ------------------------------------------------------------------


def test_string_error_envelope_still_maps_to_a_typed_error() -> None:
    response = httpx.Response(502, json={"error": "upstream unavailable"}, request=httpx.Request("POST", BASE))
    exc = APIStatusError.from_response(response)
    assert isinstance(exc, BadGatewayError) and "upstream unavailable" in exc.message


# --- callbacks ---------------------------------------------------------------


def test_json_logger_reads_cache_status(caplog: pytest.LogCaptureFixture) -> None:
    handler = JSONLoggingCallbackHandler()
    meta = AgentCCMetadata(request_id="r1", provider="openai", latency_ms=5, cache_status="hit_exact")
    with caplog.at_level(logging.INFO):
        request = CallbackRequest(method="POST", url="/v1/chat/completions", headers={}, body=None)
        handler.on_request_end(request, CallbackResponse(status_code=200, headers={}, agentcc=meta))
    assert any("hit_exact" in r.getMessage() for r in caplog.records)


@respx.mock
def test_callbacks_receive_a_callback_response(caplog: pytest.LogCaptureFixture, tmp_path) -> None:
    respx.post(f"{BASE}/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=COMPLETION, headers={"x-agentcc-provider": "openai", "x-agentcc-latency-ms": "7"})
    )
    recorder = RequestRecorder(str(tmp_path / "rec.json"))
    with caplog.at_level(logging.INFO):
        _gw(callbacks=[LoggingCallback(), recorder]).chat.completions.create(model="gpt-4o-mini", messages=MSG)
    assert any("status=200" in r.getMessage() and "provider=openai" in r.getMessage() for r in caplog.records)
    assert len(recorder.recordings) == 1


# --- resources going through the base client ---------------------------------


@respx.mock
def test_speech_sends_metadata_as_json() -> None:
    route = respx.post(f"{BASE}/v1/audio/speech").mock(return_value=httpx.Response(200, content=b"ID3"))
    _gw().audio.speech.create(model="tts-1", voice="alloy", input="hi", request_metadata={"tier": "pro"})
    assert json.loads(route.calls.last.request.headers["x-agentcc-metadata"]) == {"tier": "pro"}


@respx.mock
def test_files_create_is_multipart_and_retried() -> None:
    route = respx.post(f"{BASE}/v1/files").mock(
        side_effect=[
            httpx.Response(503, json={"error": {"message": "busy"}}),
            httpx.Response(200, json={"id": "file-1", "object": "file", "bytes": 3, "created_at": 1, "filename": "a.jsonl", "purpose": "batch"}),
        ]
    )
    result = _gw(max_retries=1).files.create(file=("a.jsonl", io.BytesIO(b"{}\n")), purpose="batch")
    assert result.id == "file-1" and route.call_count == 2
    request = route.calls.last.request
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="purpose"' in request.content and b'filename="a.jsonl"' in request.content


@respx.mock
def test_responses_delete_raises_typed_errors() -> None:
    respx.delete(f"{BASE}/v1/responses/resp-1").mock(return_value=httpx.Response(404, json={"error": {"message": "no such response"}}))
    with pytest.raises(NotFoundError):
        _gw().responses.delete("resp-1")


# --- with_options ------------------------------------------------------------


@respx.mock
def test_with_options_overrides_apply_after_the_parent_has_made_a_request() -> None:
    route = respx.post(f"{BASE}/v1/chat/completions").mock(return_value=httpx.Response(200, json=COMPLETION))
    parent = _gw(session_id="s-parent")
    parent.chat.completions.create(model="gpt-4o-mini", messages=MSG)
    child = parent.with_options(session_id="s-child", trace_id="t-1", timeout=5)
    child.chat.completions.create(model="gpt-4o-mini", messages=MSG)
    sent = route.calls.last.request.headers
    assert sent["x-agentcc-session-id"] == "s-child"
    assert sent["x-agentcc-trace-id"] == "t-1"
    assert child._get_base_client()._timeout.read == 5
    # Closing the child must not close the pool it shares with the parent.
    child.close()
    parent.chat.completions.create(model="gpt-4o-mini", messages=MSG)


# --- environment -------------------------------------------------------------


def test_fi_gateway_env_vars_work_for_every_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FI_GATEWAY_API_KEY", "sk-agentcc-env")
    monkeypatch.setenv("FI_GATEWAY_URL", "http://gw.env/v1")
    for cls in (AgentCC, AsyncAgentCC, Gateway):
        client = cls()
        assert client._api_key == "sk-agentcc-env"
        assert client._base_url == "http://gw.env"  # the OpenAI-style /v1 is dropped once, not sent twice


def test_missing_key_message_names_the_fi_variable() -> None:
    with pytest.raises(AgentCCError, match="FI_GATEWAY_API_KEY"):
        AgentCC(base_url=BASE)
