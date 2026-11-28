"""AnthropicInstrumentor format messages operations."""
from __future__ import annotations

from fi.evals.otel.instrumentors.anthropic import (Any)


class _AnthropicInstrumentorFormatMessagesMethods:
    __slots__ = ()

    def _format_messages(self, messages: list, system: str = "") -> str:
        """Format messages list as string."""
        parts = []

        # Add system prompt if present
        if system:
            parts.append(f"[system]: {system}")

        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                # Content can be string or list of content blocks
                if isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif isinstance(block, str):
                            text_parts.append(block)
                    content = "\n".join(text_parts)
                parts.append(f"[{role}]: {content}")
            else:
                parts.append(str(msg))

        return "\n".join(parts)


    def _wrap_stream_response(self, stream: Any, span: Any):
        """Wrap a streaming response to capture data."""
        from fi.evals.otel.instrumentors.anthropic import (Any, _AnthropicStreamWrapper)
        return _AnthropicStreamWrapper(stream, span, self._capture_completions)


    def _wrap_async_stream_response(self, stream: Any, span: Any):
        """Wrap an async streaming response."""
        from fi.evals.otel.instrumentors.anthropic import (Any, _AnthropicAsyncStreamWrapper)
        return _AnthropicAsyncStreamWrapper(stream, span, self._capture_completions)
