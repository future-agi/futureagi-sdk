"""Streaming engine — SSE parser, Stream/AsyncStream iterators, ChunkAccumulator, StreamManager."""

from __future__ import annotations

import codecs
import contextlib
import json as _json
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from typing import Any

from fi.gateway._exceptions import StreamError
from fi.gateway.types.agentcc_metadata import AgentCCMetadata
from fi.gateway.types.chat.chat_completion import ChatCompletion, Choice
from fi.gateway.types.chat.chat_completion_chunk import (
    ChatCompletionChunk,
    Delta,
    FunctionCallDelta,
    StreamChoice,
    ToolCallDelta,
)
from fi.gateway.types.chat.chat_completion_message import (
    ChatCompletionMessage,
    FunctionCall,
    ToolCall,
)
from fi.gateway.types.shared import Usage

# ---------------------------------------------------------------------------
# SSE Event
# ---------------------------------------------------------------------------


@dataclass
class SSEEvent:
    """One parsed Server-Sent Event."""

    data: str | None = None
    event: str | None = None
    id: str | None = None
    retry: int | None = None


# ---------------------------------------------------------------------------
# SSE Parsers
# ---------------------------------------------------------------------------


class SSEParser:
    """Parse a byte iterator into SSE events."""

    def __init__(self, byte_stream: Iterator[bytes]) -> None:
        self._byte_stream = byte_stream

    def __iter__(self) -> Iterator[SSEEvent]:
        buf_data: list[str] = []
        buf_event: str | None = None
        buf_id: str | None = None
        buf_retry: int | None = None

        # A chunk boundary can fall anywhere, even inside a multibyte character, so
        # decode incrementally and only hand out complete lines.
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        pending = ""
        for raw_chunk in self._byte_stream:
            pending += decoder.decode(raw_chunk)
            *lines, pending = pending.split("\n")
            for line in lines:
                line = line.rstrip("\r")
                if not line:
                    # Empty line = event boundary
                    if buf_data:
                        data = "\n".join(buf_data)
                        evt = SSEEvent(data=data, event=buf_event, id=buf_id, retry=buf_retry)
                        buf_data = []
                        buf_event = None
                        buf_id = None
                        buf_retry = None
                        yield evt
                        if data == "[DONE]":
                            return
                    continue

                if line.startswith(":"):
                    continue  # comment

                if line.startswith("data: "):
                    buf_data.append(line[6:])
                elif line.startswith("data:"):
                    buf_data.append(line[5:])
                elif line.startswith("event: "):
                    buf_event = line[7:]
                elif line.startswith("event:"):
                    buf_event = line[6:]
                elif line.startswith("id: "):
                    buf_id = line[4:]
                elif line.startswith("id:"):
                    buf_id = line[3:]
                elif line.startswith("retry: "):
                    with contextlib.suppress(ValueError):
                        buf_retry = int(line[7:])

        # Flush remaining: a last line without a newline, then the open event.
        pending += decoder.decode(b"", final=True)
        if pending.strip().startswith("data:"):
            buf_data.append(pending.strip()[5:].lstrip())
        if buf_data:
            yield SSEEvent(data="\n".join(buf_data), event=buf_event, id=buf_id, retry=buf_retry)


