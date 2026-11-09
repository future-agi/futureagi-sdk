"""Stream telemetry must describe consumption, not only response creation."""

import asyncio
import json
import time

import httpx
import openai
import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from fi.evals.otel.instrumentors.openai import OpenAIInstrumentor


class _Body(httpx.SyncByteStream, httpx.AsyncByteStream):
    def __init__(self, fail):
        self.fail = fail

    def __iter__(self):
        chunk = {"id": "chat-test", "object": "chat.completion.chunk", "created": 0,
                 "model": "test-model", "choices": [{"index": 0, "delta": {
                     "content": "local reply"}, "finish_reason": None}]}
        yield ("data: " + json.dumps(chunk) + "\n\n").encode()
        if self.fail:
            raise RuntimeError("stream interrupted")
        chunk.update(choices=[], usage={"prompt_tokens": 2, "completion_tokens": 1,
                                        "total_tokens": 3})
        yield ("data: " + json.dumps(chunk) + "\n\ndata: [DONE]\n\n").encode()

    async def __aiter__(self):
        for chunk in self:
            yield chunk


@pytest.fixture
def recording():
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    instrumentor = OpenAIInstrumentor()
    instrumentor._tracer = provider.get_tracer("stream-test")
    instrumentor.instrument()
    assert instrumentor.is_instrumented
    try:
        yield exporter
    finally:
        instrumentor.uninstrument()
        provider.shutdown()


def _client(is_async, fail):
    transport = httpx.MockTransport(lambda request: httpx.Response(
        200, headers={"content-type": "text/event-stream"}, stream=_Body(fail)))
    client_type = openai.AsyncOpenAI if is_async else openai.OpenAI
    http_type = httpx.AsyncClient if is_async else httpx.Client
    return client_type(api_key="test-only", base_url="https://provider.invalid/v1",
                       max_retries=0, http_client=http_type(
                           transport=transport, trust_env=False))


def _create(client):
    return client.chat.completions.create(
        model="test-model", messages=[{"role": "user", "content": "hello"}],
        stream=True, stream_options={"include_usage": True})


def _assert_finished(exporter, started_consuming, fail):
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.attributes["gen_ai.completion.0.content"] == "local reply"
    assert span.end_time >= started_consuming
    assert span.status.status_code is (StatusCode.ERROR if fail else StatusCode.OK)
    if fail:
        assert any(event.name == "exception" and
                   event.attributes["exception.message"] == "stream interrupted"
                   for event in span.events)
    else:
        assert span.attributes["gen_ai.usage.input_tokens"] == 2
        assert span.attributes["gen_ai.usage.output_tokens"] == 1


@pytest.mark.parametrize("fail", [False, True], ids=["exhausted", "interrupted"])
def test_sync_span_captures_stream_content_usage_and_failures(recording, fail):
    with _client(False, fail) as client:
        stream = _create(client)
        try:
            started_consuming = time.time_ns()
            if fail:
                assert next(stream).choices[0].delta.content == "local reply"
                with pytest.raises(RuntimeError, match="stream interrupted"):
                    next(stream)
            else:
                assert len(list(stream)) == 2
            _assert_finished(recording, started_consuming, fail)
        finally:
            stream._stream.close()


@pytest.mark.parametrize("fail", [False, True], ids=["exhausted", "interrupted"])
def test_async_span_captures_stream_content_usage_and_failures(recording, fail):
    async def exercise():
        async with _client(True, fail) as client:
            stream = await _create(client)
            try:
                started_consuming = time.time_ns()
                if fail:
                    assert (await stream.__anext__()).choices[0].delta.content == "local reply"
                    with pytest.raises(RuntimeError, match="stream interrupted"):
                        await stream.__anext__()
                else:
                    assert len([chunk async for chunk in stream]) == 2
                _assert_finished(recording, started_consuming, fail)
            finally:
                await stream._stream.close()

    asyncio.run(exercise())


def test_sync_span_remains_open_after_stream_creation(recording):
    with _client(False, False) as client:
        stream = _create(client)
        try:
            assert recording.get_finished_spans() == ()
        finally:
            stream._stream.close()


def test_async_span_remains_open_after_stream_creation(recording):
    async def exercise():
        async with _client(True, False) as client:
            stream = await _create(client)
            try:
                assert recording.get_finished_spans() == ()
            finally:
                await stream._stream.close()

    asyncio.run(exercise())
