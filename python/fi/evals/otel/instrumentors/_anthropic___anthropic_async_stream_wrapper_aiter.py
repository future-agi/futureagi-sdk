"""_AnthropicAsyncStreamWrapper aiter operations."""
from __future__ import annotations


class __AnthropicAsyncStreamWrapperAiterMethods:
    __slots__ = ()

    def __aiter__(self):
        return self


    async def __anext__(self):
        try:
            event = await self._stream.__anext__()
            self._process_event(event)
            return event
        except StopAsyncIteration:
            self._finalize()
            raise


    async def __aenter__(self):
        return self


    async def __aexit__(self, *args):
        self._finalize()


    def _process_event(self, event):
        """Process a stream event."""
        event_type = getattr(event, "type", None)

        if event_type == "content_block_delta":
            delta = getattr(event, "delta", None)
            if delta and hasattr(delta, "text"):
                self._content_parts.append(delta.text)

        elif event_type == "message_delta":
            usage = getattr(event, "usage", None)
            if usage:
                if hasattr(usage, "output_tokens"):
                    self._usage["output_tokens"] = usage.output_tokens

        elif event_type == "message_start":
            message = getattr(event, "message", None)
            if message and hasattr(message, "usage"):
                self._usage["input_tokens"] = message.usage.input_tokens


    def _finalize(self):
        """Finalize the stream and update span."""
        from fi.evals.otel.instrumentors.anthropic import (
            GenAIAttributes, OTEL_AVAILABLE, Status, StatusCode,
        )
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
        if self._usage["input_tokens"] or self._usage["output_tokens"]:
            self._span.set_attribute(
                GenAIAttributes.USAGE_TOTAL_TOKENS,
                self._usage["input_tokens"] + self._usage["output_tokens"]
            )

        if OTEL_AVAILABLE:
            self._span.set_status(Status(StatusCode.OK))
