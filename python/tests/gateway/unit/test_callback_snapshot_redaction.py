"""Released multipart snapshots without composed configuration credentials."""

import copy
import json
from types import SimpleNamespace

import httpx
import pytest

from fi.gateway._fi import AsyncGateway, Gateway
from fi.gateway._gateway_config import GatewayConfig, LoadBalanceConfig, LoadBalanceTarget
from fi.gateway._transport._async import AsyncBaseClient
from fi.gateway._transport._base import RequestOptions
from fi.gateway._transport._sync import SyncBaseClient
from fi.gateway.callbacks.base import CallbackHandler

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
KEY = "sk-agentcc-callback-unit"
VIRTUAL_KEY = "sk-agentcc-load-balance-unit"
FILE_BYTES = b"private-file-bytes-not-for-callbacks"
ORIGIN = "https://gateway.example.test"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def clear_platform_keys(monkeypatch):
    for name in ("FI_API_KEY", "FI_SECRET_KEY"):
        monkeypatch.delenv(name, raising=False)


def configuration():
    return GatewayConfig(load_balance=LoadBalanceConfig(targets=[
        LoadBalanceTarget(model="test", virtual_key=VIRTUAL_KEY),
    ]))


@pytest.mark.parametrize("transport_type", [SyncBaseClient, AsyncBaseClient])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("multipart", [False, True])
def test_snapshot_does_not_disclose_or_mutate_credentials(transport_type, redact, multipart):
    transport = transport_type(api_key=KEY, base_url=ORIGIN, config=configuration(), redact_messages=redact,
                               owner=SimpleNamespace(_callback_mode="snapshot"))
    body = {
        "model": "whisper-1", "prompt": "private prompt",
        "messages": [{"role": "user", "content": "private message"}],
        "metadata": {"nested": [{"virtual_key": VIRTUAL_KEY, "api_key": KEY}]},
    }
    original = copy.deepcopy(body)
    headers = {
        "X-AgentCC-Config": json.dumps({"virtual_key": VIRTUAL_KEY}),
        "Authorization": f"Bearer {KEY}", "X-API-Key": KEY,
        "Cookie": "cookie-unit", "Proxy-Authorization": "proxy-unit", "X-Visible": "yes",
    }
    options = RequestOptions(
        method="POST", url="/v1/audio/transcriptions", headers=headers,
        body=None if multipart else body,
        form=body if multipart else None,
        files={"file": ("sample.wav", FILE_BYTES)} if multipart else None,
    )
    transport._bind_request(options)
    snapshot = transport._for_callbacks(options)
    assert snapshot.body["model"] == "whisper-1"
    assert snapshot.headers["X-Visible"] == "yes"
    assert all(k.lower() != "x-agentcc-config" for k in snapshot.headers)
    rendered = repr(snapshot)
    for credential in (KEY, VIRTUAL_KEY, "cookie-unit", "proxy-unit", FILE_BYTES.decode()):
        assert credential not in rendered
    if redact:
        assert snapshot.body["prompt"] == "[REDACTED]"
        assert snapshot.body["messages"][0]["content"] == "[REDACTED]"
        assert "private prompt" not in rendered
        assert "private message" not in rendered
    else:
        assert snapshot.body["prompt"] == "private prompt"
    assert body == original
    assert headers["Authorization"] == f"Bearer {KEY}"
    assert KEY in transport._build_headers(options)["Authorization"]
    assert VIRTUAL_KEY in transport._build_headers(options)["x-agentcc-config"]
    assert snapshot.body is not body


class Recorder(CallbackHandler):
    def __init__(self):
        self.requests = []

    def on_request_start(self, request):
        self.requests.append(request)

    def on_request_end(self, request, response):
        self.requests.append(request)


def handler(sent):
    def handle(request):
        sent.append(request)
        assert FILE_BYTES in request.content
        assert VIRTUAL_KEY in request.headers["x-agentcc-config"]
        assert request.headers["authorization"] == f"Bearer {KEY}"
        if request.url.path.endswith("/files"):
            return httpx.Response(200, json={
                "id": "file-unit", "object": "file", "bytes": len(FILE_BYTES),
                "created_at": 0, "filename": "sample.wav", "purpose": "assistants",
                "status": "processed",
            })
        assert b"private prompt" in request.content
        return httpx.Response(200, json={"text": "transcribed"})
    return handle


def assert_snapshots(recorder, redact):
    assert len(recorder.requests) == 4
    audio = recorder.requests[0]
    assert recorder.requests[1] is audio
    assert audio.body["model"] == "whisper-1"
    assert audio.body["prompt"] == ("[REDACTED]" if redact else "private prompt")
    assert recorder.requests[2].body == {"purpose": "assistants"}
    assert recorder.requests[3] is recorder.requests[2]
    for request in recorder.requests:
        assert "file" not in request.body
        assert all(k.lower() != "x-agentcc-config" for k in request.headers)
        rendered = repr(request)
        assert KEY not in rendered
        assert VIRTUAL_KEY not in rendered
        assert FILE_BYTES.decode() not in rendered


@pytest.mark.parametrize("redact", [False, True])
def test_sync_audio_and_files_callbacks_keep_form_not_file(redact):
    recorder, sent = Recorder(), []
    with httpx.Client(transport=httpx.MockTransport(handler(sent))) as http:
        with Gateway(api_key=KEY, base_url=ORIGIN, http_client=http, config=configuration(),
                     callbacks=[recorder], redact_messages=redact, callback_mode="snapshot") as gateway:
            gateway.audio.transcriptions.create(file=FILE_BYTES, model="whisper-1", prompt="private prompt")
            gateway.files.create(file=("sample.wav", FILE_BYTES), purpose="assistants")
    assert len(sent) == 2
    assert_snapshots(recorder, redact)


@pytest.mark.anyio
@pytest.mark.parametrize("redact", [False, True])
async def test_async_audio_and_files_callbacks_keep_form_not_file(redact):
    recorder, sent = Recorder(), []
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler(sent))) as http:
        async with AsyncGateway(api_key=KEY, base_url=ORIGIN, http_client=http, config=configuration(),
                                callbacks=[recorder], redact_messages=redact, callback_mode="snapshot") as gateway:
            await gateway.audio.transcriptions.create(file=FILE_BYTES, model="whisper-1", prompt="private prompt")
            await gateway.files.create(file=("sample.wav", FILE_BYTES), purpose="assistants")
    assert len(sent) == 2
    assert_snapshots(recorder, redact)
