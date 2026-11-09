"""
OpenAI Instrumentor.

Automatic instrumentation for the OpenAI Python client library.
Supports both sync and async APIs.
"""

from typing import Any, Dict, Optional, Callable
import functools
import logging
import json

from .base import BaseInstrumentor
from ..processors import OTEL_AVAILABLE
from ..conventions import (
    GenAIAttributes,
    SYSTEM_OPENAI,
    OPERATION_CHAT,
    OPERATION_COMPLETION,
    OPERATION_EMBEDDING,
    FINISH_STOP,
    FINISH_LENGTH,
    FINISH_TOOL_CALLS,
)

if OTEL_AVAILABLE:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)


from ._openai_open_a_i_instrumentor_instrument import _OpenAIInstrumentorInstrumentMethods
from ._openai_open_a_i_instrumentor_extract_response_data import _OpenAIInstrumentorExtractResponseDataMethods

class OpenAIInstrumentor(
    _OpenAIInstrumentorInstrumentMethods,
    _OpenAIInstrumentorExtractResponseDataMethods,
    BaseInstrumentor,
):
    """
    Instrumentor for the OpenAI Python client.

    Automatically traces:
    - chat.completions.create
    - completions.create (legacy)
    - embeddings.create

    Example:
        from fi.evals.otel.instrumentors import OpenAIInstrumentor

        # Instrument OpenAI
        instrumentor = OpenAIInstrumentor()
        instrumentor.instrument()

        # All OpenAI calls are now traced
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        # Span automatically created with model, tokens, etc.

        # To disable
        instrumentor.uninstrument()
    """

    system_name = "openai"
    library_name = "openai"

    def __init__(
        self,
        capture_prompts: bool = True,
        capture_completions: bool = True,
        capture_streaming: bool = True,
    ):
        """
        Initialize the OpenAI instrumentor.

        Args:
            capture_prompts: Whether to capture input prompts
            capture_completions: Whether to capture outputs
            capture_streaming: Whether to trace streaming responses
        """
        super().__init__()
        self._capture_prompts = capture_prompts
        self._capture_completions = capture_completions
        self._capture_streaming = capture_streaming


class _StreamWrapper:
    """Wrapper for sync streaming responses."""

    def __init__(self, stream, span, capture_content: bool):
        self._stream = stream
        self._span = span
        self._capture_content = capture_content
        self._content_parts = []
        self._usage = {"input_tokens": 0, "output_tokens": 0}

    def __getattr__(self, name):
        return getattr(self._stream, name)

    def __enter__(self):
        self._stream.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self._stream.__exit__(exc_type, exc_value, traceback)

    def close(self):
        return self._stream.close()

    def __iter__(self):
        return self

    def __next__(self):
        try:
            chunk = next(self._stream)
            self._process_chunk(chunk)
            return chunk
        except StopIteration:
            self._finalize()
            raise

    def _process_chunk(self, chunk):
        """Process a stream chunk."""
        if hasattr(chunk, "choices") and chunk.choices:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                self._content_parts.append(delta.content)

        if hasattr(chunk, "usage") and chunk.usage:
            self._usage["input_tokens"] = chunk.usage.prompt_tokens
            self._usage["output_tokens"] = chunk.usage.completion_tokens

    def _finalize(self):
        """Finalize the stream and update span."""
        if self._capture_content and self._content_parts:
            content = "".join(self._content_parts)
            self._span.set_attribute(
                GenAIAttributes.completion_content(0),
                content[:10000]
            )

        if self._usage["input_tokens"]:
            self._span.set_attribute(
                GenAIAttributes.USAGE_INPUT_TOKENS,
                self._usage["input_tokens"]
            )
        if self._usage["output_tokens"]:
            self._span.set_attribute(
                GenAIAttributes.USAGE_OUTPUT_TOKENS,
                self._usage["output_tokens"]
            )

        if OTEL_AVAILABLE:
            self._span.set_status(Status(StatusCode.OK))


class _AsyncStreamWrapper:
    """Wrapper for async streaming responses."""

    def __init__(self, stream, span, capture_content: bool):
        self._stream = stream
        self._span = span
        self._capture_content = capture_content
        self._content_parts = []
        self._usage = {"input_tokens": 0, "output_tokens": 0}

    def __getattr__(self, name):
        return getattr(self._stream, name)

    async def __aenter__(self):
        await self._stream.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return await self._stream.__aexit__(exc_type, exc_value, traceback)

    async def close(self):
        return await self._stream.close()

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            chunk = await self._stream.__anext__()
            self._process_chunk(chunk)
            return chunk
        except StopAsyncIteration:
            self._finalize()
            raise

    def _process_chunk(self, chunk):
        """Process a stream chunk."""
        if hasattr(chunk, "choices") and chunk.choices:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                self._content_parts.append(delta.content)

        if hasattr(chunk, "usage") and chunk.usage:
            self._usage["input_tokens"] = chunk.usage.prompt_tokens
            self._usage["output_tokens"] = chunk.usage.completion_tokens

    def _finalize(self):
        """Finalize the stream and update span."""
        if self._capture_content and self._content_parts:
            content = "".join(self._content_parts)
            self._span.set_attribute(
                GenAIAttributes.completion_content(0),
                content[:10000]
            )

        if self._usage["input_tokens"]:
            self._span.set_attribute(
                GenAIAttributes.USAGE_INPUT_TOKENS,
                self._usage["input_tokens"]
            )
        if self._usage["output_tokens"]:
            self._span.set_attribute(
                GenAIAttributes.USAGE_OUTPUT_TOKENS,
                self._usage["output_tokens"]
            )

        if OTEL_AVAILABLE:
            self._span.set_status(Status(StatusCode.OK))


__all__ = ["OpenAIInstrumentor"]
