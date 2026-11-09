"""OpenAIInstrumentor instrument operations."""
from __future__ import annotations

from fi.evals.otel.instrumentors.openai import (Any, Callable, Dict)


class _OpenAIInstrumentorInstrumentMethods:
    __slots__ = ()

    def instrument(self, **kwargs) -> None:
        """Apply instrumentation to OpenAI client."""
        from fi.evals.otel.instrumentors.openai import (logger)
        if self._instrumented:
            return

        try:
            import openai
            from openai.resources.chat import completions as chat_completions
            from openai.resources import embeddings

            # Store original methods
            self._original_methods["chat_completions_create"] = (
                chat_completions.Completions.create
            )
            self._original_methods["async_chat_completions_create"] = (
                chat_completions.AsyncCompletions.create
            )
            self._original_methods["embeddings_create"] = (
                embeddings.Embeddings.create
            )
            self._original_methods["async_embeddings_create"] = (
                embeddings.AsyncEmbeddings.create
            )

            # Patch chat completions
            chat_completions.Completions.create = self._wrap_chat_create(
                self._original_methods["chat_completions_create"],
                is_async=False,
            )
            chat_completions.AsyncCompletions.create = self._wrap_chat_create(
                self._original_methods["async_chat_completions_create"],
                is_async=True,
            )

            # Patch embeddings
            embeddings.Embeddings.create = self._wrap_embeddings_create(
                self._original_methods["embeddings_create"],
                is_async=False,
            )
            embeddings.AsyncEmbeddings.create = self._wrap_embeddings_create(
                self._original_methods["async_embeddings_create"],
                is_async=True,
            )

            # Try to patch legacy completions if available
            try:
                from openai.resources import completions as legacy_completions
                self._original_methods["completions_create"] = (
                    legacy_completions.Completions.create
                )
                legacy_completions.Completions.create = self._wrap_completions_create(
                    self._original_methods["completions_create"],
                    is_async=False,
                )
            except (ImportError, AttributeError):
                pass  # Legacy completions not available

            self._instrumented = True
            logger.info("OpenAI instrumentation applied")

        except ImportError:
            logger.warning("OpenAI library not installed, skipping instrumentation")
        except Exception as e:
            logger.error(f"Failed to instrument OpenAI: {e}")


    def uninstrument(self, **kwargs) -> None:
        """Remove instrumentation from OpenAI client."""
        from fi.evals.otel.instrumentors.openai import (logger)
        if not self._instrumented:
            return

        try:
            from openai.resources.chat import completions as chat_completions
            from openai.resources import embeddings

            # Restore original methods
            if "chat_completions_create" in self._original_methods:
                chat_completions.Completions.create = (
                    self._original_methods["chat_completions_create"]
                )
            if "async_chat_completions_create" in self._original_methods:
                chat_completions.AsyncCompletions.create = (
                    self._original_methods["async_chat_completions_create"]
                )
            if "embeddings_create" in self._original_methods:
                embeddings.Embeddings.create = (
                    self._original_methods["embeddings_create"]
                )
            if "async_embeddings_create" in self._original_methods:
                embeddings.AsyncEmbeddings.create = (
                    self._original_methods["async_embeddings_create"]
                )

            try:
                from openai.resources import completions as legacy_completions
                if "completions_create" in self._original_methods:
                    legacy_completions.Completions.create = (
                        self._original_methods["completions_create"]
                    )
            except (ImportError, AttributeError):
                pass

            self._original_methods.clear()
            self._instrumented = False
            logger.info("OpenAI instrumentation removed")

        except Exception as e:
            logger.error(f"Failed to uninstrument OpenAI: {e}")


    def _wrap_chat_create(self, original: Callable, is_async: bool) -> Callable:
        """Wrap chat.completions.create."""
        from fi.evals.otel.instrumentors.openai import (Callable, functools)
        instrumentor = self

        if is_async:
            @functools.wraps(original)
            async def async_wrapper(self_arg, *args, **kwargs):
                return await instrumentor._trace_chat_completion(
                    original, self_arg, args, kwargs, is_async=True
                )
            return async_wrapper
        else:
            @functools.wraps(original)
            def wrapper(self_arg, *args, **kwargs):
                return instrumentor._trace_chat_completion(
                    original, self_arg, args, kwargs, is_async=False
                )
            return wrapper


    def _trace_chat_completion(
        self,
        original: Callable,
        self_arg: Any,
        args: tuple,
        kwargs: dict,
        is_async: bool,
    ):
        """Trace a chat completion call."""
        from fi.evals.otel.instrumentors.openai import (
            Any, Callable, GenAIAttributes, OPERATION_CHAT, SYSTEM_OPENAI,
        )
        tracer = self.get_tracer()

        # Extract parameters
        model = kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])
        stream = kwargs.get("stream", False)
        temperature = kwargs.get("temperature")
        max_tokens = kwargs.get("max_tokens")

        # Build attributes
        attributes = {
            GenAIAttributes.SYSTEM: SYSTEM_OPENAI,
            GenAIAttributes.OPERATION_NAME: OPERATION_CHAT,
            GenAIAttributes.REQUEST_MODEL: model,
        }

        if temperature is not None:
            attributes[GenAIAttributes.REQUEST_TEMPERATURE] = temperature
        if max_tokens is not None:
            attributes[GenAIAttributes.REQUEST_MAX_TOKENS] = max_tokens

        # Capture prompt
        if self._capture_prompts and messages:
            prompt_text = self._format_messages(messages)
            attributes[GenAIAttributes.prompt_content(0)] = prompt_text[:10000]

        span_name = f"openai.chat.completions.create"

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
        from fi.evals.otel.instrumentors.openai import (
            Any, Callable, Dict, OTEL_AVAILABLE, Status, StatusCode,
        )
        tracer = self.get_tracer()

        stream_owns_span = False
        with tracer.start_as_current_span(
            span_name, attributes=attributes, end_on_exit=False,
            record_exception=False, set_status_on_exception=False,
        ) as span:
            try:
                response = original(self_arg, *args, **kwargs)

                if stream and self._capture_streaming:
                    wrapped = self._wrap_stream_response(response, span)
                    stream_owns_span = True
                    return wrapped

                # Extract response data
                self._extract_response_data(response, span)

                if OTEL_AVAILABLE:
                    span.set_status(Status(StatusCode.OK))

                return response

            except BaseException as e:
                if OTEL_AVAILABLE:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                raise
            finally:
                if not stream_owns_span:
                    span.end()


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
        from fi.evals.otel.instrumentors.openai import (
            Any, Callable, Dict, OTEL_AVAILABLE, Status, StatusCode,
        )
        tracer = self.get_tracer()

        stream_owns_span = False
        with tracer.start_as_current_span(
            span_name, attributes=attributes, end_on_exit=False,
            record_exception=False, set_status_on_exception=False,
        ) as span:
            try:
                response = await original(self_arg, *args, **kwargs)

                if stream and self._capture_streaming:
                    wrapped = self._wrap_async_stream_response(response, span)
                    stream_owns_span = True
                    return wrapped

                self._extract_response_data(response, span)

                if OTEL_AVAILABLE:
                    span.set_status(Status(StatusCode.OK))

                return response

            except BaseException as e:
                if OTEL_AVAILABLE:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                raise
            finally:
                if not stream_owns_span:
                    span.end()
