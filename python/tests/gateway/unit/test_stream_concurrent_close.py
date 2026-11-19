"""Closing while a reader is pending must not fail or mask the owner's exception.

MockTransport bodies signal exactly when a read is blocked, then either fail or
return buffered data when closed. No sleeps, network calls, or provider access.
"""

from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import AsyncIterator, Iterator
from contextlib import nullcontext
from unittest.mock import patch

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, StreamError

GW = "http://127.0.0.1:8090"


def _answer(text: str, *, cached: bool = False) -> bytes:
    choice = (
        {"message": {"role": "assistant", "content": text}}
        if cached
        else {"delta": {"content": text}}
    )
    body = json.dumps(
        {
            "id": "chunk-1",
            "object": "chat.completion" if cached else "chat.completion.chunk",
            "created": 1,
            "model": "m",
            "choices": [{"index": 0, **choice}],
        }
    )
    return body.encode() if cached else f"data: {body}\n\n".encode()


class _SyncBody(httpx.SyncByteStream):
    def __init__(self, read_error: bool) -> None:
        self.read_error = read_error
        self.reading = threading.Event()
        self.released = threading.Event()
        self.close_calls = 0

    def __iter__(self) -> Iterator[bytes]:
        yield _answer("first")
        self.reading.set()
        if not self.released.wait(timeout=5):
            raise AssertionError("owner did not release the pending read")
        if self.read_error:
            raise httpx.ReadError("connection closed by owner")
        yield _answer("unread") + _answer("also unread")

    def close(self) -> None:
        self.close_calls += 1
        self.released.set()


class _AsyncBody(httpx.AsyncByteStream):
    def __init__(self, delivery: str) -> None:
        self.delivery = delivery
        self.reading = asyncio.Event()
        self.released = asyncio.Event()
        self.close_calls = 0

    async def __aiter__(self) -> AsyncIterator[bytes]:
        if self.delivery != "json_buffered":
            yield _answer("first")
        self.reading.set()
        await asyncio.wait_for(self.released.wait(), timeout=5)
        if self.delivery == "sse_error":
            raise httpx.ReadError("connection closed by owner")
        if self.delivery == "json_buffered":
            yield _answer("unread", cached=True)
        else:
            yield _answer("unread") + _answer("also unread")

    async def aclose(self) -> None:
        self.close_calls += 1
        self.released.set()


class _BodyError(BaseException):
    """Context cleanup must preserve even a BaseException from the owner."""


@pytest.mark.parametrize("close_mode", ["explicit", "context", "body_error"])
@pytest.mark.parametrize("read_error", [True, False], ids=["read_error", "buffered"])
def test_sync_close_while_reader_is_pending(close_mode: str, read_error: bool) -> None:
    body = _SyncBody(read_error)
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, headers={"content-type": "text/event-stream"}, stream=body
        )
    )
    with AgentCC(
        api_key="test-key", base_url=GW, http_client=httpx.Client(transport=transport)
    ) as client:
        stream = client.chat.completions.create(model="m", messages=[], stream=True)
        retained = iter(stream)
        chunks = []
        errors = []
        body_error = _BodyError("owner body failed")

        def read() -> None:
            try:
                chunks.extend(retained)
            except Exception as error:
                errors.append(error)

        reader = threading.Thread(target=read, daemon=True)
        expected = (
            pytest.raises(_BodyError) if close_mode == "body_error" else nullcontext()
        )
        with patch.object(stream.response, "close", wraps=stream.response.close) as close:
            try:
                with expected as raised:
                    with stream if close_mode != "explicit" else nullcontext(stream):
                        reader.start()
                        assert body.reading.wait(timeout=5), (
                            "reader never reached the blocked read"
                        )
                        if close_mode == "explicit":
                            stream.close()
                        elif close_mode == "body_error":
                            raise body_error
                if close_mode == "body_error":
                    assert raised.value is body_error
            finally:
                # Always release and join the worker, including on the red revision.
                body.released.set()
                reader.join(timeout=5)
            assert not reader.is_alive()
            assert stream.response.is_closed
            assert body.close_calls == 1
            close.assert_called_once()
            stream.close()
            close.assert_called_once()
            assert [chunk.choices[0].delta.content for chunk in chunks] == ["first"]
            if read_error:
                assert len(errors) == 1 and isinstance(errors[0], StreamError)
                assert isinstance(errors[0].__cause__, httpx.ReadError)
            else:
                assert errors == []
            assert list(retained) == []
            assert list(stream) == []
            with pytest.raises(StopIteration):
                next(stream)


@pytest.mark.parametrize("close_mode", ["explicit", "context", "body_error"])
@pytest.mark.parametrize("delivery", ["sse_error", "sse_buffered", "json_buffered"])
async def test_async_close_while_reader_is_pending(close_mode: str, delivery: str) -> None:
    body = _AsyncBody(delivery)
    content_type = (
        "application/json" if delivery == "json_buffered" else "text/event-stream"
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, headers={"content-type": content_type}, stream=body
        )
    )
    async with AsyncAgentCC(
        api_key="test-key", base_url=GW, http_client=httpx.AsyncClient(transport=transport)
    ) as client:
        stream = await client.chat.completions.create(model="m", messages=[], stream=True)
        retained = aiter(stream)
        chunks = []
        errors = []
        body_error = _BodyError("owner body failed")

        async def read() -> None:
            try:
                async for chunk in retained:
                    chunks.append(chunk)
            except Exception as error:
                errors.append(error)

        reader = None
        expected = (
            pytest.raises(_BodyError) if close_mode == "body_error" else nullcontext()
        )
        with patch.object(stream.response, "aclose", wraps=stream.response.aclose) as close:
            try:
                with expected as raised:
                    async with (
                        stream if close_mode != "explicit" else nullcontext(stream)
                    ):
                        reader = asyncio.create_task(read())
                        await asyncio.wait_for(body.reading.wait(), timeout=5)
                        if close_mode == "explicit":
                            await stream.aclose()
                        elif close_mode == "body_error":
                            raise body_error
                if close_mode == "body_error":
                    assert raised.value is body_error
            finally:
                body.released.set()
                if reader is not None:
                    await asyncio.wait_for(reader, timeout=5)
            assert stream.response.is_closed
            assert body.close_calls == 1
            if delivery == "json_buffered":
                # httpx also calls aclose when the pending aread reaches EOF.
                assert close.await_count >= 1
            else:
                close.assert_awaited_once()
            calls_after_reader = close.await_count
            await stream.aclose()
            assert close.await_count == calls_after_reader
            expected_chunks = [] if delivery == "json_buffered" else ["first"]
            assert [chunk.choices[0].delta.content for chunk in chunks] == expected_chunks
            if delivery == "sse_error":
                assert len(errors) == 1 and isinstance(errors[0], StreamError)
                assert isinstance(errors[0].__cause__, httpx.ReadError)
            else:
                assert errors == []
            assert [chunk async for chunk in retained] == []
            assert [chunk async for chunk in stream] == []
            with pytest.raises(StopAsyncIteration):
                await anext(retained)
