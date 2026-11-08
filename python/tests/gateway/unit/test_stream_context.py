"""Context-managed gateway streams release HTTP bodies, including on early exit.

A single transport read contains multiple SSE frames deliberately: closing only
HTTP would otherwise leave buffered chunks available from a retained iterator.
All requests use MockTransport; no server or provider is contacted.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from unittest.mock import patch

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, StreamError

GW = "http://127.0.0.1:8090"


class _Body(httpx.SyncByteStream, httpx.AsyncByteStream):
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.close_calls = 0

    def __iter__(self) -> Iterator[bytes]:
        yield self.data

    async def __aiter__(self) -> AsyncIterator[bytes]:
        yield self.data

    def close(self) -> None:
        self.close_calls += 1

    async def aclose(self) -> None:
        self.close_calls += 1


@pytest.fixture(params=["chat", "completion"])
def surface(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture(params=["sse", "json"])
def wire_format(request: pytest.FixtureRequest) -> str:
    return request.param


def _transport(surface: str, wire_format: str) -> tuple[httpx.MockTransport, _Body]:
    def answer(text: str) -> dict:
        if surface == "completion":
            choice = {"index": 0, "text": text, "finish_reason": "stop"}
            object_type = "text_completion"
        elif wire_format == "json":
            choice = {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
            object_type = "chat.completion"
        else:
            choice = {"index": 0, "delta": {"content": text}}
            object_type = "chat.completion.chunk"
        return {
            "id": "chunk-1",
            "object": object_type,
            "created": 1,
            "model": "m",
            "choices": [choice],
        }

    if wire_format == "json":
        data = json.dumps(answer("cached"))
        content_type = "application/json"
    else:
        data = "".join(f"data: {json.dumps(answer(t))}\n\n" for t in ("one", "two"))
        data += "data: [DONE]\n\n"
        content_type = "text/event-stream"
    body = _Body(data.encode())
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, headers={"content-type": content_type}, stream=body
        )
    )
    return transport, body


def _create(client: AgentCC | AsyncAgentCC, surface: str):
    if surface == "chat":
        return client.chat.completions.create(model="m", messages=[], stream=True)
    return client.completions.create(model="m", prompt="hello", stream=True)


@pytest.mark.parametrize("consume", ["none", "one", "all"])
def test_sync_context_closes_and_exhausts_stream(
    surface: str, wire_format: str, consume: str
) -> None:
    transport, body = _transport(surface, wire_format)
    with AgentCC(
        api_key="test-key", base_url=GW, http_client=httpx.Client(transport=transport)
    ) as client:
        stream = _create(client, surface)
        retained = iter(stream)
        with patch.object(stream.response, "close", wraps=stream.response.close) as close:
            with stream as entered:
                assert entered is stream
                if consume == "one":
                    next(retained)
                elif consume == "all":
                    assert len(list(retained)) == (1 if wire_format == "json" else 2)
            assert stream.response.is_closed
            assert body.close_calls == 1
            close.assert_called_once()
            stream.close()
            # Re-entering a closed stream does not reopen it or close it twice.
            with stream as entered:
                assert entered is stream
                assert list(entered) == []
            close.assert_called_once()
            assert list(retained) == []
            assert list(stream) == []
            with pytest.raises(StopIteration):
                next(stream)


@pytest.mark.parametrize("consume", ["none", "one", "all"])
async def test_async_context_closes_and_exhausts_stream(
    surface: str, wire_format: str, consume: str
) -> None:
    transport, body = _transport(surface, wire_format)
    async with AsyncAgentCC(
        api_key="test-key", base_url=GW, http_client=httpx.AsyncClient(transport=transport)
    ) as client:
        stream = await _create(client, surface)
        retained = aiter(stream)
        with patch.object(stream.response, "aclose", wraps=stream.response.aclose) as close:
            async with stream as entered:
                assert entered is stream
                if consume == "one":
                    await anext(retained)
                elif consume == "all":
                    assert len([c async for c in retained]) == (
                        1 if wire_format == "json" else 2
                    )
            assert stream.response.is_closed
            assert body.close_calls == 1
            # JSON reads close HTTP automatically; exiting must still be idempotent.
            calls_at_exit = close.await_count
            assert calls_at_exit >= 1
            await stream.aclose()
            async with stream as entered:
                assert entered is stream
                assert [c async for c in entered] == []
            assert close.await_count == calls_at_exit
            assert [c async for c in retained] == []
            assert [c async for c in stream] == []
            with pytest.raises(StopAsyncIteration):
                await anext(aiter(stream))


class _BodyError(BaseException):
    """A body failure must survive __exit__/__aexit__, even for BaseException."""


def test_sync_context_preserves_body_exception() -> None:
    transport, body = _transport("chat", "sse")
    error = _BodyError("body failed")
    with AgentCC(
        api_key="test-key", base_url=GW, http_client=httpx.Client(transport=transport)
    ) as client:
        stream = _create(client, "chat")
        with pytest.raises(_BodyError) as raised:
            with stream:
                next(stream)
                raise error
        assert raised.value is error
        assert stream.response.is_closed and body.close_calls == 1
        assert list(stream) == []


async def test_async_context_preserves_body_exception() -> None:
    transport, body = _transport("chat", "sse")
    error = _BodyError("body failed")
    async with AsyncAgentCC(
        api_key="test-key", base_url=GW, http_client=httpx.AsyncClient(transport=transport)
    ) as client:
        stream = await _create(client, "chat")
        retained = aiter(stream)
        with pytest.raises(_BodyError) as raised:
            async with stream:
                await anext(retained)
                raise error
        assert raised.value is error
        assert stream.response.is_closed and body.close_calls == 1
        assert [c async for c in retained] == []
        assert [c async for c in stream] == []


def test_sync_explicit_close_discards_buffered_chunks(surface: str, wire_format: str) -> None:
    transport, body = _transport(surface, wire_format)
    with AgentCC(
        api_key="test-key", base_url=GW, http_client=httpx.Client(transport=transport)
    ) as client:
        stream = _create(client, surface)
        retained = iter(stream)
        if wire_format == "sse":
            next(retained)
        with patch.object(stream.response, "close", wraps=stream.response.close) as close:
            stream.close()
            stream.close()
            close.assert_called_once()
        assert stream.response.is_closed and body.close_calls == 1
        assert list(retained) == []
        assert list(stream) == []


async def test_async_explicit_close_discards_buffered_chunks(
    surface: str, wire_format: str
) -> None:
    transport, body = _transport(surface, wire_format)
    async with AsyncAgentCC(
        api_key="test-key", base_url=GW, http_client=httpx.AsyncClient(transport=transport)
    ) as client:
        stream = await _create(client, surface)
        retained = aiter(stream)
        if wire_format == "sse":
            await anext(retained)
        with patch.object(stream.response, "aclose", wraps=stream.response.aclose) as close:
            await stream.aclose()
            await stream.aclose()
            close.assert_awaited_once()
        assert stream.response.is_closed and body.close_calls == 1
        assert [c async for c in retained] == []
        assert [c async for c in stream] == []


def test_sync_context_does_not_close_again_after_stream_error() -> None:
    transport, body = _transport("chat", "sse")
    body.data = b'data: {"error":{"message":"blocked"}}\n\n'
    with AgentCC(
        api_key="test-key", base_url=GW, http_client=httpx.Client(transport=transport)
    ) as client:
        stream = _create(client, "chat")
        with patch.object(stream.response, "close", wraps=stream.response.close) as close:
            with pytest.raises(StreamError, match="blocked"):
                with stream:
                    list(stream)
            stream.close()
            close.assert_called_once()
        assert stream.response.is_closed and body.close_calls == 1


async def test_async_context_does_not_close_again_after_stream_error() -> None:
    transport, body = _transport("chat", "sse")
    body.data = b'data: {"error":{"message":"blocked"}}\n\n'
    async with AsyncAgentCC(
        api_key="test-key", base_url=GW, http_client=httpx.AsyncClient(transport=transport)
    ) as client:
        stream = await _create(client, "chat")
        with patch.object(stream.response, "aclose", wraps=stream.response.aclose) as close:
            with pytest.raises(StreamError, match="blocked"):
                async with stream:
                    _ = [c async for c in stream]
            await stream.aclose()
            close.assert_awaited_once()
        assert stream.response.is_closed and body.close_calls == 1
