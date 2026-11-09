"""Client defaults and per-call overrides on mocked chat request bodies."""

import json

import httpx
import pytest

from fi.gateway import AgentCC, AsyncGateway
from fi.gateway._constants import NOT_GIVEN


MESSAGES = [{"role": "user", "content": "hello"}]
CASES = [
    pytest.param({}, None, {}, NOT_GIVEN, id="default-omitted"),
    pytest.param({"drop_params": True}, None, {}, True, id="constructor"),
    pytest.param(
        {"drop_params": True}, None, {"drop_params": NOT_GIVEN}, True,
        id="explicit-not-given",
    ),
    pytest.param({}, {"drop_params": True}, {}, True, id="copy-enable"),
    pytest.param({"drop_params": True}, {}, {}, True, id="copy-inherit"),
    pytest.param(
        {"drop_params": True}, {"drop_params": False}, {}, NOT_GIVEN,
        id="copy-disable",
    ),
    pytest.param(
        {"drop_params": True}, None, {"drop_params": False}, False,
        id="per-call-disable",
    ),
    pytest.param({}, None, {"drop_params": True}, True, id="per-call-enable"),
    pytest.param(
        {}, {"drop_params": True}, {"drop_params": False}, False,
        id="per-call-overrides-copy",
    ),
    pytest.param(
        {"drop_params": True}, None, {"extra_body": {"drop_params": False}}, False,
        id="extra-body-overrides-default",
    ),
    pytest.param(
        {"drop_params": True}, None,
        {"drop_params": False, "extra_body": {"drop_params": True}}, True,
        id="extra-body-precedence-unchanged",
    ),
]


def _transport(seen):
    def send(request):
        body = json.loads(request.content)
        seen.append(body)
        response = {
            "id": "chatcmpl-test",
            "created": 0,
            "model": "synthetic-model",
        }
        if body.get("stream"):
            response.update(
                object="chat.completion.chunk",
                choices=[{
                    "index": 0,
                    "delta": {"content": "ok"},
                    "finish_reason": "stop",
                }],
            )
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                content=f"data: {json.dumps(response)}\n\ndata: [DONE]\n\n".encode(),
            )
        response.update(
            object="chat.completion",
            choices=[{
                "index": 0,
                "message": {"role": "assistant", "content": "ok"},
                "finish_reason": "stop",
            }],
        )
        return httpx.Response(200, json=response)

    return httpx.MockTransport(send)


def _assert_request(seen, expected, mode):
    assert len(seen) == 1
    body = seen[0]
    assert body.get("drop_params", NOT_GIVEN) is expected
    assert body["temperature"] == 0.4
    assert body["model"] == "synthetic-model"
    assert body["messages"] == MESSAGES
    assert bool(body.get("stream")) is (mode != "create")


@pytest.mark.parametrize("mode", ["create", "create-stream", "stream"])
@pytest.mark.parametrize("options,copy_options,call_options,expected", CASES)
def test_sync_drop_params_defaults(mode, options, copy_options, call_options, expected):
    seen = []
    with httpx.Client(transport=_transport(seen)) as http:
        client = AgentCC(
            api_key="synthetic-test-key", base_url="https://gateway.example.test",
            http_client=http, max_retries=0, **options,
        )
        original = client
        if copy_options is not None:
            client = client.with_options(**copy_options)
        kwargs = dict(model="synthetic-model", messages=MESSAGES, temperature=0.4, **call_options)
        if mode == "stream":
            with client.chat.completions.stream(**kwargs) as stream:
                list(stream)
        elif mode == "create-stream":
            with client.chat.completions.create(stream=True, **kwargs) as stream:
                list(stream)
        else:
            client.chat.completions.create(**kwargs)
        assert original._drop_params is options.get("drop_params", False)
    _assert_request(seen, expected, mode)


@pytest.mark.parametrize("mode", ["create", "create-stream", "stream"])
@pytest.mark.parametrize("options,copy_options,call_options,expected", CASES)
async def test_async_drop_params_defaults(mode, options, copy_options, call_options, expected):
    seen = []
    async with httpx.AsyncClient(transport=_transport(seen)) as http:
        client = AsyncGateway(
            api_key="synthetic-test-key", base_url="https://gateway.example.test",
            http_client=http, max_retries=0, **options,
        )
        original = client
        if copy_options is not None:
            client = client.with_options(**copy_options)
        kwargs = dict(model="synthetic-model", messages=MESSAGES, temperature=0.4, **call_options)
        if mode == "stream":
            async with await client.chat.completions.stream(**kwargs) as stream:
                async for _ in stream:
                    pass
        elif mode == "create-stream":
            async with await client.chat.completions.create(stream=True, **kwargs) as stream:
                async for _ in stream:
                    pass
        else:
            await client.chat.completions.create(**kwargs)
        assert original._drop_params is options.get("drop_params", False)
    _assert_request(seen, expected, mode)
