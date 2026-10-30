"""Regression tests for the findings of the security / correctness review of PR #35 (nik13, 2026-10-30).

Each test names the finding it covers. The requests go through respx, so nothing reaches a network.
"""

from __future__ import annotations

import asyncio
import base64
import json
import struct

import httpx
import pytest
import respx
from pydantic import BaseModel

from fi.gateway import AsyncGateway, Gateway
from fi.gateway._exceptions import NotFoundError
from fi.gateway._structured import strict_schema, to_response_format
from fi.gateway.callbacks.base import CallbackHandler
from fi.gateway.testing import RequestRecorder, create_mock_client
from fi.gateway.types.completion import Completion
from fi.gateway.types.embedding import Embedding, decode_base64_embedding
from fi.gateway.types.responses import ResponseStreamEvent

BASE = "http://gw.test"
MSG = [{"role": "user", "content": "the secret question"}]
COMPLETION = {
    "id": "chatcmpl-1",
    "object": "chat.completion",
    "created": 1,
    "model": "gpt-4o-mini",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
}


def _sse(*events: dict, done: bool = True) -> bytes:
    lines = [f"data: {json.dumps(e)}\n\n" for e in events]
    if done:
        lines.append("data: [DONE]\n\n")
    return "".join(lines).encode()


def _chunk(text: str, finish: str | None = None) -> dict:
    return {"id": "c1", "object": "chat.completion.chunk", "created": 1, "model": "m", "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": finish}]}


# ---------------------------------------------------------------- [P1] redact_messages reaches the callbacks


class _Seen(CallbackHandler):
    def __init__(self) -> None:
        self.started: list = []
        self.ended: list = []

    def on_request_start(self, request) -> None:
        self.started.append(request.body)

    def on_request_end(self, request, response) -> None:
        self.ended.append(request.body)


@respx.mock
def test_redact_messages_hides_content_from_callbacks_but_not_from_the_provider(tmp_path):
    route = respx.post(f"{BASE}/v1/chat/completions").mock(return_value=httpx.Response(200, json=COMPLETION))
    seen, recorder = _Seen(), RequestRecorder(str(tmp_path / "rec.json"))
    gw = Gateway(api_key="k", base_url=BASE, redact_messages=True, callbacks=[seen, recorder])
    gw.chat.completions.create(model="m", messages=MSG)

    sent = json.loads(route.calls.last.request.content)
    assert sent["messages"] == MSG  # the provider gets the real messages
    for body in seen.started + seen.ended + [r["request"]["body"] for r in recorder.recordings]:
        assert body["messages"] == [{"role": "user", "content": "[REDACTED]"}]  # every callback gets the redacted copy
        assert body["model"] == "m"

    plain = _Seen()
    Gateway(api_key="k", base_url=BASE, callbacks=[plain]).chat.completions.create(model="m", messages=MSG)
    assert plain.ended[0]["messages"] == MSG  # off by default, as before


# ---------------------------------------------------------------- [P1] sessions are local to the task / thread


@respx.mock
def test_concurrent_async_sessions_do_not_leak_into_each_other():
    route = respx.post(f"{BASE}/v1/chat/completions").mock(return_value=httpx.Response(200, json=COMPLETION, headers={"x-agentcc-cost": "0.5"}))

    async def scenario():
        gw = AsyncGateway(api_key="k", base_url=BASE)
        started, release = asyncio.Event(), asyncio.Event()
        sessions = {}

        async def worker(name: str, first: bool):
            async with gw.session(name=name) as sess:
                sessions[name] = sess
                if first:
                    started.set()
                    await release.wait()  # B enters its session while A is inside its own
                else:
                    release.set()
                await gw.chat.completions.create(model="m", messages=MSG)
                return sess.request_count

        a, b = await asyncio.gather(worker("A", True), worker("B", False))
        assert (a, b) == (1, 1)  # each request was credited to its own session
        assert gw._active_session is None  # nothing left behind
        sent = [c.request.headers["x-agentcc-session-name"] for c in route.calls]
        assert sorted(sent) == ["A", "B"]  # each request carried the session of its task

    asyncio.run(scenario())


