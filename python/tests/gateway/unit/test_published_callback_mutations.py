"""Offline differential probes for the published callback mutation contract."""
import inspect
import json
import socket
from contextlib import asynccontextmanager

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway.callbacks.base import CallbackHandler

pytestmark = [pytest.mark.anyio, pytest.mark.filterwarnings("ignore::DeprecationWarning")]


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    for name in ("FI_API_KEY", "FI_SECRET_KEY", "FI_GATEWAY_API_KEY", "AGENTCC_API_KEY"):
        monkeypatch.delenv(name, raising=False)

    def refuse(*args, **kwargs):
        raise AssertionError("No sockets are permitted in callback probes")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


@asynccontextmanager
async def client_for(async_mode, callback, *, redact=True):
    seen = []

    def handler(request):
        # Capture wire values before the transport scrubs the retained request.
        seen.append(httpx.Request(request.method, request.url,
            headers=request.headers, content=request.content))
        if request.url.path.endswith(("/transcriptions", "/translations")):
            return httpx.Response(200, json={"text": "ok"})
        return httpx.Response(200, json={
            "id": "reply", "object": "chat.completion", "created": 0,
            "model": "test", "choices": [],
        })

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(handler))
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key="unit-key", base_url="https://gateway.example.test", http_client=http,
        max_retries=0, callbacks=[callback], redact_messages=redact,
    )
    try:
        yield client, seen
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("async_mode", [False, True])
async def test_redacted_deep_message_edits_are_published_shared_values(async_mode):
    calls = []

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            calls.append(request.body["messages"][0]["content"])
            request.body["messages"][0]["annotations"]["label"] = "after"
            request.body["messages"][0]["tool_calls"][0]["function"]["schema"]["label"] = "after"

    message = {"role": "assistant", "content": "private text", "annotations": {"label": "before"},
               "tool_calls": [{"id": "call", "type": "function", "function": {
                   "name": "tool", "arguments": "private arguments", "schema": {"label": "before"}}}]}
    async with client_for(async_mode, Edit()) as (client, seen):
        await resolve(client.chat.completions.create(model="test", messages=[message]))
    assert calls == ["[REDACTED]"]
    wire = json.loads(seen[0].content)
    assert wire["messages"][0]["content"] == "private text"
    assert wire["messages"][0]["annotations"]["label"] == "after"
    assert wire["messages"][0]["tool_calls"][0]["function"]["schema"]["label"] == "after"


@pytest.mark.parametrize("async_mode", [False, True])
async def test_redacted_header_reassignment_stays_on_descriptor_copy(async_mode):
    calls = []

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            calls.append(True)
            request.headers = {"X-Replaced": "after"}

    async with client_for(async_mode, Edit()) as (client, seen):
        await resolve(client.chat.completions.create(
            model="test", messages=[{"role": "user", "content": "private text"}],
            extra_headers={"X-Original": "before"}))
    assert calls == [True]
    assert seen[0].headers.get("x-original") == "before"
    assert "x-replaced" not in seen[0].headers


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("route", ["transcriptions", "translations"])
async def test_redacted_file_reassignment_stays_on_descriptor_copy(async_mode, route):
    calls = []

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            calls.append(True)
            request.files = {"file": ("after.wav", b"after")}

    async with client_for(async_mode, Edit()) as (client, seen):
        await resolve(getattr(client.audio, route).create(
            model="test", file=("before.wav", b"before"), prompt="private text"))
    assert calls == [True]
    assert b'filename="before.wav"' in seen[0].content
    assert b'filename="after.wav"' not in seen[0].content


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
async def test_reordering_masked_nested_records_keeps_original_record_associations(async_mode, redact):
    calls = []

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            calls.append(True)
            request.body["metadata"]["records"].reverse()

    original = [{"name": "first", "password": "first-placeholder"},
                {"name": "second", "password": "second-placeholder"}]
    async with client_for(async_mode, Edit(), redact=redact) as (client, seen):
        await resolve(client.chat.completions.create(
            model="test", messages=[], metadata={"records": original}))
    assert calls == [True]
    assert json.loads(seen[0].content)["metadata"]["records"] == [
        {"name": "second", "password": "second-placeholder"},
        {"name": "first", "password": "first-placeholder"},
    ]
