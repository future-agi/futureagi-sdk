"""Stream error parity with the TypeScript SDK.

Both SDKs read the same gateway frames, tests/fixtures/gateway/stream-error-frames.json
(verbatim from agent-command-center-sdk sdk/fixtures/ at the recorded source), and assert
the same thing: a stream that ends with the gateway's error event raises
StreamError carrying the error's code and message, and a stream without one
iterates to the end. Requests go to an httpx.MockTransport; nothing leaves
the process.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, StreamError

FIXTURE_PATH = (
    Path(__file__).resolve().parents[4]
    / "tests"
    / "fixtures"
    / "gateway"
    / "stream-error-frames.json"
)
CASES: list[dict[str, Any]] = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))[
    "cases"
]
ERROR_CASES = [c for c in CASES if c["expect"]["raises"]]
OK_CASES = [c for c in CASES if not c["expect"]["raises"]]

BASE_URL = "http://127.0.0.1:8090"
MESSAGES = [{"role": "user", "content": "Say hello"}]


def _sse_body(frames: list[str]) -> bytes:
    return "".join(f"data: {frame}\n\n" for frame in frames).encode("utf-8")


def _handler(frames: list[str]) -> Any:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "127.0.0.1"
        return httpx.Response(
            200,
            headers={
                "content-type": "text/event-stream",
                "x-agentcc-request-id": "req-sdk101",
            },
            content=_sse_body(frames),
        )

    return handle


def _client(frames: list[str]) -> AgentCC:
    return AgentCC(
        api_key="sk-test",
        base_url=BASE_URL,
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(_handler(frames))),
    )


def _async_client(frames: list[str]) -> AsyncAgentCC:
    return AsyncAgentCC(
        api_key="sk-test",
        base_url=BASE_URL,
        max_retries=0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(_handler(frames))),
    )


def _text(chunks: list[Any]) -> str:
    return "".join(
        (c.choices[0].delta.content or "") if c.choices else "" for c in chunks
    )


def _assert_gateway_error(exc: StreamError, expect: dict[str, Any]) -> None:
    # D-02: the fields, as TypeScript carries them (agentcc 1.0 Python carried the
    # error object's repr in the message, "Stream error: {...}").
    assert exc.code == expect["code"]
    assert exc.type == expect["type"]
    assert exc.message == str(exc) == f"Stream error: {exc.body}"
    assert exc.body["message"] == expect["message"]
    assert exc.param is None
    assert isinstance(exc.body, dict) and exc.body["code"] == expect["code"]


@pytest.mark.parametrize("case", ERROR_CASES, ids=[c["name"] for c in ERROR_CASES])
def test_stream_raises_stream_error(case: dict[str, Any]) -> None:
    expect = case["expect"]
    client = _client(case["frames"])
    chunks: list[Any] = []
    stream = client.chat.completions.create(
        model="gpt-4o-mini", messages=MESSAGES, stream=True
    )
    with pytest.raises(StreamError) as info:
        for chunk in stream:
            chunks.append(chunk)
    _assert_gateway_error(info.value, expect)
    assert len(chunks) == expect["chunks_before_error"]
    assert _text(chunks) == expect["text_before_error"]
    stream.close()
    client.close()


@pytest.mark.parametrize("case", ERROR_CASES, ids=[c["name"] for c in ERROR_CASES])
def test_stream_manager_text_stream_raises_stream_error(case: dict[str, Any]) -> None:
    expect = case["expect"]
    client = _client(case["frames"])
    texts: list[str] = []
    with client.chat.completions.stream(
        model="gpt-4o-mini", messages=MESSAGES
    ) as manager:
        with pytest.raises(StreamError) as info:
            for text in manager.text_stream:
                texts.append(text)
    _assert_gateway_error(info.value, expect)
    assert "".join(texts) == expect["text_before_error"]
    client.close()


@pytest.mark.parametrize("case", ERROR_CASES, ids=[c["name"] for c in ERROR_CASES])
async def test_async_stream_raises_stream_error(case: dict[str, Any]) -> None:
    expect = case["expect"]
    client = _async_client(case["frames"])
    chunks: list[Any] = []
    stream = await client.chat.completions.create(
        model="gpt-4o-mini", messages=MESSAGES, stream=True
    )
    with pytest.raises(StreamError) as info:
        async for chunk in stream:
            chunks.append(chunk)
    _assert_gateway_error(info.value, expect)
    assert len(chunks) == expect["chunks_before_error"]
    assert _text(chunks) == expect["text_before_error"]
    await stream.aclose()
    await client.aclose()


@pytest.mark.parametrize("case", OK_CASES, ids=[c["name"] for c in OK_CASES])
def test_stream_without_error_iterates(case: dict[str, Any]) -> None:
    expect = case["expect"]
    client = _client(case["frames"])
    stream = client.chat.completions.create(
        model="gpt-4o-mini", messages=MESSAGES, stream=True
    )
    chunks = list(stream)
    assert len(chunks) == expect["chunks"]
    assert _text(chunks) == expect["text"]
    if expect["total_tokens"] is not None:
        assert chunks[-1].choices == []
        assert chunks[-1].usage is not None
        assert chunks[-1].usage.total_tokens == expect["total_tokens"]
    stream.close()
    client.close()


@pytest.mark.parametrize("case", OK_CASES, ids=[c["name"] for c in OK_CASES])
async def test_async_stream_without_error_iterates(case: dict[str, Any]) -> None:
    expect = case["expect"]
    client = _async_client(case["frames"])
    stream = await client.chat.completions.create(
        model="gpt-4o-mini", messages=MESSAGES, stream=True
    )
    chunks = [chunk async for chunk in stream]
    assert len(chunks) == expect["chunks"]
    assert _text(chunks) == expect["text"]
    await stream.aclose()
    await client.aclose()
