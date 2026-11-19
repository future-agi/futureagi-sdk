"""
Anthropic Instrumentor.

Automatic instrumentation for the Anthropic Python client library.
Supports both sync and async APIs.
"""

from typing import Any, Dict, Optional, Callable
import functools
import logging

from .base import BaseInstrumentor
from ..processors import OTEL_AVAILABLE
from ..conventions import (
    GenAIAttributes,
    SYSTEM_ANTHROPIC,
    OPERATION_CHAT,
    FINISH_STOP,
    FINISH_LENGTH,
)

if OTEL_AVAILABLE:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)


from ._anthropic_anthropic_instrumentor_instrument import _AnthropicInstrumentorInstrumentMethods
from ._anthropic_anthropic_instrumentor_format_messages import _AnthropicInstrumentorFormatMessagesMethods

class AnthropicInstrumentor(
    _AnthropicInstrumentorInstrumentMethods,
    _AnthropicInstrumentorFormatMessagesMethods,
    BaseInstrumentor,
):
    """
    Instrumentor for the Anthropic Python client.

    Automatically traces:
    - messages.create

    Example:
        from fi.evals.otel.instrumentors import AnthropicInstrumentor

        # Instrument Anthropic
        instrumentor = AnthropicInstrumentor()
        instrumentor.instrument()

        # All Anthropic calls are now traced
        from anthropic import Anthropic
        client = Anthropic()
        response = client.messages.create(
            model="claude-3-opus-20240229",
            messages=[{"role": "user", "content": "Hello!"}]
        )
        # Span automatically created with model, tokens, etc.

        # To disable
        instrumentor.uninstrument()
    """

    system_name = "anthropic"
    library_name = "anthropic"

    def __init__(
        self,
        capture_prompts: bool = True,
        capture_completions: bool = True,
        capture_streaming: bool = True,
    ):
        """
        Initialize the Anthropic instrumentor.

        Args:
            capture_prompts: Whether to capture input prompts
            capture_completions: Whether to capture outputs
            capture_streaming: Whether to trace streaming responses
        """
        super().__init__()
        self._capture_prompts = capture_prompts
        self._capture_completions = capture_completions
        self._capture_streaming = capture_streaming


from ._anthropic___anthropic_stream_wrapper_iter import __AnthropicStreamWrapperIterMethods

class _AnthropicStreamWrapper(__AnthropicStreamWrapperIterMethods):
    """Wrapper for sync streaming responses from Anthropic."""

    def __init__(self, stream, span, capture_content: bool):
        self._stream = stream
        self._span = span
        self._capture_content = capture_content
        self._content_parts = []
        self._usage = {"input_tokens": 0, "output_tokens": 0}


from ._anthropic___anthropic_async_stream_wrapper_aiter import __AnthropicAsyncStreamWrapperAiterMethods

class _AnthropicAsyncStreamWrapper(__AnthropicAsyncStreamWrapperAiterMethods):
    """Wrapper for async streaming responses from Anthropic."""

    def __init__(self, stream, span, capture_content: bool):
        self._stream = stream
        self._span = span
        self._capture_content = capture_content
        self._content_parts = []
        self._usage = {"input_tokens": 0, "output_tokens": 0}


__all__ = ["AnthropicInstrumentor"]
