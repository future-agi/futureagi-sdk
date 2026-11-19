"""Exercise installed provider APIs with local responses, not version assertions."""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import socket

import httpx
import pytest


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setenv("LITELLM_LOCAL_MODEL_COST_MAP", "True")
    monkeypatch.setenv("DO_NOT_TRACK", "1")

    def refuse(*args, **kwargs):
        raise AssertionError("network is forbidden in provider contracts")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)


def _dependency(name):
    try:
        spec = importlib.util.find_spec(name)
    except ModuleNotFoundError:
        spec = None
    if spec is None:
        pytest.skip("futureagi[evals] is not installed: " + name)
    # An installed but broken dependency must fail, rather than become a skip.
    return importlib.import_module(name)


def _transport(requests):
    def reply(request):
        body = json.loads(request.content)
        requests.append((request.url.path, body))
        usage = {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3}
        if request.url.path == "/v1/moderations":
            payload = {"id": "modr-test", "model": body["model"], "results": [{
                "flagged": True, "categories": {"violence": True},
                "category_scores": {"violence": 0.9},
                "category_applied_input_types": {"violence": ["text"]},
            }]}
        elif request.url.path == "/v1/chat/completions":
            payload = {"id": "chat-test", "object": "chat.completion", "created": 0,
                       "model": body["model"], "usage": usage, "choices": [{
                           "index": 0, "finish_reason": "stop",
                           "message": {"role": "assistant", "content": "local reply"},
                       }]}
        elif request.url.path == "/v1/embeddings":
            payload = {"object": "list", "model": body["model"],
                       "usage": {"prompt_tokens": 2, "total_tokens": 2},
                       "data": [{"object": "embedding", "index": 0, "embedding": [0.25, 0.5]}]}
        elif request.url.path == "/v1/completions":
            payload = {"id": "completion-test", "object": "text_completion", "created": 0,
                       "model": body["model"], "usage": usage, "choices": [{
                           "index": 0, "finish_reason": "stop", "text": "local reply",
                           "logprobs": None,
                       }]}
        else:
            raise AssertionError("unexpected provider route")
        return httpx.Response(200, json=payload)

    return httpx.MockTransport(reply)


def _assert_moderation(results):
    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].category == "violence"
    assert results[0].score == pytest.approx(0.9)
    assert results[0].action == "block"


def test_guardrails_constructs_installed_sync_and_async_clients_and_calls(monkeypatch):
    openai = _dependency("openai")
    from fi.evals.guardrails.backends.openai import OpenAIBackend
    from fi.evals.guardrails.config import GuardrailModel, RailType

    sync_type, async_type = openai.OpenAI, openai.AsyncOpenAI
    requests, sync_clients, async_clients = [], [], []

    def sync_factory(**kwargs):
        client = sync_type(**kwargs, base_url="https://provider.invalid/v1", max_retries=0,
                           http_client=httpx.Client(transport=_transport(requests), trust_env=False))
        sync_clients.append(client)
        return client

    def async_factory(**kwargs):
        client = async_type(**kwargs, base_url="https://provider.invalid/v1", max_retries=0,
                            http_client=httpx.AsyncClient(transport=_transport(requests), trust_env=False))
        async_clients.append(client)
        return client

    monkeypatch.setattr(openai, "OpenAI", sync_factory)
    monkeypatch.setattr(openai, "AsyncOpenAI", async_factory)
    backend = OpenAIBackend(GuardrailModel.OPENAI_MODERATION, api_key="test-only")
    try:
        _assert_moderation(backend.classify("sample text", RailType.INPUT))
        assert len(sync_clients) == 1 and isinstance(sync_clients[0], sync_type)
        assert backend._get_client() is sync_clients[0]
    finally:
        for client in sync_clients:
            client.close()

    async def exercise_async():
        try:
            _assert_moderation(await backend.classify_async("sample text", RailType.INPUT))
            assert len(async_clients) == 1 and isinstance(async_clients[0], async_type)
        finally:
            for client in async_clients:
                await client.close()

    asyncio.run(exercise_async())
    assert requests == [("/v1/moderations", {"input": "sample text", "model": "omni-moderation-latest"})] * 2


