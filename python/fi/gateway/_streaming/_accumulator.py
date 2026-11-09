"""ChunkAccumulator: reassemble streamed chunks into one ChatCompletion."""

from __future__ import annotations

from dataclasses import dataclass, field

from fi.gateway.types.chat.chat_completion import ChatCompletion, Choice
from fi.gateway.types.chat.chat_completion_chunk import ChatCompletionChunk
from fi.gateway.types.chat.chat_completion_message import (
    ChatCompletionMessage,
    FunctionCall,
    ToolCall,
)
from fi.gateway.types.shared import Usage


@dataclass
class _AccumulatedToolCall:
    id: str | None = None
    type: str | None = None
    name_parts: list[str] = field(default_factory=list)
    args_parts: list[str] = field(default_factory=list)


@dataclass
class _AccumulatedChoice:
    content_parts: list[str] = field(default_factory=list)
    refusal_parts: list[str] = field(default_factory=list)
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

            if choice.delta.refusal is not None:
                acc.refusal_parts.append(choice.delta.refusal)

            if choice.delta.tool_calls:
                for tc_delta in choice.delta.tool_calls:
                    tc_acc = acc.tool_calls.setdefault(
                        tc_delta.index, _AccumulatedToolCall()
                    )
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
                    tool_calls_list.append(
                        ToolCall(
                            id=tc_acc.id or "",
                            type=tc_acc.type or "function",
                            function=FunctionCall(
                                name="".join(tc_acc.name_parts),
                                arguments="".join(tc_acc.args_parts),
                            ),
                        )
                    )

            message = ChatCompletionMessage(
                role=acc.role or "assistant",
                content=content,
                refusal="".join(acc.refusal_parts) if acc.refusal_parts else None,
                tool_calls=tool_calls_list,
            )
            choices.append(
                Choice(
                    index=idx,
                    message=message,
                    finish_reason=acc.finish_reason,
                )
            )

        return ChatCompletion(
            id=self._id or "",
            object="chat.completion",
            created=self._created or 0,
            model=self._model or "",
            choices=choices,
            usage=self._usage,
            system_fingerprint=self._system_fingerprint,
        )


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
