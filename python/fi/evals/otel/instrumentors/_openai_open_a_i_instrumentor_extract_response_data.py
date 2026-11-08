"""OpenAIInstrumentor extract response data operations."""
from __future__ import annotations

from fi.evals.otel.instrumentors.openai import (Any, Callable)


class _OpenAIInstrumentorExtractResponseDataMethods:
    __slots__ = ()

    def _extract_response_data(self, response: Any, span: Any) -> None:
        """Extract data from a chat completion response."""
        from fi.evals.otel.instrumentors.openai import (Any, GenAIAttributes, logger)
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
                if hasattr(usage, "prompt_tokens"):
                    span.set_attribute(
                        GenAIAttributes.USAGE_INPUT_TOKENS,
                        usage.prompt_tokens
                    )
                if hasattr(usage, "completion_tokens"):
                    span.set_attribute(
                        GenAIAttributes.USAGE_OUTPUT_TOKENS,
                        usage.completion_tokens
                    )
                if hasattr(usage, "total_tokens"):
                    span.set_attribute(
                        GenAIAttributes.USAGE_TOTAL_TOKENS,
                        usage.total_tokens
                    )

            # Completion content
            if self._capture_completions and hasattr(response, "choices"):
                choices = response.choices
                if choices and len(choices) > 0:
                    choice = choices[0]

                    # Finish reason
                    if hasattr(choice, "finish_reason") and choice.finish_reason:
                        span.set_attribute(
                            GenAIAttributes.RESPONSE_FINISH_REASON,
                            choice.finish_reason
                        )

                    # Content
                    if hasattr(choice, "message") and choice.message:
                        msg = choice.message
                        if hasattr(msg, "content") and msg.content:
                            span.set_attribute(
                                GenAIAttributes.completion_content(0),
                                msg.content[:10000]
                            )
                        if hasattr(msg, "role"):
                            span.set_attribute(
                                GenAIAttributes.completion_role(0),
                                msg.role
                            )

        except Exception as e:
            logger.debug(f"Failed to extract response data: {e}")


    def _format_messages(self, messages: list) -> str:
        """Format messages list as string."""
        parts = []
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                parts.append(f"[{role}]: {content}")
            else:
                parts.append(str(msg))
        return "\n".join(parts)


    def _wrap_stream_response(self, stream: Any, span: Any):
        """Wrap a streaming response to capture data."""
        from fi.evals.otel.instrumentors.openai import (Any, _StreamWrapper)
        # Return wrapped iterator that accumulates content
        return _StreamWrapper(stream, span, self._capture_completions)


    def _wrap_async_stream_response(self, stream: Any, span: Any):
        """Wrap an async streaming response."""
        from fi.evals.otel.instrumentors.openai import (Any, _AsyncStreamWrapper)
        return _AsyncStreamWrapper(stream, span, self._capture_completions)


    def _wrap_embeddings_create(self, original: Callable, is_async: bool) -> Callable:
        """Wrap embeddings.create."""
        from fi.evals.otel.instrumentors.openai import (
            Callable, GenAIAttributes, OPERATION_EMBEDDING, OTEL_AVAILABLE, SYSTEM_OPENAI, Status,
            StatusCode, functools,
        )
        instrumentor = self

        if is_async:
            @functools.wraps(original)
            async def async_wrapper(self_arg, *args, **kwargs):
                tracer = instrumentor.get_tracer()
                model = kwargs.get("model", "text-embedding-ada-002")

                attributes = {
                    GenAIAttributes.SYSTEM: SYSTEM_OPENAI,
                    GenAIAttributes.OPERATION_NAME: OPERATION_EMBEDDING,
                    GenAIAttributes.REQUEST_MODEL: model,
                }

                # Capture input text
                input_text = kwargs.get("input", "")
                if instrumentor._capture_prompts and input_text:
                    if isinstance(input_text, list):
                        input_text = " ".join(str(t) for t in input_text[:5])
                    attributes[GenAIAttributes.prompt_content(0)] = str(input_text)[:10000]

                with tracer.start_as_current_span(
                    "openai.embeddings.create",
                    attributes=attributes
                ) as span:
                    try:
                        response = await original(self_arg, *args, **kwargs)

                        # Extract usage
                        if hasattr(response, "usage") and response.usage:
                            span.set_attribute(
                                GenAIAttributes.USAGE_INPUT_TOKENS,
                                response.usage.prompt_tokens
                            )
                            span.set_attribute(
                                GenAIAttributes.USAGE_TOTAL_TOKENS,
                                response.usage.total_tokens
                            )

                        if OTEL_AVAILABLE:
                            span.set_status(Status(StatusCode.OK))

                        return response
                    except Exception as e:
                        if OTEL_AVAILABLE:
                            span.set_status(Status(StatusCode.ERROR, str(e)))
                            span.record_exception(e)
                        raise

            return async_wrapper
        else:
            @functools.wraps(original)
            def wrapper(self_arg, *args, **kwargs):
                tracer = instrumentor.get_tracer()
                model = kwargs.get("model", "text-embedding-ada-002")

                attributes = {
                    GenAIAttributes.SYSTEM: SYSTEM_OPENAI,
                    GenAIAttributes.OPERATION_NAME: OPERATION_EMBEDDING,
                    GenAIAttributes.REQUEST_MODEL: model,
                }

                input_text = kwargs.get("input", "")
                if instrumentor._capture_prompts and input_text:
                    if isinstance(input_text, list):
                        input_text = " ".join(str(t) for t in input_text[:5])
                    attributes[GenAIAttributes.prompt_content(0)] = str(input_text)[:10000]

                with tracer.start_as_current_span(
                    "openai.embeddings.create",
                    attributes=attributes
                ) as span:
                    try:
                        response = original(self_arg, *args, **kwargs)

                        if hasattr(response, "usage") and response.usage:
                            span.set_attribute(
                                GenAIAttributes.USAGE_INPUT_TOKENS,
                                response.usage.prompt_tokens
                            )
                            span.set_attribute(
                                GenAIAttributes.USAGE_TOTAL_TOKENS,
                                response.usage.total_tokens
                            )

                        if OTEL_AVAILABLE:
                            span.set_status(Status(StatusCode.OK))

                        return response
                    except Exception as e:
                        if OTEL_AVAILABLE:
                            span.set_status(Status(StatusCode.ERROR, str(e)))
                            span.record_exception(e)
                        raise

            return wrapper


    def _wrap_completions_create(self, original: Callable, is_async: bool) -> Callable:
        """Wrap legacy completions.create."""
        from fi.evals.otel.instrumentors.openai import (
            Callable, GenAIAttributes, OPERATION_COMPLETION, OTEL_AVAILABLE, SYSTEM_OPENAI, Status,
            StatusCode, functools,
        )
        instrumentor = self

        @functools.wraps(original)
        def wrapper(self_arg, *args, **kwargs):
            tracer = instrumentor.get_tracer()
            model = kwargs.get("model", "unknown")

            attributes = {
                GenAIAttributes.SYSTEM: SYSTEM_OPENAI,
                GenAIAttributes.OPERATION_NAME: OPERATION_COMPLETION,
                GenAIAttributes.REQUEST_MODEL: model,
            }

            prompt = kwargs.get("prompt", "")
            if instrumentor._capture_prompts and prompt:
                attributes[GenAIAttributes.prompt_content(0)] = str(prompt)[:10000]

            with tracer.start_as_current_span(
                "openai.completions.create",
                attributes=attributes
            ) as span:
                try:
                    response = original(self_arg, *args, **kwargs)

                    if hasattr(response, "usage") and response.usage:
                        span.set_attribute(
                            GenAIAttributes.USAGE_INPUT_TOKENS,
                            response.usage.prompt_tokens
                        )
                        span.set_attribute(
                            GenAIAttributes.USAGE_OUTPUT_TOKENS,
                            response.usage.completion_tokens
                        )
                        span.set_attribute(
                            GenAIAttributes.USAGE_TOTAL_TOKENS,
                            response.usage.total_tokens
                        )

                    if instrumentor._capture_completions and hasattr(response, "choices"):
                        if response.choices:
                            text = response.choices[0].text
                            span.set_attribute(
                                GenAIAttributes.completion_content(0),
                                text[:10000]
                            )

                    if OTEL_AVAILABLE:
                        span.set_status(Status(StatusCode.OK))

                    return response
                except Exception as e:
                    if OTEL_AVAILABLE:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                    raise

        return wrapper
