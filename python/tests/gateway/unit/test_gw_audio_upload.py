"""Explicit normalized audio uploads use repeated list fields and string paths.

Published uploads already use multipart; their string-content and JSON field
semantics remain the default and are covered by the published-contract tests.
"""

from __future__ import annotations

import io
import json
import mimetypes
from pathlib import Path
from typing import Any

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, InternalServerError

from ._forms import read_form

GW = "http://127.0.0.1:8090"
AUDIO = b"RIFF\x00\x01fake-wave\xff"
TEXT = {"text": "hello world"}
COST = {"x-agentcc-cost": "0.25", "x-agentcc-request-id": "01ARZ3NDEKTSV4RRFFQ69G5FAV"}


def _sync(seen: list[httpx.Request], *replies: httpx.Response, **kw: Any) -> AgentCC:
    queue = list(replies)

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return queue.pop(0) if queue else httpx.Response(200, json=TEXT, headers=COST)

    return AgentCC(
        api_key="gw-key",
        base_url=GW,
        audio_upload_mode="normalized",
        metadata_mode="merge",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        **kw,
    )


def _async(seen: list[httpx.Request], **kw: Any) -> AsyncAgentCC:
    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=TEXT, headers=COST)

    return AsyncAgentCC(
        api_key="gw-key",
        base_url=GW,
        audio_upload_mode="normalized",
        metadata_mode="merge",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        **kw,
    )


def _assert_form(request: httpx.Request, filename: str, content_type: str) -> dict:
    values, files = read_form(request)
    assert files == {"file": (filename, AUDIO, content_type)}
    assert request.headers["content-type"].startswith("multipart/form-data; boundary=")
    assert "application/json" not in request.headers["content-type"]
    return values


def _guessed(filename: str) -> str:
    """The part's content type when none is given: httpx guesses it from the name."""
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


def _file_kinds(tmp_path: Path) -> list[tuple[str, Any, str, str]]:
    path = tmp_path / "speech.wav"
    path.write_bytes(AUDIO)
    wav = _guessed("speech.wav")
    return [
        ("bytes", AUDIO, "upload", "application/octet-stream"),
        ("BytesIO", io.BytesIO(AUDIO), "upload", "application/octet-stream"),
        ("open file", path.open("rb"), "speech.wav", wav),
        ("Path", path, "speech.wav", wav),
        ("tuple", ("a.mp3", AUDIO, "audio/mpeg"), "a.mp3", "audio/mpeg"),
        ("tuple, no type", ("a.mp3", AUDIO), "a.mp3", _guessed("a.mp3")),
        ("tuple of a Path", ("b.wav", path), "b.wav", wav),
    ]


@pytest.mark.parametrize("route", ["transcriptions", "translations"])
def test_every_file_kind_goes_as_the_file_part(route: str, tmp_path: Path) -> None:
    for label, file, filename, content_type in _file_kinds(tmp_path):
        seen: list[httpx.Request] = []
        client = _sync(seen)
        result = getattr(client.audio, route).create(file=file, model="whisper-1")
        assert result.text == "hello world", label
        assert len(seen) == 1 and seen[0].url.path == f"/v1/audio/{route}", label
        values = _assert_form(seen[0], filename, content_type)
        assert values == {"model": ["whisper-1"]}, label
        if hasattr(file, "close"):
            file.close()


def test_the_fields_are_form_values_and_a_list_repeats_under_its_bracket_name() -> None:
    seen: list[httpx.Request] = []
    _sync(seen).audio.transcriptions.create(
        file=("a.wav", AUDIO, "audio/wav"),
        model="whisper-1",
        language="en",
        prompt="names: Ada",
        response_format="verbose_json",
        temperature=0.2,
        timestamp_granularities=["word", "segment"],
        chunking_strategy="auto",
    )
    assert _assert_form(seen[0], "a.wav", "audio/wav") == {
        "model": ["whisper-1"],
        "language": ["en"],
        "prompt": ["names: Ada"],
        "response_format": ["verbose_json"],
        "temperature": ["0.2"],
        "timestamp_granularities[]": ["word", "segment"],
        "chunking_strategy": ["auto"],
    }


def test_translation_fields_extra_body_and_keyword_arguments() -> None:
    seen: list[httpx.Request] = []
    _sync(seen).audio.translations.create(
        file=("de.mp3", AUDIO, "audio/mpeg"),
        model="whisper-1",
        prompt="Translate",
        response_format="json",
        temperature=0,
        extra_body={"custom": "value", "temperature": 0.5},
        seed=7,
    )
    assert _assert_form(seen[0], "de.mp3", "audio/mpeg") == {
        "model": ["whisper-1"],
        "prompt": ["Translate"],
        "response_format": ["json"],
        "temperature": ["0.5"],
        "custom": ["value"],
        "seed": ["7"],
    }


@pytest.mark.parametrize("route", ["transcriptions", "translations"])
def test_a_str_is_refused_before_any_request(route: str, tmp_path: Path) -> None:
    """Historical id: explicit Path inputs read audio rather than literal path text."""
    path = tmp_path / "a.wav"
    path.write_bytes(AUDIO)
    seen: list[httpx.Request] = []
    result = getattr(_sync(seen).audio, route).create(file=path, model="whisper-1")
    assert result.text == "hello world"
    assert len(seen) == 1 and seen[0].url.path == f"/v1/audio/{route}"
    assert _assert_form(seen[0], path.name, _guessed(path.name)) == {"model": ["whisper-1"]}