def test_litellm_provider_completes_through_installed_mock_response_api(monkeypatch):
    litellm = _dependency("litellm")
    _dependency("openai")
    from fi.evals.llm import LiteLLMProvider

    # Use LiteLLM's actual completion() and ModelResponse conversion, not a fake module.
    monkeypatch.setattr(litellm, "telemetry", False, raising=False)
    monkeypatch.setattr(litellm, "drop_params", litellm.drop_params)
    provider = LiteLLMProvider(credentials={"api_key": "test-only"})
    assert provider.get_completion(
        "openai/gpt-4o-mini", [{"role": "user", "content": "sample text"}],
        mock_response="local reply",
    ) == "local reply"


@pytest.mark.parametrize("kind", ["APIError", "APIConnectionError", "RateLimitError"])
def test_litellm_provider_wraps_installed_openai_exception_types(monkeypatch, kind):
    litellm = _dependency("litellm")
    openai = _dependency("openai")
    from fi.evals.llm import LiteLLMProvider

    request = httpx.Request("POST", "https://provider.invalid/v1/chat/completions")
    if kind == "APIError":
        error = openai.APIError("local failure", request=request, body=None)
    elif kind == "APIConnectionError":
        error = openai.APIConnectionError(message="local failure", request=request)
    else:
        response = httpx.Response(429, request=request)
        error = openai.RateLimitError("local failure", response=response, body=None)
    assert isinstance(error, openai.APIError)

    def fail(**kwargs):
        raise error

    monkeypatch.setattr(litellm, "completion", fail)
    monkeypatch.setattr(litellm, "drop_params", litellm.drop_params)
    with pytest.raises(RuntimeError, match="^LiteLLM provider failed:") as caught:
        LiteLLMProvider().get_completion("openai/gpt-4o-mini", [])
    assert caught.value.__cause__ is error


def test_instrumentor_wraps_calls_and_restores_installed_openai_targets(monkeypatch):
    openai = _dependency("openai")
    _dependency("opentelemetry.sdk.trace")
    from openai.resources.chat import completions as chat
    from openai.resources import completions, embeddings
    from opentelemetry.trace import NoOpTracer
    from fi.evals.otel.instrumentors.openai import OpenAIInstrumentor

    targets = (chat.Completions, chat.AsyncCompletions, embeddings.Embeddings,
               embeddings.AsyncEmbeddings, completions.Completions)
    originals = {target: target.create for target in targets}
    instrumentor = OpenAIInstrumentor()
    monkeypatch.setattr(instrumentor, "get_tracer", lambda: NoOpTracer())
    requests = []
    try:
        instrumentor.instrument()
        assert instrumentor.is_instrumented
        for target, original in originals.items():
            assert target.create is not original
            assert target.create.__wrapped__ is original
        with openai.OpenAI(api_key="test-only", base_url="https://provider.invalid/v1",
                           max_retries=0, http_client=httpx.Client(
                               transport=_transport(requests), trust_env=False)) as client:
            chat_result = client.chat.completions.create(
                model="gpt-4o-mini", messages=[{"role": "user", "content": "sample text"}])
            assert chat_result.choices[0].message.content == "local reply"
            embedding = client.embeddings.create(model="text-embedding-3-small", input="sample text",
                                                 encoding_format="float")
            assert embedding.data[0].embedding == [0.25, 0.5]
            completion = client.completions.create(model="test-model", prompt="sample text")
            assert completion.choices[0].text == "local reply"

        async def exercise_async():
            async with openai.AsyncOpenAI(api_key="test-only", base_url="https://provider.invalid/v1",
                                          max_retries=0, http_client=httpx.AsyncClient(
                                              transport=_transport(requests), trust_env=False)) as client:
                chat_result = await client.chat.completions.create(
                    model="gpt-4o-mini", messages=[{"role": "user", "content": "sample text"}])
                assert chat_result.choices[0].message.content == "local reply"
                embedding = await client.embeddings.create(
                    model="text-embedding-3-small", input="sample text", encoding_format="float")
                assert embedding.data[0].embedding == [0.25, 0.5]

        asyncio.run(exercise_async())
        assert [path for path, _ in requests] == [
            "/v1/chat/completions", "/v1/embeddings", "/v1/completions",
            "/v1/chat/completions", "/v1/embeddings",
        ]
    finally:
        instrumentor.uninstrument()
        # Check the instrumentor's own restoration, then isolate any failing test.
        try:
            assert not instrumentor.is_instrumented
            for target, original in originals.items():
                assert target.create is original
        finally:
            for target, original in originals.items():
                target.create = original
