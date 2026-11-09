"""Stream ownership covers early release, failures and cancellation offline."""

import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from fi.evals.otel.instrumentors.openai import OpenAIInstrumentor
from tests.evals.test_openai_stream_spans import _client, _create, recording


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("release", ["close", "context", "context-error"])
@pytest.mark.parametrize("consume", [False, True], ids=["empty", "partial"])
def test_early_release_finishes_once(recording, is_async, release, consume, monkeypatch):
    def observe(stream):
        end = Mock(wraps=stream._span.end)
        monkeypatch.setattr(stream._span, "end", end)
        assert recording.get_finished_spans() == ()
        return end

    def check(end):
        end.assert_called_once_with()
        spans = recording.get_finished_spans()
        assert len(spans) == 1
        span = spans[0]
        assert span.status.status_code is (
            StatusCode.ERROR if release == "context-error" else StatusCode.OK)
        assert span.attributes.get("gen_ai.completion.0.content") == (
            "local reply" if consume else None)
        assert len(span.events) == (1 if release == "context-error" else 0)

    async def exercise():
        async with _client(True, False) as client:
            stream = await _create(client)
            end = observe(stream)
            try:
                if release == "close":
                    if consume:
                        await stream.__anext__()
                    await stream.close()
                else:
                    async with stream:
                        if consume:
                            await stream.__anext__()
                        if release == "context-error":
                            raise RuntimeError("consumer interrupted")
            except RuntimeError as exc:
                assert release == "context-error" and str(exc) == "consumer interrupted"
            await stream.close()
            with pytest.raises(StopAsyncIteration):
                await stream.__anext__()
            check(end)

    if is_async:
        asyncio.run(exercise())
    else:
        with _client(False, False) as client:
            stream = _create(client)
            end = observe(stream)
            try:
                if release == "close":
                    if consume:
                        next(stream)
                    stream.close()
                else:
                    with stream:
                        if consume:
                            next(stream)
                        if release == "context-error":
                            raise RuntimeError("consumer interrupted")
            except RuntimeError as exc:
                assert release == "context-error" and str(exc) == "consumer interrupted"
            stream.close()
            with pytest.raises(StopIteration):
                next(stream)
            check(end)


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("operation", ["create", "iterate", "enter", "close", "exit"])
@pytest.mark.parametrize("error_type", [RuntimeError, asyncio.CancelledError])
def test_failures_finalize_and_propagate(is_async, operation, error_type):
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    instrumentor = OpenAIInstrumentor()
    instrumentor._tracer = provider.get_tracer("stream-finalization")
    error = error_type("interrupted")

    class Stream:
        def perform(self, name):
            if operation == name:
                raise error
            return self

        def __next__(self):
            return self.perform("iterate")

        def __enter__(self):
            return self.perform("enter")

        def __exit__(self, *args):
            self.perform("exit")

        def close(self):
            self.perform("close")

    class AsyncStream(Stream):
        async def __anext__(self):
            return self.perform("iterate")

        async def __aenter__(self):
            return self.perform("enter")

        async def __aexit__(self, *args):
            self.perform("exit")

        async def close(self):
            self.perform("close")

    def create(*args, **kwargs):
        if operation == "create":
            raise error
        return Stream()

    async def create_async(*args, **kwargs):
        create()
        return AsyncStream()

    async def exercise():
        stream = await instrumentor._trace_async(
            create_async, None, (), {}, "test-stream", {}, True)
        if operation == "iterate":
            await stream.__anext__()
        elif operation == "enter":
            await stream.__aenter__()
        elif operation == "close":
            await stream.close()
        else:
            await stream.__aexit__(None, None, None)

    try:
        with pytest.raises(error_type) as caught:
            if is_async:
                asyncio.run(exercise())
            else:
                stream = instrumentor._trace_sync(
                    create, None, (), {}, "test-stream", {}, True)
                if operation == "iterate":
                    next(stream)
                elif operation == "enter":
                    stream.__enter__()
                elif operation == "close":
                    stream.close()
                else:
                    stream.__exit__(None, None, None)
        assert caught.value is error
        spans = exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].status.status_code is StatusCode.ERROR
        assert len(spans[0].events) == 1
        assert spans[0].events[0].attributes["exception.message"] == "interrupted"
    finally:
        provider.shutdown()


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("capture_streaming,streaming", [(False, True), (True, False)])
def test_unwrapped_response_and_parent_context_are_preserved(is_async, capture_streaming, streaming):
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("stream-finalization")
    instrumentor = OpenAIInstrumentor(capture_streaming=capture_streaming)
    instrumentor._tracer = tracer
    response = SimpleNamespace(choices=[], usage=None)

    def create(*args, **kwargs):
        assert trace.get_current_span().is_recording()
        return response

    async def create_async(*args, **kwargs):
        return create()

    try:
        with tracer.start_as_current_span("parent") as parent:
            if is_async:
                result = asyncio.run(instrumentor._trace_async(
                    create_async, None, (), {}, "test-stream", {}, streaming))
            else:
                result = instrumentor._trace_sync(
                    create, None, (), {}, "test-stream", {}, streaming)
            assert result is response
            assert trace.get_current_span() is parent
            spans = exporter.get_finished_spans()
            assert len(spans) == 1
            assert spans[0].parent.span_id == parent.get_span_context().span_id
            assert spans[0].status.status_code is StatusCode.OK
    finally:
        provider.shutdown()