@pytest.mark.parametrize("path", ["bad\x00path", "bad\npath", "bad\rpath"])
@pytest.mark.parametrize("route", ["transcriptions", "translations"])
def test_unsafe_string_is_refused_before_read_or_send(path, route, monkeypatch) -> None:
    def forbidden(*args, **kwargs):
        pytest.fail("unsafe path attempted a read")

    seen = []
    with monkeypatch.context() as patch:
        patch.setattr(Path, "open", forbidden)
        patch.setattr(Path, "read_bytes", forbidden)
        patch.setattr(io, "open", forbidden)
        with pytest.raises(TypeError, match="NUL or newline"):
            getattr(_sync(seen).audio, route).create(file=path, model="whisper-1")
    assert seen == []


def test_a_text_mode_file_is_refused_before_any_request() -> None:
    seen: list[httpx.Request] = []
    with pytest.raises(TypeError, match="binary mode|BytesIO"):
        _sync(seen).audio.transcriptions.create(
            file=io.StringIO("text"), model="whisper-1"
        )
    assert seen == []


def test_gateway_parameters_are_headers_and_metadata_follows_the_one_rule() -> None:
    seen: list[httpx.Request] = []
    client = _sync(seen, metadata={"tenant": "A"})
    client.audio.transcriptions.create(
        file=AUDIO,
        model="whisper-1",
        session_id="s1",
        trace_id="t1",
        request_metadata={"call": "1"},
        request_timeout=30,
        cache_ttl=60,
        guardrail_policy="strict",
        properties={"team": "a"},
        user_id="u1",
        request_id="r1",
        extra_headers={"X-Extra": "e"},
    )
    with client.session(name="checkout", metadata={"cart": "c1"}):
        client.audio.translations.create(file=AUDIO, model="whisper-1")
    first, second = seen
    assert json.loads(first.headers["x-agentcc-metadata"]) == {
        "tenant": "A",
        "call": "1",
    }
    for name, value in {
        "x-agentcc-session-id": "s1",
        "x-agentcc-trace-id": "t1",
        "x-agentcc-cache-ttl": "60",
        "x-guardrail-policy": "strict",
        "x-agentcc-property-team": "a",
        "x-agentcc-user-id": "u1",
        "x-agentcc-request-id": "r1",
        "x-extra": "e",
        "authorization": "Bearer gw-key",
    }.items():
        assert first.headers[name] == value, name
    assert json.loads(second.headers["x-agentcc-metadata"]) == {
        "tenant": "A",
        "cart": "c1",
    }
    assert second.headers["x-agentcc-session-name"] == "checkout"
    values, _ = read_form(first)
    assert values == {"model": ["whisper-1"]}


def test_the_answer_carries_its_metadata_and_cost() -> None:
    seen: list[httpx.Request] = []
    client = _sync(seen)
    result = client.audio.transcriptions.create(file=AUDIO, model="whisper-1")
    assert result.agentcc is not None
    assert result.agentcc.request_id == "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    assert result.agentcc.cost == 0.25
    assert client.current_cost == 0.25


def test_a_retried_upload_sends_the_whole_file_again() -> None:
    seen: list[httpx.Request] = []
    busy = httpx.Response(503, json={"error": {"message": "busy"}})
    client = _sync(seen, busy, max_retries=1)
    client._get_base_client()._calculate_delay = lambda *a, **k: 0.0
    file = io.BytesIO(AUDIO)
    assert client.audio.transcriptions.create(file=file, model="whisper-1").text
    assert len(seen) == 2
    for request in seen:
        _assert_form(request, "upload", "application/octet-stream")


def test_an_error_answer_raises_the_mapped_error() -> None:
    seen: list[httpx.Request] = []
    boom = httpx.Response(500, json={"error": {"message": "upstream failed"}})
    client = _sync(seen, boom, max_retries=0)
    with pytest.raises(InternalServerError, match="upstream failed"):
        client.audio.transcriptions.create(file=AUDIO, model="whisper-1")
    assert len(seen) == 1


@pytest.mark.anyio
async def test_the_async_uploads_are_multipart_too(tmp_path: Path) -> None:
    for route in ("transcriptions", "translations"):
        for label, file, filename, content_type in _file_kinds(tmp_path):
            seen: list[httpx.Request] = []
            client = _async(seen, metadata={"tenant": "A"})
            result = await getattr(client.audio, route).create(
                file=file, model="whisper-1", request_metadata={"call": "1"}
            )
            assert result.text == "hello world", label
            values = _assert_form(seen[0], filename, content_type)
            assert values == {"model": ["whisper-1"]}, label
            assert json.loads(seen[0].headers["x-agentcc-metadata"]) == {
                "tenant": "A",
                "call": "1",
            }
            if hasattr(file, "close"):
                file.close()
        seen = []
        path = tmp_path / "a.wav"
        path.write_bytes(AUDIO)
        result = await getattr(_async(seen).audio, route).create(file=path, model="m")
        assert result.text == "hello world"
        assert len(seen) == 1 and seen[0].url.path == f"/v1/audio/{route}"
        assert _assert_form(seen[0], path.name, _guessed(path.name)) == {"model": ["m"]}
