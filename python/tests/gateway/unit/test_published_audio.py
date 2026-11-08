"""Actual multipart requests preserve the published upload interpretation."""

import io
import json
from pathlib import Path

import pytest

from fi.gateway._constants import NOT_GIVEN

from ._forms import read_form
from ._published_helpers import client_for, clear_platform_keys, resolve

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("route", ["transcriptions", "translations"])
@pytest.mark.parametrize("kind", ["str", "nul", "newline", "existing_name", "bytes", "stream", "tuple", "path", "tuple_path"])
async def test_published_file_parts(async_mode, route, kind, tmp_path, monkeypatch):
    path = tmp_path / "audio.wav"
    path.write_bytes(b"disk bytes")
    content = {"str": "literal audio", "nul": "literal\x00audio", "newline": "literal\naudio\r",
               "existing_name": str(path), "bytes": b"binary\x00audio", "stream": io.BytesIO(b"stream bytes"),
               "tuple": ("named.wav", b"tuple bytes", "audio/wav"), "path": path,
               "tuple_path": ("renamed.wav", path)}[kind]
    expected = {"bytes": b"binary\x00audio", "stream": b"stream bytes", "tuple": b"tuple bytes",
                "path": b"disk bytes", "tuple_path": b"disk bytes"}.get(kind)
    if expected is None:
        expected = content.encode()

    def forbidden(*args, **kwargs):
        pytest.fail("Literal upload content attempted a filesystem read")

    async with client_for(async_mode) as (client, seen):
        with monkeypatch.context() as patch:
            if isinstance(content, str):
                patch.setattr(Path, "read_bytes", forbidden)
                patch.setattr(Path, "open", forbidden)
            result = await resolve(getattr(client.audio, route).create(file=content, model="test"))
    assert result.text == "ok"
    values, files = read_form(seen[0])
    assert files["file"][1] == expected
    assert values == {"model": ["test"]}
    if kind == "path":
        assert files["file"][0] == "audio.wav"
    if kind.startswith("tuple"):
        assert files["file"][0] == content[0]


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("route", ["transcriptions", "translations"])
async def test_published_form_serialization(async_mode, route):
    # Only a method's own omitted parameters are skipped; keyword and extra-body
    # values are serialized as given, the omission sentinel included.
    async with client_for(async_mode) as (client, seen):
        await resolve(getattr(client.audio, route).create(file=b"audio", model="test", prompt=None,
            temperature=0.5, response_format=NOT_GIVEN, timestamp_granularities=["word", "segment"],
            custom={"key": [1, 2]}, enabled=True, passthrough=NOT_GIVEN, extra_body={"extra": [1]}))
    values, files = read_form(seen[0])
    extra = ({"extra_body": [json.dumps({"extra": [1]})]} if route == "transcriptions"
             else {"extra": [json.dumps([1])]})
    assert values == {"model": ["test"], "prompt": ["None"], "temperature": ["0.5"],
        "timestamp_granularities": [json.dumps(["word", "segment"])],
        "custom": [json.dumps({"key": [1, 2]})], "enabled": ["True"],
        "passthrough": ["NOT_GIVEN"], **extra}
    assert files["file"][1] == b"audio"


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("route", ["transcriptions", "translations"])
async def test_normalized_uploads_are_explicit_and_survive_option_copies(async_mode, route, tmp_path):
    path = tmp_path / "audio.wav"
    path.write_bytes(b"disk bytes")
    async with client_for(async_mode, alias=True, audio_upload_mode="normalized") as (parent, seen):
        client = parent.with_options()
        with pytest.warns(DeprecationWarning, match="String audio paths"):
            await resolve(getattr(client.audio, route).create(file=str(path), model="test", prompt=None,
                temperature=0.5, timestamp_granularities=["word", "segment"]))
    fields, files = read_form(seen[0])
    assert files["file"][:2] == ("audio.wav", b"disk bytes")
    assert fields == {"model": ["test"], "temperature": ["0.5"],
                      "timestamp_granularities[]": ["word", "segment"]}


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("route", ["transcriptions", "translations"])
@pytest.mark.parametrize("redact", [False, True])
async def test_published_multipart_callback_and_session_interoperability(async_mode, route, redact):
    from fi.gateway.callbacks.base import CallbackHandler

    snapshots = []

    class Mutate(CallbackHandler):
        def on_request_start(self, request):
            # Recorded here, asserted below: handler exceptions never reach the caller.
            snapshots.append((request.url, dict(request.body["custom"]), request.body["prompt"],
                              dict(request.files)))
            request.body["custom"]["key"] = 2
            request.headers["X-Callback"] = "yes"

    async with client_for(async_mode, alias=True, callbacks=[Mutate()], redact_messages=redact,
                          metadata={"client": "cleared"}) as (client, seen):
        with client.session(metadata={"session": "separate"}):
            await resolve(getattr(client.audio, route).create(file="literal\x00audio", model="test",
                prompt="original", custom={"key": 1}, request_metadata={}))
    fields, files = read_form(seen[0])
    assert snapshots == [("/v1/audio/" + route, {"key": 1}, "[REDACTED]" if redact else "original",
                          {"file": "literal\x00audio"})]
    assert files["file"][1] == b"literal\x00audio"
    assert fields["custom"] == [json.dumps({"key": 2})]
    assert fields["prompt"] == ["original"]
    assert seen[0].headers["x-callback"] == "yes"
    assert seen[0].headers["x-agentcc-metadata"] == "{}"
    assert seen[0].headers["x-agentcc-metadata-session"] == "separate"
