"""Single-pass chat/text completion streams, with released lifecycle hooks."""

from __future__ import annotations

import json as _json
from collections.abc import AsyncIterator, Iterator
from typing import Any

from fi.gateway._exceptions import StreamError
from fi.gateway._streaming._sse import AsyncSSEParser, SSEEvent, SSEParser
from fi.gateway._streaming._tracking import StreamTracking
from fi.gateway.types.agentcc_metadata import AgentCCMetadata
from fi.gateway.types.chat.chat_completion_chunk import (
    ChatCompletionChunk, Delta, FunctionCallDelta, StreamChoice, ToolCallDelta,
)
from fi.gateway.types.completion import Completion
from fi.gateway.types.shared import Usage

_DONE = object()


def _str_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def stream_error_from_frame(error: Any, request_id: str | None = None) -> StreamError:
    """Retain structured error fields; never use a response to choose a destination."""
    if isinstance(error, str):
        return StreamError(f"Stream error: {error}", body=error, request_id=request_id)
    if isinstance(error, dict):
        message = f"Stream error: {error}"
        if error.get("code") == "wrong_region":
            message = "Gateway request reached the wrong region; check the explicitly configured origin."
        return StreamError(
            message, type=_str_or_none(error.get("type")), code=_str_or_none(error.get("code")),
            param=_str_or_none(error.get("param")), body=error, request_id=request_id,
        )
    return StreamError(f"Stream error: {error}", body=error, request_id=request_id)


def _chunk_from_event(event: SSEEvent, chunk_cls: Any, request_id: str | None) -> Any:
    if event.data is None:
        return None
    if event.data == "[DONE]":
        return _DONE
    try:
        data = _json.loads(event.data)
    except _json.JSONDecodeError as exc:
        raise StreamError(f"Invalid JSON in SSE event: {exc}") from exc
    if isinstance(data, dict) and "error" in data:
        return stream_error_from_frame(data["error"], request_id)
    return chunk_cls.model_validate(data)


def _request_id(response: Any) -> str | None:
    return response.headers.get("x-agentcc-request-id")


def _cache_hit_item(body: dict[str, Any], chunk_cls: Any) -> Any:
    return _cache_hit_chunk(body) if issubclass(chunk_cls, ChatCompletionChunk) else chunk_cls.model_validate(body)


def _cache_hit_chunk(body: dict[str, Any]) -> ChatCompletionChunk:
    choices: list[StreamChoice] = []
    for choice_data in body.get("choices", []):
        msg = choice_data.get("message", {})
        delta = Delta(
            role=msg.get("role"), content=msg.get("content"),
            refusal=msg.get("refusal"),
            tool_calls=[
                ToolCallDelta(
                    index=i, id=tc.get("id"), type=tc.get("type"),
                    function=FunctionCallDelta(
                        name=tc.get("function", {}).get("name"),
                        arguments=tc.get("function", {}).get("arguments"),
                    ) if tc.get("function") else None,
                ) for i, tc in enumerate(msg.get("tool_calls") or [])
            ] or None,
        )
        choices.append(StreamChoice(index=choice_data.get("index", 0), delta=delta, finish_reason=choice_data.get("finish_reason")))
    usage_data = body.get("usage")
    return ChatCompletionChunk(
        id=body.get("id", ""), object="chat.completion.chunk", created=body.get("created", 0),
        model=body.get("model", ""), choices=choices,
        usage=Usage.model_validate(usage_data) if usage_data else None,
        system_fingerprint=body.get("system_fingerprint"),
    )


