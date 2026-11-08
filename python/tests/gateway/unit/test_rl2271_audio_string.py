"""RL 2271 keeps string paths in 0.x without allowing unsafe path contents."""

import io
from pathlib import Path

import httpx
import pytest

from fi.gateway._fi import AsyncGateway, Gateway
from fi.gateway.resources._audio_upload import upload_part

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def clear_platform_keys(monkeypatch):
    for name in ("FI_API_KEY", "FI_SECRET_KEY"):
        monkeypatch.delenv(name, raising=False)


def test_string_path_warns_and_opens_read_only(tmp_path, monkeypatch):
    path = tmp_path / "sample.wav"
    path.write_bytes(b"unit-audio")
    opened = []
    original = Path.open

    def observe(self, mode="r", *args, **kwargs):
        opened.append((self, mode))
        return original(self, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    with pytest.warns(DeprecationWarning, match=r"Path\(\.\.\.\).*1\.0"):
        assert upload_part(str(path)) == ("sample.wav", b"unit-audio")
    assert opened == [(path, "rb")]


@pytest.mark.parametrize("path", ["bad\x00path", "bad\npath", "bad\rpath", "bad\r\npath"])
def test_unsafe_string_refused_before_any_read(path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("unsafe string attempted a file read")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "open", forbidden)
        patch.setattr(Path, "read_bytes", forbidden)
        patch.setattr(io, "open", forbidden)
        with pytest.raises(TypeError, match="NUL or newline"):
            upload_part(path)


def test_nonstring_inputs_unchanged(tmp_path):
    data = b"unit-audio"
    path = tmp_path / "sample.wav"
    path.write_bytes(data)
    assert upload_part(data) is data
    assert upload_part(path) == (path.name, data)
    for part in (("name.wav", data), ("name.wav", data, "audio/wav")):
        assert upload_part(part) is part
    assert upload_part(("override.wav", path, "audio/wav")) == (
        "override.wav", data, "audio/wav",
    )
    with path.open("rb") as binary_file:
        assert upload_part(binary_file) is binary_file
        assert binary_file.tell() == 0
    stream = io.BytesIO(data)
    assert upload_part(stream) is stream
    assert stream.tell() == 0


def test_sync_string_upload_and_failed_open_send_order(tmp_path):
    path = tmp_path / "sample.wav"
    path.write_bytes(b"unit-audio")
    sent = []

    def handle(request):
        sent.append(request)
        assert b"unit-audio" in request.content
        return httpx.Response(200, json={"text": "transcribed"})

    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        with Gateway(api_key="sk-agentcc-unit", base_url="https://gateway.example.test", http_client=http) as gateway:
            with pytest.warns(DeprecationWarning, match=r"Path\(\.\.\.\)"):
                gateway.audio.transcriptions.create(file=str(path), model="whisper-1")
            assert len(sent) == 1
            with pytest.warns(DeprecationWarning), pytest.raises(FileNotFoundError):
                gateway.audio.transcriptions.create(file=str(tmp_path / "missing.wav"), model="whisper-1")
            with pytest.raises(TypeError):
                gateway.audio.transcriptions.create(file="bad\npath", model="whisper-1")
            assert len(sent) == 1


@pytest.mark.anyio
async def test_async_string_upload_and_failed_open_send_order(tmp_path):
    path = tmp_path / "sample.wav"
    path.write_bytes(b"unit-audio")
    sent = []

    def handle(request):
        sent.append(request)
        assert b"unit-audio" in request.content
        return httpx.Response(200, json={"text": "transcribed"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        async with AsyncGateway(api_key="sk-agentcc-unit", base_url="https://gateway.example.test", http_client=http) as gateway:
            with pytest.warns(DeprecationWarning, match=r"Path\(\.\.\.\)"):
                await gateway.audio.transcriptions.create(file=str(path), model="whisper-1")
            assert len(sent) == 1
            with pytest.warns(DeprecationWarning), pytest.raises(FileNotFoundError):
                await gateway.audio.transcriptions.create(file=str(tmp_path / "missing.wav"), model="whisper-1")
            with pytest.raises(TypeError):
                await gateway.audio.transcriptions.create(file="bad\x00path", model="whisper-1")
            assert len(sent) == 1
