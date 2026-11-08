"""Offline wire helpers for the published gateway contract."""

import inspect
import json
from contextlib import asynccontextmanager

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, Gateway, AsyncGateway

ORIGIN = "https://gateway.example.test"
CHAT = {
    "id": "reply", "object": "chat.completion", "created": 0, "model": "test",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5},
}
RESPONSE_HEADERS = {
    "x-agentcc-cost": "0.25", "x-agentcc-cache": "hit",
    "x-agentcc-fallback-used": "true", "x-agentcc-model-used": "fallback",
}


@pytest.fixture(autouse=True)
def clear_platform_keys(monkeypatch):
    for name in ("FI_API_KEY", "FI_SECRET_KEY"):
        monkeypatch.delenv(name, raising=False)


def wire_snapshot(request):
    """The request exactly as dispatched, for assertions about the wire.

    The client masks credential and client-composed headers on every retained
    request once a send finishes, so handlers record this copy at dispatch time
    instead of reading the original request afterwards.
    """
    return httpx.Request(request.method, request.url, headers=request.headers,
                         content=request.content, extensions=request.extensions)


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


@asynccontextmanager
async def client_for(async_mode, *, alias=False, reply=None, **options):
    seen = []

    def handler(request):
        # Wire observations are snapshots: retained exchange headers are scrubbed.
        seen.append(httpx.Request(request.method, request.url,
            headers=request.headers, content=request.content))
        if reply is not None:
            return reply(request)
        path = request.url.path
        if path.endswith("/speech"):
            return httpx.Response(201, content=b"audio", headers=RESPONSE_HEADERS)
        if path.endswith(("/transcriptions", "/translations")):
            return httpx.Response(200, json={"text": "ok"}, headers=RESPONSE_HEADERS)
        if path.endswith("/files"):
            return httpx.Response(200, json={"id": "file", "object": "file", "bytes": 3,
                "created_at": 0, "filename": "sample", "purpose": "assistants", "status": "processed"})
        if path.endswith("/responses"):
            return httpx.Response(200, json={"id": "resp", "object": "response", "created_at": 0,
                "model": "test", "status": "completed", "output": []})
        if path.endswith("/completions") and not path.endswith("/chat/completions"):
            return httpx.Response(200, json={"id": "comp", "object": "text_completion", "created": 0,
                "model": "test", "choices": [{"index": 0, "text": "ok", "finish_reason": "stop"}]})
        if json.loads(request.content).get("stream"):
            chunk = {"id": "reply", "object": "chat.completion.chunk", "created": 0, "model": "test",
                "choices": [{"index": 0, "delta": {"content": "ok"}, "finish_reason": "stop"}],
                "usage": CHAT["usage"]}
            return httpx.Response(200, content="data: " + json.dumps(chunk) + "\n\ndata: [DONE]\n\n",
                headers={**RESPONSE_HEADERS, "content-type": "text/event-stream"})
        return httpx.Response(200, json=CHAT, headers=RESPONSE_HEADERS)

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(handler))
    cls = (AsyncGateway if alias else AsyncAgentCC) if async_mode else (Gateway if alias else AgentCC)
    client = cls(api_key="unit-key", base_url=ORIGIN, http_client=http, max_retries=0, **options)
    try:
        yield client, seen
    finally:
        await resolve(http.aclose() if async_mode else http.close())


async def call_resource(client, resource, **options):
    if resource == "chat":
        return await resolve(client.chat.completions.create(model="test", messages=[], **options))
    if resource == "stream":
        stream = await resolve(client.chat.completions.create(model="test", messages=[], stream=True, **options))
        if hasattr(stream, "__aiter__"):
            return [chunk async for chunk in stream]
        return list(stream)
    if resource == "completions":
        return await resolve(client.completions.create(model="test", prompt="hello", **options))
    if resource == "responses":
        return await resolve(client.responses.create(model="test", input="hello", **options))
    if resource == "files":
        return await resolve(client.files.create(file=("sample", b"abc"), purpose="assistants", **options))
    if resource == "speech":
        return await resolve(client.audio.speech.create(model="test", voice="alloy", input="hello", **options))
    return await resolve(getattr(client.audio, resource).create(file=b"abc", model="test", **options))