class AsyncSSEParser:
    """Parse an async byte iterator into SSE events."""

    def __init__(self, byte_stream: AsyncIterator[bytes]) -> None:
        self._byte_stream = byte_stream

    async def __aiter__(self) -> AsyncIterator[SSEEvent]:
        buf_data: list[str] = []
        buf_event: str | None = None
        buf_id: str | None = None
        buf_retry: int | None = None

        # A chunk boundary can fall anywhere, even inside a multibyte character, so
        # decode incrementally and only hand out complete lines.
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        pending = ""
        async for raw_chunk in self._byte_stream:
            pending += decoder.decode(raw_chunk)
            *lines, pending = pending.split("\n")
            for line in lines:
                line = line.rstrip("\r")
                if not line:
                    if buf_data:
                        data = "\n".join(buf_data)
                        evt = SSEEvent(data=data, event=buf_event, id=buf_id, retry=buf_retry)
                        buf_data = []
                        buf_event = None
                        buf_id = None
                        buf_retry = None
                        yield evt
                        if data == "[DONE]":
                            return
                    continue

                if line.startswith(":"):
                    continue

                if line.startswith("data: "):
                    buf_data.append(line[6:])
                elif line.startswith("data:"):
                    buf_data.append(line[5:])
                elif line.startswith("event: "):
                    buf_event = line[7:]
                elif line.startswith("event:"):
                    buf_event = line[6:]
                elif line.startswith("id: "):
                    buf_id = line[4:]
                elif line.startswith("id:"):
                    buf_id = line[3:]
                elif line.startswith("retry: "):
                    with contextlib.suppress(ValueError):
                        buf_retry = int(line[7:])

        pending += decoder.decode(b"", final=True)
        if pending.strip().startswith("data:"):
            buf_data.append(pending.strip()[5:].lstrip())
        if buf_data:
            yield SSEEvent(data="\n".join(buf_data), event=buf_event, id=buf_id, retry=buf_retry)


# ---------------------------------------------------------------------------
# Stream (sync)
# ---------------------------------------------------------------------------


class Stream:
    """Synchronous iterator over streaming chat completion chunks."""

    def __init__(self, response: Any, chunk_cls: type[ChatCompletionChunk] = ChatCompletionChunk) -> None:
        self._response = response
        self._chunk_cls = chunk_cls
        self._agentcc = AgentCCMetadata.from_headers(dict(response.headers), http_response=response)
        self._is_cache_hit = False

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            self._is_cache_hit = True
            body = _json.loads(response.read())
            self._iterator: Iterator[ChatCompletionChunk] = self._cache_hit_iterator(body)
        else:
            parser = SSEParser(response.iter_bytes())
            self._iterator = self._iterate_chunks(parser)

    @property
    def agentcc(self) -> AgentCCMetadata:
        return self._agentcc

    @property
    def response(self) -> Any:
        return self._response

    def __iter__(self) -> Iterator[ChatCompletionChunk]:
        return self._iterator

    def __next__(self) -> ChatCompletionChunk:
        return next(self._iterator)

    def _iterate_chunks(self, parser: SSEParser) -> Iterator[ChatCompletionChunk]:
        try:
            for event in parser:
                if event.data is None:
                    continue
                if event.data == "[DONE]":
                    return
                try:
                    data = _json.loads(event.data)
                except _json.JSONDecodeError as e:
                    raise StreamError(f"Invalid JSON in SSE event: {e}") from e

                if isinstance(data, dict) and "error" in data:

                    raise StreamError(f"Stream error: {data['error']}")

                yield self._chunk_cls.model_validate(data)
        except StreamError:
            raise
        except Exception as e:
            raise StreamError(f"Stream interrupted: {e}") from e

    def _cache_hit_iterator(self, body: dict[str, Any]) -> Iterator[ChatCompletionChunk]:
        """Convert a JSON cache-hit response into a single chunk."""
        choices: list[StreamChoice] = []
        for choice_data in body.get("choices", []):
            msg = choice_data.get("message", {})
            delta = Delta(
                role=msg.get("role"),
                content=msg.get("content"),
                tool_calls=[
                    ToolCallDelta(
                        index=i,
                        id=tc.get("id"),
                        type=tc.get("type"),
                        function=FunctionCallDelta(
                            name=tc.get("function", {}).get("name"),
                            arguments=tc.get("function", {}).get("arguments"),
                        ) if tc.get("function") else None,
                    )
                    for i, tc in enumerate(msg.get("tool_calls") or [])
                ] or None,
            )
            choices.append(StreamChoice(
                index=choice_data.get("index", 0),
                delta=delta,
                finish_reason=choice_data.get("finish_reason"),
            ))

        usage_data = body.get("usage")
        usage = Usage.model_validate(usage_data) if usage_data else None

        chunk = ChatCompletionChunk(
            id=body.get("id", ""),
            object="chat.completion.chunk",
            created=body.get("created", 0),
            model=body.get("model", ""),
            choices=choices,
            usage=usage,
            system_fingerprint=body.get("system_fingerprint"),
        )
        yield chunk

    def close(self) -> None:
        """Close the underlying HTTP response."""
        self._response.close()


