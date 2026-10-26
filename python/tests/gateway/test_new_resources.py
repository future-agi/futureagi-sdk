"""Tests for new API resources — embeddings, images, audio, completions, moderations, speech, translations."""

from __future__ import annotations

import respx

from fi.gateway import AgentCC
from fi.gateway._client import AsyncAgentCC

GATEWAY = "http://test-gateway:8080"

AGENTCC_HEADERS = {
    "x-agentcc-request-id": "req-1",
    "x-agentcc-trace-id": "t-1",
    "x-agentcc-provider": "openai",
    "x-agentcc-latency-ms": "10",
}


# ---------------------------------------------------------------------------
# Embeddings (existing)
# ---------------------------------------------------------------------------


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
    result = client.embeddings.create(model="text-embedding-3-small", input="Hello world")
    assert len(result.data) == 1
    assert result.data[0].embedding == [0.1, 0.2, 0.3]
    assert result.model == "text-embedding-3-small"
    client.close()


# ---------------------------------------------------------------------------
# Images (existing)
# ---------------------------------------------------------------------------


@respx.mock
def test_images_generate():
    respx.post(f"{GATEWAY}/v1/images/generations").respond(
        200,
        json={
            "created": 1700000000,
            "data": [{"url": "https://example.com/image.png", "revised_prompt": "A cute cat"}],
        },
        headers=AGENTCC_HEADERS,
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    result = client.images.generate(prompt="A cute cat")
    assert len(result.data) == 1
    assert result.data[0].url == "https://example.com/image.png"
    client.close()


# ---------------------------------------------------------------------------
# Completions
# ---------------------------------------------------------------------------

COMPLETIONS_RESPONSE = {
    "id": "cmpl-abc",
    "object": "text_completion",
    "created": 1700000000,
    "model": "gpt-3.5-turbo-instruct",
    "choices": [{"text": "Hello world!", "index": 0, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
}


@respx.mock
def test_completions_create_basic():
    respx.post(f"{GATEWAY}/v1/completions").respond(200, json=COMPLETIONS_RESPONSE, headers=AGENTCC_HEADERS)

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    result = client.completions.create(model="gpt-3.5-turbo-instruct", prompt="Say hello")
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
    route = respx.post(f"{GATEWAY}/v1/completions").respond(200, json=COMPLETIONS_RESPONSE, headers=AGENTCC_HEADERS)

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
    route = respx.post(f"{GATEWAY}/v1/completions").respond(200, json=COMPLETIONS_RESPONSE, headers=AGENTCC_HEADERS)

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
    route = respx.post(f"{GATEWAY}/v1/completions").respond(200, json=COMPLETIONS_RESPONSE, headers=AGENTCC_HEADERS)

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt="Say hello",
        extra_headers={"X-Custom-Header": "test-value"},
    )
    request = route.calls[0].request
    assert request.headers["X-Custom-Header"] == "test-value"
    client.close()


# ---------------------------------------------------------------------------
# Moderations (existing)
# ---------------------------------------------------------------------------


@respx.mock
def test_moderations_create():
    respx.post(f"{GATEWAY}/v1/moderations").respond(
        200,
        json={
            "id": "modr-abc",
            "model": "text-moderation-latest",
            "results": [
                {
                    "flagged": False,
                    "categories": {"violence": False},
                    "category_scores": {"violence": 0.01},
                }
            ],
        },
        headers=AGENTCC_HEADERS,
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    result = client.moderations.create(input="Hello world")
    assert len(result.results) == 1
    assert result.results[0].flagged is False
    client.close()


# ---------------------------------------------------------------------------
# Audio — Transcriptions (existing)
# ---------------------------------------------------------------------------


@respx.mock
def test_audio_transcriptions_create():
    respx.post(f"{GATEWAY}/v1/audio/transcriptions").respond(
        200,
        json={
            "text": "Hello, this is a test transcription.",
        },
        headers=AGENTCC_HEADERS,
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    result = client.audio.transcriptions.create(file="test.mp3", model="whisper-1")
    assert "test transcription" in result.text
    client.close()


# ---------------------------------------------------------------------------
# Audio — Speech (TTS)
# ---------------------------------------------------------------------------

SPEECH_AUDIO_BYTES = b"\xff\xfb\x90\x00\x00\x00\x00" * 100  # fake MP3 bytes


@respx.mock
def test_speech_create_basic():
    respx.post(f"{GATEWAY}/v1/audio/speech").respond(
        200,
        content=SPEECH_AUDIO_BYTES,
        headers={"content-type": "audio/mpeg"},
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    result = client.audio.speech.create(
        model="tts-1",
        input="Hello world",
        voice="alloy",
    )
    assert isinstance(result, bytes)
    assert len(result) > 0
    assert result == SPEECH_AUDIO_BYTES
    client.close()


@respx.mock
def test_speech_create_all_params():
    route = respx.post(f"{GATEWAY}/v1/audio/speech").respond(
        200,
        content=SPEECH_AUDIO_BYTES,
        headers={"content-type": "audio/wav"},
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    result = client.audio.speech.create(
        model="tts-1-hd",
        input="This is a test of text to speech.",
        voice="nova",
        response_format="wav",
        speed=1.5,
    )
    assert isinstance(result, bytes)
    assert result == SPEECH_AUDIO_BYTES

    # Verify the body was sent correctly
    import json

    body = json.loads(route.calls[0].request.content)
    assert body["model"] == "tts-1-hd"
    assert body["input"] == "This is a test of text to speech."
    assert body["voice"] == "nova"
    assert body["response_format"] == "wav"
    assert body["speed"] == 1.5
    client.close()


@respx.mock
def test_speech_returns_bytes():
    """Verify speech returns raw bytes, not a Pydantic model."""
    audio_data = b"\x00\x01\x02\x03\x04\x05"
    respx.post(f"{GATEWAY}/v1/audio/speech").respond(
        200,
        content=audio_data,
        headers={"content-type": "audio/mpeg"},
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    result = client.audio.speech.create(
        model="tts-1",
        input="Test",
        voice="echo",
    )
    assert type(result) is bytes
    assert result == audio_data
    client.close()


@respx.mock
def test_speech_default_params_not_sent():
    """When using default response_format and speed, they should not be in the body."""
    route = respx.post(f"{GATEWAY}/v1/audio/speech").respond(
        200,
        content=b"audio",
        headers={"content-type": "audio/mpeg"},
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    client.audio.speech.create(
        model="tts-1",
        input="Test",
        voice="alloy",
    )

    import json

    body = json.loads(route.calls[0].request.content)
    assert "response_format" not in body
    assert "speed" not in body
    assert body["model"] == "tts-1"
    assert body["voice"] == "alloy"
    client.close()


@respx.mock
def test_speech_with_extra_body():
    route = respx.post(f"{GATEWAY}/v1/audio/speech").respond(
        200,
        content=b"audio",
        headers={"content-type": "audio/mpeg"},
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    client.audio.speech.create(
        model="tts-1",
        input="Test",
        voice="alloy",
        extra_body={"custom_field": "value"},
    )

    import json

    body = json.loads(route.calls[0].request.content)
    assert body["custom_field"] == "value"
    client.close()


# ---------------------------------------------------------------------------
# Audio — Translations
# ---------------------------------------------------------------------------


@respx.mock
def test_translations_create_basic():
    respx.post(f"{GATEWAY}/v1/audio/translations").respond(
        200,
        json={"text": "Hello, this is a translated text."},
        headers=AGENTCC_HEADERS,
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    result = client.audio.translations.create(file="test_german.mp3", model="whisper-1")
    assert result.text == "Hello, this is a translated text."
    client.close()


@respx.mock
def test_translations_create_all_params():
    route = respx.post(f"{GATEWAY}/v1/audio/translations").respond(
        200,
        json={"text": "Translated text."},
        headers=AGENTCC_HEADERS,
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    result = client.audio.translations.create(
        file=("test_french.mp3", b"ID3audio"),
        model="whisper-1",
        prompt="Translate the following French audio to English.",
        response_format="text",
        temperature=0.3,
    )
    assert result.text == "Translated text."

    # Audio is uploaded as multipart/form-data: the file plus one form field per param.
    request = route.calls[0].request
    assert request.headers["content-type"].startswith("multipart/form-data")
    body = request.content
    assert b'name="file"; filename="test_french.mp3"' in body and b"ID3audio" in body
    for name, value in [("model", b"whisper-1"), ("prompt", b"Translate the following French audio to English."),
                        ("response_format", b"text"), ("temperature", b"0.3")]:
        assert f'name="{name}"'.encode() in body and value in body
    client.close()


@respx.mock
def test_translations_create_with_extra_body():
    route = respx.post(f"{GATEWAY}/v1/audio/translations").respond(
        200,
        json={"text": "Translated."},
        headers=AGENTCC_HEADERS,
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    client.audio.translations.create(
        file=("test.mp3", b"ID3"),
        model="whisper-1",
        extra_body={"custom_param": "value"},
    )

    body = route.calls[0].request.content
    assert b'name="custom_param"' in body and b"value" in body
    client.close()


# ---------------------------------------------------------------------------
# Lazy import / property access tests
# ---------------------------------------------------------------------------


def test_resource_properties_exist():
    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    assert hasattr(client, "embeddings")
    assert hasattr(client, "images")
    assert hasattr(client, "audio")
    assert hasattr(client, "completions")
    assert hasattr(client, "moderations")
    assert hasattr(client.audio, "transcriptions")
    assert hasattr(client.audio, "speech")
    assert hasattr(client.audio, "translations")


def test_speech_accessible_via_client():
    """Verify client.audio.speech is lazily created and cached."""
    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    speech1 = client.audio.speech
    speech2 = client.audio.speech
    assert speech1 is speech2
    assert type(speech1).__qualname__ == "Speech"


def test_translations_accessible_via_client():
    """Verify client.audio.translations is lazily created and cached."""
    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    translations1 = client.audio.translations
    translations2 = client.audio.translations
    assert translations1 is translations2
    assert type(translations1).__qualname__ == "Translations"


def test_completions_accessible_via_client():
    """Verify client.completions is lazily created and cached."""
    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    comp1 = client.completions
    comp2 = client.completions
    assert comp1 is comp2
    assert type(comp1).__qualname__ == "Completions"


def test_async_audio_sub_resources():
    """Verify async client has speech and translations sub-resources."""
    client = AsyncAgentCC(api_key="sk-test", base_url=GATEWAY)
    assert type(client.audio.speech).__qualname__ == "AsyncSpeech"
    assert type(client.audio.translations).__qualname__ == "AsyncTranslations"
    assert type(client.audio.transcriptions).__qualname__ == "AsyncTranscriptions"
    # Verify caching
    assert client.audio.speech is client.audio.speech
    assert client.audio.translations is client.audio.translations


def test_async_completions_accessible():
    """Verify async client.completions exists."""
    client = AsyncAgentCC(api_key="sk-test", base_url=GATEWAY)
    assert type(client.completions).__qualname__ == "AsyncCompletions"
    assert client.completions is client.completions
