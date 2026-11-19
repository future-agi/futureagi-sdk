"""Which calls inside ``client.session()`` carry the session headers.

``AgentCC.session()`` and ``AsyncAgentCC.session()`` say: chat completions (``create``
and ``stream``), completions, ``responses.create``, audio and ``files.create`` send the
session's id, name, path and metadata; embeddings, images, rerank, models and the other
``files`` and ``responses`` calls send the client's headers only (as in agentcc 1.x).
These tests keep that sentence true for the calls a mock transport can answer.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from ._published_helpers import wire_snapshot
from fi.gateway import AgentCC

COMPLETION = {
    "id": "c",
    "object": "chat.completion",
    "created": 1,
    "model": "m",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "hi"},
            "finish_reason": "stop",
        }
    ],
}
TEXT_COMPLETION = {
    "id": "t",
    "object": "text_completion",
    "created": 1,
    "model": "m",
    "choices": [{"index": 0, "text": "hi", "finish_reason": "stop"}],
}
RESPONSE = {
    "id": "r",
    "object": "response",
    "created_at": 1,
    "model": "m",
    "output": [],
    "status": "completed",
}
LIST = {"object": "list", "data": []}
EMBEDDINGS = {
    "object": "list",
    "model": "e",
    "data": [],
    "usage": {"prompt_tokens": 1, "completion_tokens": 0, "total_tokens": 1},
}
SSE = (
    'data: {"id":"c","object":"chat.completion.chunk","created":1,"model":"m",'
    '"choices":[{"index":0,"delta":{"content":"a"},"finish_reason":"stop"}]}\n\n'
    "data: [DONE]\n\n"
)


def _reply(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/v1/chat/completions":
        if json.loads(request.content).get("stream"):
            return httpx.Response(
                200, headers={"content-type": "text/event-stream"}, content=SSE
            )
        return httpx.Response(200, json=COMPLETION)
    if path == "/v1/completions":
        return httpx.Response(200, json=TEXT_COMPLETION)
    if path == "/v1/responses":
        return httpx.Response(200, json=RESPONSE)
    if path == "/v1/embeddings":
        return httpx.Response(200, json=EMBEDDINGS)
    return httpx.Response(200, json=LIST)


def _client(seen: list[httpx.Request], **kwargs: Any) -> AgentCC:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(wire_snapshot(request))
        return _reply(request)

    return AgentCC(
        api_key="gw-key",
        base_url="http://127.0.0.1:8090",
        metadata={"tenant": "A"},
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        **kwargs,
    )


def _stream(c: AgentCC) -> None:
    with c.chat.completions.stream(model="m", messages=[]) as stream:
        for _ in stream:
            pass


MSG = [{"role": "user", "content": "hi"}]
SESSION: dict[str, Any] = {
    "session_id": "s-1",
    "name": "checkout",
    "path": "/checkout",
    "metadata": {"cart": "c1"},
}
CARRY: dict[str, Callable[[AgentCC], Any]] = {
    "chat.completions.create": lambda c: c.chat.completions.create(
        model="m", messages=MSG
    ),
    "chat.completions.stream": _stream,
    "completions.create": lambda c: c.completions.create(model="m", prompt="hi"),
    "responses.create": lambda c: c.responses.create(model="m", input="hi"),
}
CLIENT_ONLY: dict[str, Callable[[AgentCC], Any]] = {
    "embeddings.create": lambda c: c.embeddings.create(model="e", input="x"),
    "models.list": lambda c: c.models.list(),
    "files.list": lambda c: c.files.list(),
}


@pytest.mark.parametrize("mode", ["replace", "merge"])
@pytest.mark.parametrize("call", sorted(CARRY))
def test_model_requests_carry_the_session(call: str, mode: str) -> None:
    seen: list[httpx.Request] = []
    client = _client(seen, metadata_mode=mode)
    with client.session(**SESSION):
        CARRY[call](client)
    headers = seen[-1].headers
    assert headers["x-agentcc-session-id"] == "s-1"
    assert headers["x-agentcc-session-name"] == "checkout"
    assert headers["x-agentcc-session-path"] == "/checkout"
    if mode == "merge":
        assert json.loads(headers["x-agentcc-metadata"]) == {"tenant": "A", "cart": "c1"}
        assert "x-agentcc-metadata-cart" not in headers
    else:
        # The published default: per-key session metadata beside the client's header.
        assert json.loads(headers["x-agentcc-metadata"]) == {"tenant": "A"}
        assert headers["x-agentcc-metadata-cart"] == "c1"


@pytest.mark.parametrize("call", sorted(CLIENT_ONLY))
def test_the_other_calls_send_the_client_headers_only(call: str) -> None:
    seen: list[httpx.Request] = []
    client = _client(seen)
    with client.session(**SESSION):
        CLIENT_ONLY[call](client)
    headers = seen[-1].headers
    assert not [h for h in headers if h.startswith("x-agentcc-session-")]
    assert json.loads(headers["x-agentcc-metadata"]) == {"tenant": "A"}
    assert headers["authorization"] == "Bearer gw-key"
