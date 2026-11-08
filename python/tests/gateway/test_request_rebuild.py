"""A caller's send override may rebuild the initial Request before dispatch."""
import httpx
import pytest
import fi.gateway as gw


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
async def test_request_rebuilding_client_retains_response_hook_evidence(async_mode):
    responses = []

    class Body(httpx.SyncByteStream, httpx.AsyncByteStream):
        def __iter__(self):
            raise httpx.ReadTimeout("fixture body failure")
            yield b""  # pragma: no cover

        async def __aiter__(self):
            for part in self:
                yield part

    def handler(request):
        response = httpx.Response(200, headers={"x-agentcc-dispatched": "true",
            "x-agentcc-request-id": "01ARZ3NDEKTSV4RRFFQ69G5FAV"}, stream=Body())
        responses.append(response)
        return response

    def rebuild(request):
        return httpx.Request(request.method, request.url, headers=request.headers,
                             content=request.content, extensions=request.extensions)

    def hook(response):
        response.read()

    async def ahook(response):
        await response.aread()

    if async_mode:
        class Rebuilding(httpx.AsyncClient):
            async def send(self, request, **kwargs):
                return await super().send(rebuild(request), **kwargs)
    else:
        class Rebuilding(httpx.Client):
            def send(self, request, **kwargs):
                return super().send(rebuild(request), **kwargs)

    http = Rebuilding(transport=httpx.MockTransport(handler), trust_env=False,
                       event_hooks={"response": [ahook if async_mode else hook]})
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
        assert caught.value.gateway_evidence is responses[0].extensions["fi.gateway_evidence"]
    finally:
        if async_mode:
            await client.aclose()
            await http.aclose()
        else:
            client.close()
            http.close()