class Stream(StreamTracking):
    """Single-pass iterator; exhaustion, failure and close release the response once.

    Closing discards buffered SSE/cache chunks. Existing iterators stay exhausted.
    """

    def __init__(
        self, response: Any, chunk_cls: Any = ChatCompletionChunk, *,
        on_chunk: Any = None, on_finish: Any = None,
    ) -> None:
        self._response = response
        self._chunk_cls = chunk_cls
        self._closed = False
        self._agentcc = AgentCCMetadata.from_headers(response.headers, http_response=response)
        self._init_tracking(chunk_cls, on_chunk, on_finish)
        self._is_cache_hit = "application/json" in response.headers.get("content-type", "")
        if self._is_cache_hit:
            iterator = self._cache_hit_iterator(_json.loads(response.read()))
        else:
            iterator = self._iterate_chunks(SSEParser(response.iter_bytes()))
        self._iterator = self._tracked(iterator)

    @property
    def agentcc(self) -> AgentCCMetadata:
        return self._agentcc

    @property
    def response(self) -> Any:
        return self._response

    def __iter__(self) -> Iterator[Any]:
        return self._iterator

    def __next__(self) -> Any:
        return next(self._iterator)

    def _iterate_chunks(self, parser: SSEParser) -> Iterator[Any]:
        if self._closed:
            return
        for event in parser:
            if self._closed:
                return
            chunk = _chunk_from_event(event, self._chunk_cls, _request_id(self._response))
            if chunk is _DONE:
                return
            if isinstance(chunk, StreamError):
                raise chunk
            if chunk is not None:
                yield chunk

    def _cache_hit_iterator(self, body: dict[str, Any]) -> Iterator[Any]:
        if not self._closed:
            yield _cache_hit_item(body, self._chunk_cls)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._response.close()
        except BaseException as exc:
            self._scrub_error(exc)
            raise
        finally:
            try:
                self._iterator.close()
            except ValueError as exc:
                if str(exc) != "generator already executing":
                    raise
            finally:
                self._notify_finish()

    def __enter__(self) -> Stream:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncStream(StreamTracking):
    """Async counterpart, preserving one parser across partial iteration and draining."""

    def __init__(
        self, response: Any, chunk_cls: Any = ChatCompletionChunk, *,
        on_chunk: Any = None, on_finish: Any = None,
    ) -> None:
        self._response = response
        self._chunk_cls = chunk_cls
        self._closed = False
        self._agentcc = AgentCCMetadata.from_headers(response.headers, http_response=response)
        self._init_tracking(chunk_cls, on_chunk, on_finish)
        self._is_cache_hit = "application/json" in response.headers.get("content-type", "")
        iterator = self._async_cache_hit_iterator() if self._is_cache_hit else self._async_iterate_chunks()
        self._iterator = self._atracked(iterator)

    @property
    def agentcc(self) -> AgentCCMetadata:
        return self._agentcc

    @property
    def response(self) -> Any:
        return self._response

    def __aiter__(self) -> AsyncIterator[Any]:
        return self._iterator

    async def __anext__(self) -> Any:
        return await self._iterator.__anext__()

    async def _async_iterate_chunks(self) -> AsyncIterator[Any]:
        if self._closed:
            return
        async for event in AsyncSSEParser(self._response.aiter_bytes()):
            if self._closed:
                return
            chunk = _chunk_from_event(event, self._chunk_cls, _request_id(self._response))
            if chunk is _DONE:
                return
            if isinstance(chunk, StreamError):
                raise chunk
            if chunk is not None:
                yield chunk

    async def _async_cache_hit_iterator(self) -> AsyncIterator[Any]:
        if self._closed:
            return
        body = await self._response.aread()
        if not self._closed:
            yield _cache_hit_item(_json.loads(body), self._chunk_cls)

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            await self._response.aclose()
        except BaseException as exc:
            self._scrub_error(exc)
            raise
        finally:
            try:
                await self._iterator.aclose()
            except RuntimeError as exc:
                if str(exc) != "aclose(): asynchronous generator is already running":
                    raise
            finally:
                self._notify_finish()

    async def __aenter__(self) -> AsyncStream:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()


class MockStream:
    """No-network chunk iterator for mock_response."""

    def __init__(self, chunk_iterator: Iterator[ChatCompletionChunk]) -> None:
        self._iterator = iter(chunk_iterator)
        self._agentcc = AgentCCMetadata(request_id="mock", trace_id="mock")

    @property
    def agentcc(self) -> AgentCCMetadata:
        return self._agentcc

    @property
    def response(self) -> Any:
        return None

    def __iter__(self) -> Iterator[ChatCompletionChunk]:
        return self._iterator

    def __next__(self) -> ChatCompletionChunk:
        return next(self._iterator)

    def close(self) -> None:
        close = getattr(self._iterator, "close", None)
        if close is not None:
            close()
        self._iterator = iter(())
