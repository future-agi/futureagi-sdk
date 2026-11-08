"""Tests for utility features -- token counting, cost estimation, model info, stream_chunk_builder."""

from __future__ import annotations


def test_stream_chunk_builder():
    from fi.gateway._streaming import stream_chunk_builder
    from fi.gateway.types.chat.chat_completion_chunk import (
        ChatCompletionChunk,
        Delta,
        StreamChoice,
    )

    chunks = [
        ChatCompletionChunk(
            id="c1",
            object="chat.completion.chunk",
            created=1,
            model="gpt-4o",
            choices=[StreamChoice(index=0, delta=Delta(role="assistant"))],
        ),
        ChatCompletionChunk(
            id="c1",
            object="chat.completion.chunk",
            created=1,
            model="gpt-4o",
            choices=[StreamChoice(index=0, delta=Delta(content="Hello"))],
        ),
        ChatCompletionChunk(
            id="c1",
            object="chat.completion.chunk",
            created=1,
            model="gpt-4o",
            choices=[
                StreamChoice(
                    index=0, delta=Delta(content=" world"), finish_reason="stop"
                )
            ],
        ),
    ]
    result = stream_chunk_builder(chunks)
    assert result.choices[0].message.content == "Hello world"
    assert result.choices[0].finish_reason == "stop"
