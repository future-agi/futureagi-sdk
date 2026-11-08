"""Released options and resources retain effects, not just names or signatures."""

import inspect
import json
from contextlib import AsyncExitStack, asynccontextmanager

import httpx
import pytest

from fi.gateway import AgentCC, AgentCCError, AsyncAgentCC
from fi.gateway.callbacks import CallbackHandler

ORIGIN = "https://gateway.example.test"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def clean_platform_keys(monkeypatch):
    for name in ("FI_API_KEY", "FI_SECRET_KEY"):
        monkeypatch.delenv(name, raising=False)


async def _result(value):
    return await value if inspect.isawaitable(value) else value


@asynccontextmanager
async def _client(async_mode, handler, **options):
    async with AsyncExitStack() as stack:
        if async_mode:
            http = await stack.enter_async_context(httpx.AsyncClient(transport=httpx.MockTransport(handler)))
            cls = AsyncAgentCC
        else:
            http = stack.enter_context(httpx.Client(transport=httpx.MockTransport(handler)))
            cls = AgentCC
        kwargs = dict(api_key="unit-key", base_url=ORIGIN, http_client=http, max_retries=0, **options)
        if options:
            with pytest.warns(DeprecationWarning, match="compatibility options"):
                client = cls(**kwargs)
        else:
            client = cls(**kwargs)
        if async_mode:
            await stack.enter_async_context(client)
        else:
            stack.enter_context(client)
        yield client


@pytest.mark.anyio
@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
async def test_deprecated_resources_send_the_released_routes_and_payloads(async_mode):
    sent = []

    def handler(request):
        sent.append(request)
        if request.url.path == "/v1/batches":
            return httpx.Response(200, json={"batch_id": "b", "status": "completed", "total": 1})
        return httpx.Response(200, json={"id": "m", "model": "moderation-unit", "results": [{"flagged": False}]})

    async with _client(async_mode, handler) as client:
        with pytest.warns(DeprecationWarning, match="batches"):
            batches = getattr(client, "batches", None)
        assert callable(getattr(batches, "create", None))
        requests = [{"model": "unit-model", "messages": []}]
        batch = await _result(batches.create(requests=requests, max_concurrency=2))
        assert batch.batch_id == "b" and batch.status == "completed" and batch.total == 1
        with pytest.warns(DeprecationWarning, match="moderations"):
            moderations = getattr(client, "moderations", None)
        assert callable(getattr(moderations, "create", None))
        moderation = await _result(moderations.create(input="unit-text", model="moderation-unit"))
        assert moderation.id == "m" and moderation.results[0].flagged is False
    assert [(r.method, r.url.path) for r in sent] == [
        ("POST", "/v1/batches"), ("POST", "/v1/moderations"),
    ]
    assert json.loads(sent[0].content) == {"requests": requests, "max_concurrency": 2}
    assert json.loads(sent[1].content) == {"input": "unit-text", "model": "moderation-unit"}


@pytest.mark.anyio
@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
async def test_deprecated_options_redact_modify_and_block_before_send(async_mode):
    sent, callback_requests, rule_calls = [], [], []
    permit = True

    class Recorder(CallbackHandler):
        def on_request_start(self, request):
            callback_requests.append(request)

    def rule(model, messages, kwargs):
        rule_calls.append((model, messages))
        return permit

    def handler(request):
        sent.append(request)
        return httpx.Response(200, json={
            "id": "c", "object": "chat.completion", "created": 1,
            "model": "gemini-unit", "choices": [],
        })

    messages = [{"role": "user", "content": "private unit text"}]
    async with _client(async_mode, handler, redact_messages=True, modify_params=True,
                       pre_call_rules=[rule], callbacks=[Recorder()]) as client:
        result = await _result(client.chat.completions.create(
            model="gemini-unit", messages=messages, max_tokens=7, n=2,
        ))
        assert result.id == "c"
        assert len(sent) == len(callback_requests) == len(rule_calls) == 1
        wire = json.loads(sent[0].content)
        assert wire["messages"] == messages
        assert wire["max_output_tokens"] == 7
        assert "max_tokens" not in wire and "n" not in wire
        assert callback_requests[0].body["messages"][0]["content"] == "[REDACTED]"
        assert messages[0]["content"] == "private unit text"
        permit = False
        with pytest.raises(AgentCCError, match="blocked by pre-call rule"):
            await _result(client.chat.completions.create(model="gemini-unit", messages=messages))
        assert len(sent) == len(callback_requests) == 1
        assert rule_calls == [("gemini-unit", messages), ("gemini-unit", messages)]
