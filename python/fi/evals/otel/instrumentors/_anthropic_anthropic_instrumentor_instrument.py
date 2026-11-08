"""AnthropicInstrumentor instrument operations."""
from __future__ import annotations

from fi.evals.otel.instrumentors.anthropic import (Any, Callable, Dict)


class _AnthropicInstrumentorInstrumentMethods:
    __slots__ = ()

    def instrument(self, **kwargs) -> None:
        """Apply instrumentation to Anthropic client."""
        from fi.evals.otel.instrumentors.anthropic import (logger)
        if self._instrumented:
            return

        try:
            import anthropic
            from anthropic.resources import messages

            # Store original methods
            self._original_methods["messages_create"] = messages.Messages.create
            self._original_methods["async_messages_create"] = (
                messages.AsyncMessages.create
            )

            # Patch messages.create
            messages.Messages.create = self._wrap_messages_create(
                self._original_methods["messages_create"],
                is_async=False,
            )
            messages.AsyncMessages.create = self._wrap_messages_create(
                self._original_methods["async_messages_create"],
                is_async=True,
            )

            self._instrumented = True
            logger.info("Anthropic instrumentation applied")

        except ImportError:
            logger.warning("Anthropic library not installed, skipping instrumentation")
        except Exception as e:
            logger.error(f"Failed to instrument Anthropic: {e}")


    def uninstrument(self, **kwargs) -> None:
        """Remove instrumentation from Anthropic client."""
        from fi.evals.otel.instrumentors.anthropic import (logger)
        if not self._instrumented:
            return

        try:
            from anthropic.resources import messages

            # Restore original methods
            if "messages_create" in self._original_methods:
                messages.Messages.create = self._original_methods["messages_create"]
            if "async_messages_create" in self._original_methods:
                messages.AsyncMessages.create = (
                    self._original_methods["async_messages_create"]
                )

            self._original_methods.clear()
            self._instrumented = False
            logger.info("Anthropic instrumentation removed")

        except Exception as e:
            logger.error(f"Failed to uninstrument Anthropic: {e}")


    def _wrap_messages_create(self, original: Callable, is_async: bool) -> Callable:
        """Wrap messages.create."""
        from fi.evals.otel.instrumentors.anthropic import (Callable, functools)
        instrumentor = self

        if is_async:
            @functools.wraps(original)
            async def async_wrapper(self_arg, *args, **kwargs):
                return await instrumentor._trace_messages_create(
                    original, self_arg, args, kwargs, is_async=True
                )
            return async_wrapper
        else:
            @functools.wraps(original)
            def wrapper(self_arg, *args, **kwargs):
                return instrumentor._trace_messages_create(
                    original, self_arg, args, kwargs, is_async=False
                )
            return wrapper


    def _trace_messages_create(
        self,
        original: Callable,
        self_arg: Any,
        args: tuple,
        kwargs: dict,
        is_async: bool,
    ):
        """Trace a messages.create call."""
        from fi.evals.otel.instrumentors.anthropic import (
            Any, Callable, GenAIAttributes, OPERATION_CHAT, SYSTEM_ANTHROPIC,
        )
        tracer = self.get_tracer()

        # Extract parameters
        model = kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])
        system = kwargs.get("system", "")
        stream = kwargs.get("stream", False)
        temperature = kwargs.get("temperature")
        max_tokens = kwargs.get("max_tokens")

        # Build attributes
        attributes = {
            GenAIAttributes.SYSTEM: SYSTEM_ANTHROPIC,
            GenAIAttributes.OPERATION_NAME: OPERATION_CHAT,
            GenAIAttributes.REQUEST_MODEL: model,
        }

        if temperature is not None:
            attributes[GenAIAttributes.REQUEST_TEMPERATURE] = temperature
        if max_tokens is not None:
            attributes[GenAIAttributes.REQUEST_MAX_TOKENS] = max_tokens

        # Capture prompt
        if self._capture_prompts:
            prompt_text = self._format_messages(messages, system)
            attributes[GenAIAttributes.prompt_content(0)] = prompt_text[:10000]

        span_name = "anthropic.messages.create"

        if is_async:
            return self._trace_async(
                original, self_arg, args, kwargs, span_name, attributes, stream
            )
        else:
            return self._trace_sync(
                original, self_arg, args, kwargs, span_name, attributes, stream
            )


    def _trace_sync(
        self,
        original: Callable,
        self_arg: Any,
        args: tuple,
        kwargs: dict,
        span_name: str,
        attributes: Dict[str, Any],
        stream: bool,
    ):
        """Trace a synchronous call."""
        from fi.evals.otel.instrumentors.anthropic import (
            Any, Callable, Dict, OTEL_AVAILABLE, Status, StatusCode,
        )
        tracer = self.get_tracer()

        with tracer.start_as_current_span(span_name, attributes=attributes) as span:
            try:
                response = original(self_arg, *args, **kwargs)

                if stream and self._capture_streaming:
                    # Wrap streaming response
                    return self._wrap_stream_response(response, span)

                # Extract response data
                self._extract_response_data(response, span)

                if OTEL_AVAILABLE:
                    span.set_status(Status(StatusCode.OK))

                return response

            except Exception as e:
                if OTEL_AVAILABLE:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                raise


    async def _trace_async(
        self,
        original: Callable,
        self_arg: Any,
        args: tuple,
        kwargs: dict,
        span_name: str,
        attributes: Dict[str, Any],
        stream: bool,
    ):
        """Trace an asynchronous call."""
        from fi.evals.otel.instrumentors.anthropic import (
            Any, Callable, Dict, OTEL_AVAILABLE, Status, StatusCode,
        )
        tracer = self.get_tracer()

        with tracer.start_as_current_span(span_name, attributes=attributes) as span:
            try:
                response = await original(self_arg, *args, **kwargs)

                if stream and self._capture_streaming:
                    return self._wrap_async_stream_response(response, span)

                self._extract_response_data(response, span)

                if OTEL_AVAILABLE:
                    span.set_status(Status(StatusCode.OK))

                return response

            except Exception as e:
                if OTEL_AVAILABLE:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                raise


    def _extract_response_data(self, response: Any, span: Any) -> None:
        """Extract data from a messages response."""
        from fi.evals.otel.instrumentors.anthropic import (Any, GenAIAttributes, logger)
        try:
            # Model used
            if hasattr(response, "model"):
                span.set_attribute(GenAIAttributes.RESPONSE_MODEL, response.model)

            # Response ID
            if hasattr(response, "id"):
                span.set_attribute(GenAIAttributes.RESPONSE_ID, response.id)

            # Token usage
            if hasattr(response, "usage") and response.usage:
                usage = response.usage
                if hasattr(usage, "input_tokens"):
                    span.set_attribute(
                        GenAIAttributes.USAGE_INPUT_TOKENS,
                        usage.input_tokens
                    )
                if hasattr(usage, "output_tokens"):
                    span.set_attribute(
                        GenAIAttributes.USAGE_OUTPUT_TOKENS,
                        usage.output_tokens
                    )
                    # Calculate total
                    input_tokens = getattr(usage, "input_tokens", 0)
                    output_tokens = getattr(usage, "output_tokens", 0)
                    span.set_attribute(
                        GenAIAttributes.USAGE_TOTAL_TOKENS,
                        input_tokens + output_tokens
                    )

            # Stop reason
            if hasattr(response, "stop_reason") and response.stop_reason:
                span.set_attribute(
                    GenAIAttributes.RESPONSE_FINISH_REASON,
                    response.stop_reason
                )

            # Content
            if self._capture_completions and hasattr(response, "content"):
                content = response.content
                if content and len(content) > 0:
                    # Anthropic returns list of content blocks
                    text_parts = []
                    for block in content:
                        if hasattr(block, "text"):
                            text_parts.append(block.text)
                        elif hasattr(block, "type") and block.type == "text":
                            text_parts.append(getattr(block, "text", ""))

                    if text_parts:
                        span.set_attribute(
                            GenAIAttributes.completion_content(0),
                            "\n".join(text_parts)[:10000]
                        )
                        span.set_attribute(
                            GenAIAttributes.completion_role(0),
                            "assistant"
                        )

        except Exception as e:
            logger.debug(f"Failed to extract response data: {e}")