@respx.mock
def test_nested_sessions_restore_the_outer_one():
    respx.post(f"{BASE}/v1/chat/completions").mock(return_value=httpx.Response(200, json=COMPLETION))
    gw = Gateway(api_key="k", base_url=BASE)
    with gw.session(name="outer") as outer:
        with gw.session(name="inner") as inner:
            assert gw._active_session is inner
        assert gw._active_session is outer  # not None
        gw.chat.completions.create(model="m", messages=MSG)
        assert outer.request_count == 1 and inner.request_count == 0
    assert gw._active_session is None


# ---------------------------------------------------------------- [P1] strict structured output needs a converted schema


class Inner(BaseModel):
    note: str


class Event(BaseModel):
    name: str
    date: str
    place: str | None = None
    attendees: int = 0
    inner: Inner | None = None


def test_to_response_format_emits_a_schema_strict_mode_accepts():
    fmt = to_response_format(Event)
    schema = fmt["json_schema"]["schema"]
    assert fmt["json_schema"]["strict"] is True
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["name", "date", "place", "attendees", "inner"]  # every property
    assert schema["properties"]["attendees"]["type"] == ["integer", "null"]  # a defaulted field becomes nullable
    assert "default" not in schema["properties"]["attendees"]
    assert {"type": "null"} in schema["properties"]["inner"]["anyOf"]
    inner = schema["$defs"]["Inner"]
    assert inner["additionalProperties"] is False and inner["required"] == ["note"]  # nested models too
    assert schema["properties"]["name"] == {"title": "Name", "type": "string"}  # a required field is untouched


