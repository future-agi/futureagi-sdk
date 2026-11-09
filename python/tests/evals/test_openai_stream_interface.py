"""Instrumented streams retain the installed provider's public lifecycle API."""

import asyncio
import json

import httpx
import openai
import pytest
from opentelemetry.trace import NoOpTracer

from fi.evals.otel.instrumentors.openai import OpenAIInstrumentor


def _transport():
    chunk = {"id": "chat-test", "object": "chat.completion.chunk", "created": 0,
             "model": "test-model", "choices": [{"index": 0, "delta": {
                 "content": "local reply"}, "finish_reason": None}]}
    payload = "data: " + json.dumps(chunk) + "\n\ndata: [DONE]\n\n"
    return httpx.MockTransport(lambda request: httpx.Response(
        200, headers={"content-type": "text/event-stream"},
        stream=httpx.ByteStream(payload.encode())))


@pytest.fixture
def instrumentor():
    instance = OpenAIInstrumentor()
    instance._tracer = NoOpTracer()
    instance.instrument()
    assert instance.is_instrumented
    try:
        yield instance
    finally:
        instance.uninstrument()


def _client(is_async=False):
    client_type = openai.AsyncOpenAI if is_async else openai.OpenAI
    http_type = httpx.AsyncClient if is_async else httpx.Client
    return client_type(api_key="test-only", base_url="https://provider.invalid/v1",
                       max_retries=0, http_client=http_type(
                           transport=_transport(), trust_env=False))


def _create(client):
    return client.chat.completions.create(
        model="test-model", messages=[{"role": "user", "content": "hello"}], stream=True)


@pytest.mark.parametrize("consume", ["none", "partial", "all"])
def test_sync_stream_context_manager_preserves_iteration_and_closes(instrumentor, consume):
    with _client() as client:
        stream = _create(client)
        underlying = stream._stream
        try:
            with stream as entered:
                assert entered is stream
                if consume == "partial":
                    assert next(entered).choices[0].delta.content == "local reply"
                elif consume == "all":
                    assert len(list(entered)) == 1
            assert underlying.response.is_closed
        finally:
            underlying.close()


@pytest.mark.parametrize("consume", ["none", "partial", "all"])
def test_async_stream_context_manager_preserves_iteration_and_closes(instrumentor, consume):
    async def exercise():
        async with _client(True) as client:
            stream = await _create(client)
            underlying = stream._stream
            try:
                async with stream as entered:
                    assert entered is stream
                    if consume == "partial":
                        assert (await entered.__anext__()).choices[0].delta.content == "local reply"
                    elif consume == "all":
                        assert len([chunk async for chunk in entered]) == 1
                assert underlying.response.is_closed
            finally:
                await underlying.close()

    asyncio.run(exercise())


def test_sync_stream_delegates_response_and_explicit_close(instrumentor):
    with _client() as client:
        stream = _create(client)
        underlying = stream._stream
        try:
            stream.close()
            stream.close()
            assert stream.response is underlying.response
            assert stream.response.is_closed
        finally:
            underlying.close()


def test_async_stream_delegates_response_and_explicit_close(instrumentor):
    async def exercise():
        async with _client(True) as client:
            stream = await _create(client)
            underlying = stream._stream
            try:
                await stream.close()
                await stream.close()
                assert stream.response is underlying.response
                assert stream.response.is_closed
            finally:
                await underlying.close()

    asyncio.run(exercise())


def test_sync_context_exception_reaches_provider_exit(instrumentor, monkeypatch):
    with _client() as client:
        stream = _create(client)
        underlying = stream._stream
        exits = []
        original_exit = type(underlying).__exit__

        def exit_stream(self, *args):
            exits.append(args)
            return original_exit(self, *args)

        monkeypatch.setattr(type(underlying), "__exit__", exit_stream)
        error = ValueError("consumer failed")
        try:
            with pytest.raises(ValueError) as caught:
                with stream:
                    raise error
            assert caught.value is error
            assert len(exits) == 1
            assert exits[0][0] is ValueError and exits[0][1] is error
            assert underlying.response.is_closed
        finally:
            underlying.close()


def test_async_context_exception_reaches_provider_exit(instrumentor, monkeypatch):
    async def exercise():
        async with _client(True) as client:
            stream = await _create(client)
            underlying = stream._stream
            exits = []
            original_exit = type(underlying).__aexit__

            async def exit_stream(self, *args):
                exits.append(args)
                return await original_exit(self, *args)

            monkeypatch.setattr(type(underlying), "__aexit__", exit_stream)
            error = ValueError("consumer failed")
            try:
                with pytest.raises(ValueError) as caught:
                    async with stream:
                        raise error
                assert caught.value is error
                assert len(exits) == 1
                assert exits[0][0] is ValueError and exits[0][1] is error
                assert underlying.response.is_closed
            finally:
                await underlying.close()

    asyncio.run(exercise())


def test_disabling_stream_capture_returns_the_provider_stream(instrumentor):
    instrumentor._capture_streaming = False
    with _client() as client:
        with _create(client) as stream:
            assert isinstance(stream, openai.Stream)
            assert len(list(stream)) == 1
        assert stream.response.is_closed