# ---------------------------------------------------------------------------
# AsyncStream
# ---------------------------------------------------------------------------


class AsyncStream:
    """Asynchronous iterator over streaming chat completion chunks."""

    def __init__(self, response: Any, chunk_cls: type[ChatCompletionChunk] = ChatCompletionChunk) -> None:
        self._response = response
        self._chunk_cls = chunk_cls
        self._agentcc = AgentCCMetadata.from_headers(dict(response.headers), http_response=response)
        self._is_cache_hit = False

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            self._is_cache_hit = True
        self._started = False

    @property
    def agentcc(self) -> AgentCCMetadata:
        return self._agentcc

    @property
    def response(self) -> Any:
        return self._response

    def __aiter__(self) -> AsyncIterator[ChatCompletionChunk]:
        if self._is_cache_hit:
            return self._async_cache_hit_iterator()
        return self._async_iterate_chunks()

    async def _async_iterate_chunks(self) -> AsyncIterator[ChatCompletionChunk]:
        parser = AsyncSSEParser(self._response.aiter_bytes())
        try:
            async for event in parser:
                if event.data is None:
                    continue
                if event.data == "[DONE]":
                    return
                try:
                    data = _json.loads(event.data)
                except _json.JSONDecodeError as e:
                    raise StreamError(f"Invalid JSON in SSE event: {e}") from e

                if isinstance(data, dict) and "error" in data:
                    raise StreamError(f"Stream error: {data['error']}")

                yield self._chunk_cls.model_validate(data)
        except StreamError:
            raise
        except Exception as e:
            raise StreamError(f"Stream interrupted: {e}") from e

    async def _async_cache_hit_iterator(self) -> AsyncIterator[ChatCompletionChunk]:
        body = _json.loads(await self._response.aread())
        choices: list[StreamChoice] = []
        for choice_data in body.get("choices", []):
            msg = choice_data.get("message", {})
            delta = Delta(
                role=msg.get("role"),
                content=msg.get("content"),
                tool_calls=[
                    ToolCallDelta(
                        index=i,
                        id=tc.get("id"),
                        type=tc.get("type"),
                        function=FunctionCallDelta(
                            name=tc.get("function", {}).get("name"),
                            arguments=tc.get("function", {}).get("arguments"),
                        ) if tc.get("function") else None,
                    )
                    for i, tc in enumerate(msg.get("tool_calls") or [])
                ] or None,
            )
            choices.append(StreamChoice(
                index=choice_data.get("index", 0),
                delta=delta,
                finish_reason=choice_data.get("finish_reason"),
            ))

        usage_data = body.get("usage")
        usage = Usage.model_validate(usage_data) if usage_data else None

        yield ChatCompletionChunk(
            id=body.get("id", ""),
            object="chat.completion.chunk",
            created=body.get("created", 0),
            model=body.get("model", ""),
            choices=choices,
            usage=usage,
            system_fingerprint=body.get("system_fingerprint"),
        )

    async def aclose(self) -> None:
        await self._response.aclose()


# ---------------------------------------------------------------------------
# ChunkAccumulator
# ---------------------------------------------------------------------------


@dataclass
class _AccumulatedToolCall:
    id: str | None = None
    type: str | None = None
    name_parts: list[str] = field(default_factory=list)
    args_parts: list[str] = field(default_factory=list)


@dataclass
class _AccumulatedChoice:
    content_parts: list[str] = field(default_factory=list)
    tool_calls: dict[int, _AccumulatedToolCall] = field(default_factory=dict)
    finish_reason: str | None = None
    role: str | None = None


