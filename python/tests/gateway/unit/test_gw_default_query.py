"""``default_query`` and ``with_options(extra_query=)`` are sent as URL query parameters.

agentcc 1.x accepted both, stored them and never sent them. Now every request a client
sends carries its ``default_query``; a ``with_options(extra_query=...)`` copy sends the
parent's keys plus its own, its own winning for a key both set; a key the request path
already carries (``files.list(purpose=...)``) keeps the path's value. No resource
method takes a query argument of its own, so a ``with_options`` copy is the per-request
layer. A client without ``default_query`` sends exactly the URL it sent before.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC

GW = "http://127.0.0.1:8090"
MSG = [{"role": "user", "content": "hi"}]
CHAT = {
    "id": "c1",
    "object": "chat.completion",
    "created": 1,
    "model": "m",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}}],
}
SSE = (
    'data: {"id":"c","object":"chat.completion.chunk","created":1,"model":"m",'
    '"choices":[{"index":0,"delta":{"content":"hi"},"finish_reason":"stop"}]}\n\n'
    "data: [DONE]\n\n"
)
FILE = {
    "id": "file-1",
    "object": "file",
    "bytes": 1,
    "created_at": 1,
    "filename": "a.jsonl",
    "purpose": "batch",
}
RESPONSE = {"id": "resp_1", "object": "response", "status": "completed"}
EMBEDDING = {
    "object": "list",
    "model": "e",
    "data": [{"object": "embedding", "index": 0, "embedding": [0.1]}],
}


def _reply(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/v1/chat/completions":
        if b'"stream":true' in request.content:
            return httpx.Response(
                200, headers={"content-type": "text/event-stream"}, content=SSE.encode()
            )
        return httpx.Response(200, json=CHAT)
    if path == "/v1/embeddings":
        return httpx.Response(200, json=EMBEDDING)
    if path == "/v1/files" and request.method == "POST":
        return httpx.Response(200, json=FILE)
    if path == "/v1/files":
        return httpx.Response(200, json={"object": "list", "data": [FILE]})
    if path.endswith("/content"):
        return httpx.Response(200, content=b"raw")
    if path.startswith("/v1/responses"):
        return httpx.Response(200, json=RESPONSE)
    if path == "/v1/models":
        return httpx.Response(200, json={"object": "list", "data": []})
    return httpx.Response(404, json={"error": {"message": "no route"}})


def _sync(seen: list[httpx.Request], **opts: Any) -> AgentCC:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _reply(request)

    return AgentCC(
        api_key="k",
        base_url=GW,
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        **opts,
    )


def _async(seen: list[httpx.Request], **opts: Any) -> AsyncAgentCC:
    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _reply(request)

    return AsyncAgentCC(
        api_key="k",
        base_url=GW,
        max_retries=0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        **opts,
    )


def _query(request: httpx.Request) -> list[tuple[str, str]]:
    return list(request.url.params.multi_items())


def _every_resource(client: AgentCC) -> None:
    client.chat.completions.create(model="m", messages=MSG)
    list(client.chat.completions.create(model="m", messages=MSG, stream=True))
    with client.chat.completions.stream(model="m", messages=MSG) as s:
        s.get_final_completion()
    client.embeddings.create(model="e", input="x")
    client.files.create(file=("a.jsonl", b"{}"), purpose="batch")
    client.files.content("file-1")
    client.responses.retrieve("resp_1")
    client.responses.delete("resp_1")
    client.models.list()


def test_default_query_reaches_every_request() -> None:
    seen: list[httpx.Request] = []
    _every_resource(_sync(seen, default_query={"tenant": "t1", "region": "eu"}))
    assert len(seen) == 9
    for request in seen:
        assert _query(request) == [("tenant", "t1"), ("region", "eu")], request.url


def test_without_default_query_the_url_is_unchanged() -> None:
    seen: list[httpx.Request] = []
    _every_resource(_sync(seen))
    assert [str(r.url) for r in seen] == [
        f"{GW}/v1/chat/completions",
        f"{GW}/v1/chat/completions",
        f"{GW}/v1/chat/completions",
        f"{GW}/v1/embeddings",
        f"{GW}/v1/files",
        f"{GW}/v1/files/file-1/content",
        f"{GW}/v1/responses/resp_1",
        f"{GW}/v1/responses/resp_1",
        f"{GW}/v1/models",
    ]
    assert all(r.url.query == b"" for r in seen)


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_extra_query_on_a_copy_adds_keys_and_wins_on_a_shared_key() -> None:
    seen: list[httpx.Request] = []
    parent = _sync(seen, default_query={"tenant": "t1", "region": "eu"})
    copy = parent.with_options(extra_query={"region": "us", "trace": "x"})
    copy.chat.completions.create(model="m", messages=MSG)
    parent.chat.completions.create(model="m", messages=MSG)
    assert _query(seen[0]) == [("tenant", "t1"), ("region", "us"), ("trace", "x")]
    assert _query(seen[1]) == [("tenant", "t1"), ("region", "eu")]


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_extra_query_without_a_default_query() -> None:
    seen: list[httpx.Request] = []
    _sync(seen).with_options(extra_query={"q": "1"}).chat.completions.create(
        model="m", messages=MSG
    )
    assert _query(seen[0]) == [("q", "1")]


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_a_copy_made_after_the_parent_has_sent_sends_its_own_query() -> None:
    seen: list[httpx.Request] = []
    parent = _sync(seen, default_query={"tenant": "t1"})
    parent.chat.completions.create(model="m", messages=MSG)
    a = parent.with_options(extra_query={"tenant": "A"})
    b = a.with_options(extra_query={"tenant": "B"})
    a.chat.completions.create(model="m", messages=MSG)
    b.chat.completions.create(model="m", messages=MSG)
    a.chat.completions.create(model="m", messages=MSG)
    assert [_query(r) for r in seen] == [
        [("tenant", "t1")],
        [("tenant", "A")],
        [("tenant", "B")],
        [("tenant", "A")],
    ]


def test_a_key_the_path_carries_keeps_the_path_s_value() -> None:
    seen: list[httpx.Request] = []
    client = _sync(seen, default_query={"purpose": "fine-tune", "tenant": "t1"})
    client.files.list(purpose="batch")
    assert _query(seen[0]) == [("purpose", "batch"), ("tenant", "t1")]


def test_values_are_sent_as_text_and_encoded() -> None:
    seen: list[httpx.Request] = []
    client = _sync(seen, default_query={"name": "a b&c", "n": 2})  # type: ignore[dict-item]
    client.chat.completions.create(model="m", messages=MSG)
    assert _query(seen[0]) == [("name", "a b&c"), ("n", "2")]
    assert seen[0].url.query == b"name=a+b%26c&n=2"


def test_the_transport_url_join_keeps_an_absolute_url_and_adds_the_query() -> None:
    base = _sync([], default_query={"tenant": "t1"})._get_base_client()
    assert base._build_url("/v1/models") == f"{GW}/v1/models?tenant=t1"
    assert base._build_url(f"{GW}/v1/x?a=1") == f"{GW}/v1/x?tenant=t1&a=1"
    plain = _sync([])._get_base_client()
    assert plain._build_url(f"{GW}/v1/x?a=1") == f"{GW}/v1/x?a=1"
    from fi.gateway import AgentCCError

    for client in (base, plain):
        with pytest.raises(AgentCCError, match="explicitly configured origin"):
            client._build_url("https://other.example.test/v1/x?a=1")


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
@pytest.mark.parametrize("stream", [False, True])
async def test_the_async_client_sends_it_too(stream: bool) -> None:
    seen: list[httpx.Request] = []
    client = _async(seen, default_query={"tenant": "t1"})
    copy = client.with_options(extra_query={"q": "1"})
    if stream:
        async for _ in await copy.chat.completions.create(
            model="m", messages=MSG, stream=True
        ):
            pass
    else:
        await copy.chat.completions.create(model="m", messages=MSG)
    await client.files.create(file=("a.jsonl", b"{}"), purpose="batch")
    await client.files.content("file-1")
    await client.responses.retrieve("resp_1")
    assert _query(seen[0]) == [("tenant", "t1"), ("q", "1")]
    assert [_query(r) for r in seen[1:]] == [[("tenant", "t1")]] * 3
