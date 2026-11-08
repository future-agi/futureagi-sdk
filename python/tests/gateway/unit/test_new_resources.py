"""Embedding, image and completion resources."""
from __future__ import annotations
import respx
from fi.gateway import AgentCC, AsyncAgentCC
from ._resource_fixtures import GATEWAY, AGENTCC_HEADERS, COMPLETIONS_RESPONSE, SPEECH_AUDIO_BYTES


@respx.mock
def test_embeddings_create():
    respx.post(f"{GATEWAY}/v1/embeddings").respond(
        200,
        json={
            "object": "list",
            "data": [{"object": "embedding", "embedding": [0.1, 0.2, 0.3], "index": 0}],
            "model": "text-embedding-3-small",
            "usage": {"prompt_tokens": 5, "completion_tokens": 0, "total_tokens": 5},
        },
        headers=AGENTCC_HEADERS,
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    result = client.embeddings.create(
        model="text-embedding-3-small", input="Hello world"
    )
    assert len(result.data) == 1
    assert result.data[0].embedding == [0.1, 0.2, 0.3]
    assert result.model == "text-embedding-3-small"
    client.close()


@respx.mock
def test_images_generate():
    respx.post(f"{GATEWAY}/v1/images/generations").respond(
        200,
        json={
            "created": 1700000000,
            "data": [
                {"url": "https://example.com/image.png", "revised_prompt": "A cute cat"}
            ],
        },
        headers=AGENTCC_HEADERS,
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    result = client.images.generate(prompt="A cute cat")
    assert len(result.data) == 1
    assert result.data[0].url == "https://example.com/image.png"
    client.close()


@respx.mock
def test_completions_create_basic():
    respx.post(f"{GATEWAY}/v1/completions").respond(
        200, json=COMPLETIONS_RESPONSE, headers=AGENTCC_HEADERS
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    result = client.completions.create(
        model="gpt-3.5-turbo-instruct", prompt="Say hello"
    )
    assert result.id == "cmpl-abc"
    assert result.object == "text_completion"
    assert result.model == "gpt-3.5-turbo-instruct"
    assert result.choices[0].text == "Hello world!"
    assert result.choices[0].index == 0
    assert result.choices[0].finish_reason == "stop"
    assert result.usage is not None
    assert result.usage.prompt_tokens == 3
    assert result.usage.completion_tokens == 2
    assert result.usage.total_tokens == 5
    client.close()


@respx.mock
def test_completions_create_all_params():
    route = respx.post(f"{GATEWAY}/v1/completions").respond(
        200, json=COMPLETIONS_RESPONSE, headers=AGENTCC_HEADERS
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    result = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt="Say hello",
        max_tokens=100,
        temperature=0.7,
        top_p=0.9,
        n=1,
        stream=False,
        stop=["\n"],
        presence_penalty=0.1,
        frequency_penalty=0.2,
        logit_bias={"50256": -100},
        logprobs=5,
        echo=False,
        suffix=" world",
        best_of=1,
        user="test-user",
        seed=42,
    )
    assert result.choices[0].text == "Hello world!"

    # Verify the body was sent correctly
    request = route.calls[0].request
    import json

    body = json.loads(request.content)
    assert body["model"] == "gpt-3.5-turbo-instruct"
    assert body["prompt"] == "Say hello"
    assert body["max_tokens"] == 100
    assert body["temperature"] == 0.7
    assert body["top_p"] == 0.9
    assert body["n"] == 1
    assert body["stream"] is False
    assert body["stop"] == ["\n"]
    assert body["presence_penalty"] == 0.1
    assert body["frequency_penalty"] == 0.2
    assert body["logit_bias"] == {"50256": -100}
    assert body["logprobs"] == 5
    assert body["echo"] is False
    assert body["suffix"] == " world"
    assert body["best_of"] == 1
    assert body["user"] == "test-user"
    assert body["seed"] == 42
    client.close()


@respx.mock
def test_completions_create_with_prompt_list():
    respx.post(f"{GATEWAY}/v1/completions").respond(
        200,
        json={
            "id": "cmpl-list",
            "object": "text_completion",
            "created": 1700000000,
            "model": "gpt-3.5-turbo-instruct",
            "choices": [
                {"text": "Hello!", "index": 0, "finish_reason": "stop"},
                {"text": "Hi!", "index": 1, "finish_reason": "stop"},
            ],
            "usage": {"prompt_tokens": 6, "completion_tokens": 4, "total_tokens": 10},
        },
        headers=AGENTCC_HEADERS,
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    result = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=["Say hello", "Say hi"],
    )
    assert len(result.choices) == 2
    assert result.choices[0].text == "Hello!"
    assert result.choices[1].text == "Hi!"
    client.close()


@respx.mock
def test_completions_create_with_extra_body():
    route = respx.post(f"{GATEWAY}/v1/completions").respond(
        200, json=COMPLETIONS_RESPONSE, headers=AGENTCC_HEADERS
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    result = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt="Say hello",
        extra_body={"custom_param": "value"},
    )
    assert result.choices[0].text == "Hello world!"

    import json

    body = json.loads(route.calls[0].request.content)
    assert body["custom_param"] == "value"
    client.close()


@respx.mock
def test_completions_create_with_extra_headers():
    route = respx.post(f"{GATEWAY}/v1/completions").respond(
        200, json=COMPLETIONS_RESPONSE, headers=AGENTCC_HEADERS
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt="Say hello",
        extra_headers={"X-Custom-Header": "test-value"},
    )
    request = route.calls[0].request
    assert request.headers["X-Custom-Header"] == "test-value"
    client.close()


def test_resource_properties_exist():
    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    assert hasattr(client, "embeddings")
    assert hasattr(client, "images")
    assert hasattr(client, "audio")
    assert hasattr(client, "completions")
    assert hasattr(client.audio, "transcriptions")
    assert hasattr(client.audio, "speech")
    assert hasattr(client.audio, "translations")


def test_completions_accessible_via_client():
    """Verify client.completions is lazily created and cached."""
    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    comp1 = client.completions
    comp2 = client.completions
    assert comp1 is comp2
    assert type(comp1).__qualname__ == "Completions"


def test_async_completions_accessible():
    """Verify async client.completions exists."""
    client = AsyncAgentCC(api_key="sk-test", base_url=GATEWAY)
    assert type(client.completions).__qualname__ == "AsyncCompletions"
    assert client.completions is client.completions