def test_strict_schema_leaves_a_strict_schema_alone():
    strict = {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"], "additionalProperties": False}
    assert strict_schema(strict) == strict


# ---------------------------------------------------------------- [P1] Responses and legacy completions decode their own events


@respx.mock
def test_responses_stream_yields_response_events_with_text_deltas():
    events = [
        {"type": "response.created", "sequence_number": 0, "response": {"id": "resp_1", "status": "in_progress"}},
        {"type": "response.output_text.delta", "sequence_number": 1, "item_id": "msg_1", "output_index": 0, "content_index": 0, "delta": "Hel"},
        {"type": "response.output_text.delta", "sequence_number": 2, "item_id": "msg_1", "output_index": 0, "content_index": 0, "delta": "lo"},
        {"type": "response.completed", "sequence_number": 3, "response": {"id": "resp_1", "status": "completed", "output": []}},
    ]
    respx.post(f"{BASE}/v1/responses").mock(return_value=httpx.Response(200, content=_sse(*events), headers={"content-type": "text/event-stream"}))
    gw = Gateway(api_key="k", base_url=BASE)
    got = list(gw.responses.create(model="m", input="hi", stream=True))
    assert all(isinstance(e, ResponseStreamEvent) for e in got)
    assert [e.type for e in got] == [e["type"] for e in events]
    assert "".join(e.delta for e in got if e.type == "response.output_text.delta") == "Hello"
    assert got[0].response.id == "resp_1" and got[-1].response.status == "completed"


@respx.mock
def test_legacy_completions_stream_yields_text_completions():
    events = [{"id": "cmpl-1", "object": "text_completion", "created": 1, "model": "m", "choices": [{"text": "Hel", "index": 0}]}, {"id": "cmpl-1", "object": "text_completion", "created": 1, "model": "m", "choices": [{"text": "lo", "index": 0, "finish_reason": "stop"}]}]
    respx.post(f"{BASE}/v1/completions").mock(return_value=httpx.Response(200, content=_sse(*events), headers={"content-type": "text/event-stream"}))
    gw = Gateway(api_key="k", base_url=BASE)
    got = list(gw.completions.create(model="m", prompt="hi", stream=True))
    assert all(isinstance(c, Completion) for c in got)
    assert "".join(c.choices[0].text for c in got) == "Hello"


# ---------------------------------------------------------------- [P1] a finished stream closes its response


@respx.mock
def test_a_fully_consumed_stream_closes_the_response():
    respx.post(f"{BASE}/v1/chat/completions").mock(return_value=httpx.Response(200, content=_sse(_chunk("a"), _chunk("b", "stop")), headers={"content-type": "text/event-stream"}))
    gw = Gateway(api_key="k", base_url=BASE)
    stream = gw.chat.completions.create(model="m", messages=MSG, stream=True)
    assert [c.choices[0].delta.content for c in stream] == ["a", "b"]
    assert stream.response.is_closed  # no explicit close() needed

    broken = respx.post(f"{BASE}/v1/chat/completions").mock(return_value=httpx.Response(200, content=b"data: not json\n\n", headers={"content-type": "text/event-stream"}))
    stream = gw.chat.completions.create(model="m", messages=MSG, stream=True)
    with pytest.raises(Exception, match="Invalid JSON"):
        list(stream)
    assert stream.response.is_closed and broken.called


@respx.mock
def test_a_fully_consumed_async_stream_closes_the_response():
    respx.post(f"{BASE}/v1/chat/completions").mock(return_value=httpx.Response(200, content=_sse(_chunk("a"), _chunk("b", "stop")), headers={"content-type": "text/event-stream"}))

    async def scenario():
        gw = AsyncGateway(api_key="k", base_url=BASE)
        stream = await gw.chat.completions.create(model="m", messages=MSG, stream=True)
        assert [c.choices[0].delta.content async for c in stream] == ["a", "b"]
        assert stream.response.is_closed

    asyncio.run(scenario())


# ---------------------------------------------------------------- [P2] resuming an async stream reuses its iterator


@respx.mock
def test_async_stream_manager_resumes_after_an_early_break():
    respx.post(f"{BASE}/v1/chat/completions").mock(return_value=httpx.Response(200, content=_sse(_chunk("He"), _chunk("l"), _chunk("lo", "stop")), headers={"content-type": "text/event-stream"}))

    async def scenario():
        gw = AsyncGateway(api_key="k", base_url=BASE)
        async with await gw.chat.completions.stream(model="m", messages=MSG) as manager:
            async for event in manager:
                if event.type == "content":
                    break  # one event, then hand over to the drain
            completion = await manager.get_final_completion()
        assert completion.choices[0].message.content == "Hello"

    asyncio.run(scenario())


# ---------------------------------------------------------------- [P1] create_mock_client never touches the network


def test_create_mock_client_serves_the_mapping_and_fails_closed():
    client = create_mock_client(responses={"/v1/chat/completions": COMPLETION})
    assert client.chat.completions.create(model="m", messages=MSG).choices[0].message.content == "hi"
    with pytest.raises(NotFoundError, match="no response for GET /v1/models"):
        client.models.list()
    client._mock_responses["/v1/models"] = {"object": "list", "data": [{"id": "m", "object": "model", "created": 1, "owned_by": "x"}]}  # the mapping stays live
    assert client.models.list().data[0].id == "m"


# ---------------------------------------------------------------- [P2] base64 embeddings parse


def test_base64_embeddings_parse_and_decode():
    floats = [0.5, -1.0, 2.0]
    encoded = base64.b64encode(struct.pack("<3f", *floats)).decode()
    emb = Embedding.model_validate({"object": "embedding", "embedding": encoded, "index": 0})
    assert emb.embedding == encoded
    assert decode_base64_embedding(emb.embedding) == floats
    assert decode_base64_embedding([1.0, 2.0]) == [1.0, 2.0]


# ---------------------------------------------------------------- [P2] a client copied before first use closes its own pool


@respx.mock
def test_a_copy_made_before_first_use_closes_its_own_pool():
    respx.post(f"{BASE}/v1/chat/completions").mock(return_value=httpx.Response(200, json=COMPLETION))
    parent = Gateway(api_key="k", base_url=BASE)
    copy = parent.with_options(timeout=5)
    copy.chat.completions.create(model="m", messages=MSG)
    pool = copy._base_client._client
    assert pool is not None and copy._base_client._owns_client
    copy.close()
    assert pool.is_closed and copy._base_client._client is None

    parent.chat.completions.create(model="m", messages=MSG)
    shared = parent.with_options(timeout=5)  # made after first use: shares the parent's pool
    shared.chat.completions.create(model="m", messages=MSG)
    shared.close()
    assert not parent._base_client._client.is_closed  # a shared pool is left to its owner
    parent.close()
    assert parent._base_client._client is None