class ChunkAccumulator:
    """Reassembles streaming chunks into a complete ChatCompletion."""

    def __init__(self) -> None:
        self._id: str | None = None
        self._model: str | None = None
        self._created: int | None = None
        self._system_fingerprint: str | None = None
        self._choices: dict[int, _AccumulatedChoice] = {}
        self._usage: Usage | None = None

    def add(self, chunk: ChatCompletionChunk) -> None:
        """Incorporate a streaming chunk."""
        if self._id is None:
            self._id = chunk.id
        if self._model is None:
            self._model = chunk.model
        if self._created is None:
            self._created = chunk.created
        if self._system_fingerprint is None and chunk.system_fingerprint:
            self._system_fingerprint = chunk.system_fingerprint

        for choice in chunk.choices:
            acc = self._choices.setdefault(choice.index, _AccumulatedChoice())

            if choice.delta.role:
                acc.role = choice.delta.role

            if choice.delta.content is not None:
                acc.content_parts.append(choice.delta.content)

            if choice.delta.tool_calls:
                for tc_delta in choice.delta.tool_calls:
                    tc_acc = acc.tool_calls.setdefault(tc_delta.index, _AccumulatedToolCall())
                    if tc_delta.id:
                        tc_acc.id = tc_delta.id
                    if tc_delta.type:
                        tc_acc.type = tc_delta.type
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tc_acc.name_parts.append(tc_delta.function.name)
                        if tc_delta.function.arguments:
                            tc_acc.args_parts.append(tc_delta.function.arguments)

            if choice.finish_reason:
                acc.finish_reason = choice.finish_reason

        if chunk.usage:
            self._usage = chunk.usage

    def build(self) -> ChatCompletion:
        """Build a complete ChatCompletion from accumulated chunks."""
        choices: list[Choice] = []
        for idx in sorted(self._choices.keys()):
            acc = self._choices[idx]
            content = "".join(acc.content_parts) if acc.content_parts else None

            tool_calls_list: list[ToolCall] | None = None
            if acc.tool_calls:
                tool_calls_list = []
                for tc_idx in sorted(acc.tool_calls.keys()):
                    tc_acc = acc.tool_calls[tc_idx]
                    tool_calls_list.append(ToolCall(
                        id=tc_acc.id or "",
                        type=tc_acc.type or "function",
                        function=FunctionCall(
                            name="".join(tc_acc.name_parts),
                            arguments="".join(tc_acc.args_parts),
                        ),
                    ))

            message = ChatCompletionMessage(
                role=acc.role or "assistant",
                content=content,
                tool_calls=tool_calls_list,
            )
            choices.append(Choice(
                index=idx,
                message=message,
                finish_reason=acc.finish_reason,
            ))

        return ChatCompletion(
            id=self._id or "",
            object="chat.completion",
            created=self._created or 0,
            model=self._model or "",
            choices=choices,
            usage=self._usage,
            system_fingerprint=self._system_fingerprint,
        )


# ---------------------------------------------------------------------------
# StreamEvent (for Step 9 StreamManager)
# ---------------------------------------------------------------------------


@dataclass
class StreamEvent:
    """A typed event from the StreamManager iterator."""

    type: str  # "content", "tool_call", "guardrail_warning", "guardrail_block", "guardrail_disclaimer", "usage", "done", "error"
    text: str | None = None
    index: int = 0
    tool_call: ToolCallDelta | None = None
    guardrail_name: str | None = None
    message: str | None = None
    confidence: float | None = None
    disclaimer_text: str | None = None
    usage: Usage | None = None
    error: Any = None


# ---------------------------------------------------------------------------
# StreamManager (sync context manager)
# ---------------------------------------------------------------------------


