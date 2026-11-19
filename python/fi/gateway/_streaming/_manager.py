"""StreamEvent and the StreamManager context managers (``chat.completions.stream()``)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from typing import Any, Literal

from fi.gateway._streaming._accumulator import ChunkAccumulator
from fi.gateway._streaming._stream import AsyncStream, Stream
from fi.gateway.types.agentcc_metadata import AgentCCMetadata
from fi.gateway.types.chat.chat_completion import ChatCompletion
from fi.gateway.types.chat.chat_completion_chunk import ToolCallDelta
from fi.gateway.types.chat.chat_completion_message import ChatCompletionMessage
from fi.gateway.types.shared import Usage

StreamEventType = Literal["content", "tool_call", "usage", "done"]


@dataclass
class StreamEvent:
    """A typed event from the StreamManager iterator.

    ``content`` (``text``, ``index``), ``tool_call`` (``tool_call``, ``index``), ``usage``
    (``usage``) and ``done``. ``done`` comes only after ``[DONE]`` or the end of the body,
    so a gateway error frame sent after the finish chunk raises ``StreamError`` before
    ``done`` (a consumer that stops at ``done`` still sees the error). agentcc 1.x also
    declared guardrail and error variants and their fields, which nothing emitted: a
    guardrail block on a stream raises ``StreamError`` and a warning arrives in the
    ``.agentcc`` metadata (D-16).

    As in the released API, every chunk carrying usage emits a ``usage`` event,
    including a trailing ``choices: []`` chunk. Consumers must not sum cumulative
    usage events. ``get_final_completion().usage`` is the last reported usage.
    """

    type: str
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
                    yield StreamEvent(
                        type="content", text=choice.delta.content, index=choice.index
                    )
                if choice.delta.tool_calls:
                    for tc in choice.delta.tool_calls:
                        yield StreamEvent(
                            type="tool_call", tool_call=tc, index=choice.index
                        )
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
                    yield StreamEvent(
                        type="content", text=choice.delta.content, index=choice.index
                    )
                if choice.delta.tool_calls:
                    for tc in choice.delta.tool_calls:
                        yield StreamEvent(
                            type="tool_call", tool_call=tc, index=choice.index
                        )
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
