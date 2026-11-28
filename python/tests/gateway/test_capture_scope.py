"""Header observation does not alter caller hooks, nested sends or cancellation."""
import asyncio

import httpx
import pytest

import fi.gateway as gw
from .test_terminal_outcomes import assert_safe

UID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"


class BrokenBody(httpx.SyncByteStream, httpx.AsyncByteStream):
    def __iter__(self):
        raise httpx.ReadTimeout("fixture body failure")
        yield b""  # pragma: no cover

    async def __aiter__(self):
        for chunk in self:
            yield chunk


def assert_methods_restored(client, methods):
    for name, method in methods.items():
        assert getattr(client, name) == method
        assert name not in vars(client)


def original_methods(client):
    return {name: getattr(client, name) for name in ("_send_handling_auth", "_send_single_request")}


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("nested_sdk", [False, True], ids=["httpx", "sdk"])
async def test_nested_send_from_response_hook_cannot_replace_outer_evidence(async_mode, nested_sdk):
    requests = []
    hook_order = []
    results = []

    def handler(request):
        requests.append(request)
        outer = len(requests) == 1
        headers = {"x-agentcc-request-id": UID,
                   "x-agentcc-dispatched": "true" if outer else "false",
                   "x-agentcc-client-request-id": "outer" if outer else "nested"}
        if outer:
            return httpx.Response(200, headers=headers, stream=BrokenBody())
        return httpx.Response(200, headers=headers,
                              json={"id": "fixture", "object": "chat.completion", "created": 0,
                                    "model": "fixture", "choices": []})

    def hook(response):
        hook_order.append(response.headers["x-agentcc-client-request-id"])
        if len(requests) == 1:
            results.append(client.chat.completions.create(model="fixture", messages=[]) if nested_sdk
                           else http.get("https://gateway.test/nested"))
            response.read()

    async def ahook(response):
        hook_order.append(response.headers["x-agentcc-client-request-id"])
        if len(requests) == 1:
            results.append(await client.chat.completions.create(model="fixture", messages=[]) if nested_sdk
                           else await http.get("https://gateway.test/nested"))
            await response.aread()

    http = (httpx.AsyncClient if async_mode else httpx.Client)(
        transport=httpx.MockTransport(handler), trust_env=False,
        event_hooks={"response": [ahook if async_mode else hook]},
    )
    methods = original_methods(http)
    hooks = http.event_hooks
    hook_lists = dict(hooks)
    client = (gw.AsyncAgentCC if async_mode else gw.AgentCC)(
        api_key="synthetic-credential-only", base_url="https://gateway.test", http_client=http,
    )
    try:
        with pytest.raises(gw.APITimeoutError) as caught:
            if async_mode:
                await client.chat.completions.create(model="fixture", messages=[])
            else:
                client.chat.completions.create(model="fixture", messages=[])
        assert caught.value.dispatched is True
        assert caught.value.client_request_id == "outer"
        assert len(requests) == 2 and len(results) == 1
        assert hook_order == ["outer", "nested"]
        assert http.event_hooks is hooks
        assert all(hooks[name] is value for name, value in hook_lists.items())
        assert_methods_restored(http, methods)
        assert_safe(caught.value)
    finally:
        if async_mode:
            await client.aclose()
            await http.aclose()
        else:
            client.close()
            http.close()


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("status", [200, 246])
async def test_follow_up_response_owns_its_body_failure_evidence(async_mode, status):
    requests = []
    responses = []

    class ExchangeAuth(httpx.Auth):
        def auth_flow(self, request):
            yield request
            yield httpx.Request(request.method, request.url, content=request.content,
                                headers=request.headers)

    def handler(request):
        requests.append(request)
        first = len(requests) == 1
        headers = {"x-agentcc-request-id": UID,
                   "x-agentcc-dispatched": "false" if first else "true",
                   "x-agentcc-client-request-id": "challenge" if first else "follow-up"}
        response = (httpx.Response(401, headers=headers, json={"error": "fixture challenge"})
                    if first else httpx.Response(status, headers=headers, stream=BrokenBody()))
        responses.append(response)
        return response

    http = (httpx.AsyncClient if async_mode else httpx.Client)(
        transport=httpx.MockTransport(handler), auth=ExchangeAuth(), trust_env=False,
    )
    methods = original_methods(http)
    client = (gw.AsyncAgentCC if async_mode else gw.AgentCC)(
        api_key="synthetic-credential-only", base_url="https://gateway.test", http_client=http,
    )
    try:
        with pytest.raises(gw.APITimeoutError) as caught:
            if async_mode:
                await client.chat.completions.create(model="fixture", messages=[])
            else:
                client.chat.completions.create(model="fixture", messages=[])
        assert len(requests) == 2
        assert caught.value.dispatched is True
        assert caught.value.client_request_id == "follow-up"
        assert caught.value.gateway_evidence is responses[-1].extensions["fi.gateway_evidence"]
        assert all(response.is_closed for response in responses)
        assert_methods_restored(http, methods)
        assert_safe(caught.value)
    finally:
        if async_mode:
            await client.aclose()
            await http.aclose()
        else:
            client.close()
            http.close()


async def test_cancelled_send_restores_caller_methods():
    entered = asyncio.Event()

    async def handler(request):
        entered.set()
        await asyncio.Event().wait()

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False) as http:
        methods = original_methods(http)
        async with gw.AsyncAgentCC(api_key="synthetic-credential-only", base_url="https://gateway.test",
                                   http_client=http) as client:
            task = asyncio.create_task(client.chat.completions.create(model="fixture", messages=[]))
            await asyncio.wait_for(entered.wait(), timeout=5)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert_methods_restored(http, methods)
            assert not http.is_closed