class StreamManager:
    """Context manager for consuming a stream with convenience helpers."""

    def __init__(self, stream: Stream) -> None:
        self._stream = stream
        self._accumulator = ChunkAccumulator()
        self._entered = False
        self._done = False

    @property
    def agentcc(self) -> AgentCCMetadata:
        return self._stream.agentcc

    @property
    def response(self) -> Any:
        return self._stream.response

    @property
    def text_stream(self) -> Iterator[str]:
        """Iterate over text content only."""
        for chunk in self._stream:
            self._accumulator.add(chunk)
            for choice in chunk.choices:
                if choice.delta.content is not None:
                    yield choice.delta.content
        self._done = True

    @property
    def current_completion_snapshot(self) -> ChatCompletion:
        return self._accumulator.build()

    def __iter__(self) -> Iterator[StreamEvent]:
        for chunk in self._stream:
            self._accumulator.add(chunk)
            for choice in chunk.choices:
                if choice.delta.content is not None:
                    yield StreamEvent(type="content", text=choice.delta.content, index=choice.index)
                if choice.delta.tool_calls:
                    for tc in choice.delta.tool_calls:
                        yield StreamEvent(type="tool_call", tool_call=tc, index=choice.index)
            if chunk.usage:
                yield StreamEvent(type="usage", usage=chunk.usage)
        self._done = True
        yield StreamEvent(type="done")

    def get_final_completion(self) -> ChatCompletion:
        """Return the fully accumulated ChatCompletion."""
        if not self._done:
            # Drain remaining chunks
            for chunk in self._stream:
                self._accumulator.add(chunk)
            self._done = True
        result = self._accumulator.build()
        object.__setattr__(result, "agentcc", self._stream.agentcc)
        return result

    def get_final_message(self) -> ChatCompletionMessage:
        return self.get_final_completion().choices[0].message

    def get_final_text(self) -> str:
        return self.get_final_message().content or ""

    def __enter__(self) -> StreamManager:
        self._entered = True
        return self

    def __exit__(self, *args: Any) -> None:
        self._stream.close()

    def close(self) -> None:
        self._stream.close()


# ---------------------------------------------------------------------------
# AsyncStreamManager
# ---------------------------------------------------------------------------


class AsyncStreamManager:
    """Async context manager for consuming a stream."""

    def __init__(self, stream: AsyncStream) -> None:
        self._stream = stream
        self._accumulator = ChunkAccumulator()
        self._entered = False
        self._done = False

    @property
    def agentcc(self) -> AgentCCMetadata:
        return self._stream.agentcc

    @property
    def response(self) -> Any:
        return self._stream.response

    async def text_stream(self) -> AsyncIterator[str]:
        async for chunk in self._stream:
            self._accumulator.add(chunk)
            for choice in chunk.choices:
                if choice.delta.content is not None:
                    yield choice.delta.content
        self._done = True

    @property
    def current_completion_snapshot(self) -> ChatCompletion:
        return self._accumulator.build()

    async def __aiter__(self) -> AsyncIterator[StreamEvent]:
        async for chunk in self._stream:
            self._accumulator.add(chunk)
            for choice in chunk.choices:
                if choice.delta.content is not None:
                    yield StreamEvent(type="content", text=choice.delta.content, index=choice.index)
                if choice.delta.tool_calls:
                    for tc in choice.delta.tool_calls:
                        yield StreamEvent(type="tool_call", tool_call=tc, index=choice.index)
            if chunk.usage:
                yield StreamEvent(type="usage", usage=chunk.usage)
        self._done = True
        yield StreamEvent(type="done")

    async def get_final_completion(self) -> ChatCompletion:
        if not self._done:
            async for chunk in self._stream:
                self._accumulator.add(chunk)
            self._done = True
        result = self._accumulator.build()
        object.__setattr__(result, "agentcc", self._stream.agentcc)
        return result

    async def get_final_message(self) -> ChatCompletionMessage:
        comp = await self.get_final_completion()
        return comp.choices[0].message

    async def get_final_text(self) -> str:
        msg = await self.get_final_message()
        return msg.content or ""

    async def __aenter__(self) -> AsyncStreamManager:
        self._entered = True
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._stream.aclose()

    async def aclose(self) -> None:
        await self._stream.aclose()


# ---------------------------------------------------------------------------
# stream_chunk_builder (public convenience)
# ---------------------------------------------------------------------------


class MockStream:
    """A lightweight Stream-like object backed by a pre-built chunk iterator.

    Used by mock_response + stream=True to avoid needing a real HTTP response.
    """

    def __init__(self, chunk_iterator: Iterator[ChatCompletionChunk]) -> None:
        self._iterator = chunk_iterator
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
        pass


def stream_chunk_builder(chunks: list[ChatCompletionChunk]) -> ChatCompletion:
    """Reassemble a list of streaming chunks into a complete ChatCompletion.

    This is a convenience function for users who collect chunks manually
    and want to reconstruct the full response.

    Args:
        chunks: List of ChatCompletionChunk objects from a stream.

    Returns:
        A complete ChatCompletion with all content assembled.
    """
    acc = ChunkAccumulator()
    for chunk in chunks:
        acc.add(chunk)
    return acc.build()
