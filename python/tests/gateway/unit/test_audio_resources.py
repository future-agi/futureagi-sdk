"""Audio transcription, speech and translation resources."""
from __future__ import annotations

import pytest
import respx
from fi.gateway import AgentCC, AsyncAgentCC
from ._resource_fixtures import GATEWAY, AGENTCC_HEADERS, COMPLETIONS_RESPONSE, SPEECH_AUDIO_BYTES


@pytest.mark.filterwarnings("default:^futureagi:fi.gateway._deprecation.AgentCCDeprecationWarning")
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
    result = client.audio.transcriptions.create(
        file=("test.mp3", b"ID3-audio"), model="whisper-1"
    )
    assert "test transcription" in result.text
    client.close()


@pytest.mark.filterwarnings("default:^futureagi:fi.gateway._deprecation.AgentCCDeprecationWarning")
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


@pytest.mark.filterwarnings("default:^futureagi:fi.gateway._deprecation.AgentCCDeprecationWarning")
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


@pytest.mark.filterwarnings("default:^futureagi:fi.gateway._deprecation.AgentCCDeprecationWarning")
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


@pytest.mark.filterwarnings("default:^futureagi:fi.gateway._deprecation.AgentCCDeprecationWarning")
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


@pytest.mark.filterwarnings("default:^futureagi:fi.gateway._deprecation.AgentCCDeprecationWarning")
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


@pytest.mark.filterwarnings("default:^futureagi:fi.gateway._deprecation.AgentCCDeprecationWarning")
@respx.mock
def test_translations_create_basic():
    respx.post(f"{GATEWAY}/v1/audio/translations").respond(
        200,
        json={"text": "Hello, this is a translated text."},
        headers=AGENTCC_HEADERS,
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    result = client.audio.translations.create(
        file=("test_german.mp3", b"ID3-audio"), model="whisper-1"
    )
    assert result.text == "Hello, this is a translated text."
    client.close()


@pytest.mark.filterwarnings("default:^futureagi:fi.gateway._deprecation.AgentCCDeprecationWarning")
@respx.mock
def test_translations_create_all_params():
    route = respx.post(f"{GATEWAY}/v1/audio/translations").respond(
        200,
        json={"text": "Translated text."},
        headers=AGENTCC_HEADERS,
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    result = client.audio.translations.create(
        file=("test_french.mp3", b"ID3-audio"),
        model="whisper-1",
        prompt="Translate the following French audio to English.",
        response_format="text",
        temperature=0.3,
    )
    assert result.text == "Translated text."

    from ._forms import read_form

    form, files = read_form(route.calls[0].request)
    assert form["model"] == ["whisper-1"]
    assert files["file"][:2] == ("test_french.mp3", b"ID3-audio")
    assert form["prompt"] == ["Translate the following French audio to English."]
    assert form["response_format"] == ["text"]
    assert form["temperature"] == ["0.3"]
    client.close()


@pytest.mark.filterwarnings("default:^futureagi:fi.gateway._deprecation.AgentCCDeprecationWarning")
@respx.mock
def test_translations_create_with_extra_body():
    route = respx.post(f"{GATEWAY}/v1/audio/translations").respond(
        200,
        json={"text": "Translated."},
        headers=AGENTCC_HEADERS,
    )

    client = AgentCC(api_key="sk-test", base_url=GATEWAY)
    client.audio.translations.create(
        file=("test.mp3", b"ID3-audio"),
        model="whisper-1",
        extra_body={"custom_param": "value"},
    )

    from ._forms import read_form

    form, _ = read_form(route.calls[0].request)
    assert form["custom_param"] == ["value"]
    client.close()


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


def test_async_audio_sub_resources():
    """Verify async client has speech and translations sub-resources."""
    client = AsyncAgentCC(api_key="sk-test", base_url=GATEWAY)
    assert type(client.audio.speech).__qualname__ == "AsyncSpeech"
    assert type(client.audio.translations).__qualname__ == "AsyncTranslations"
    assert type(client.audio.transcriptions).__qualname__ == "AsyncTranscriptions"
    # Verify caching
    assert client.audio.speech is client.audio.speech
    assert client.audio.translations is client.audio.translations
