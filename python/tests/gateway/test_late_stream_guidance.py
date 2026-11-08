"""Late transport failures keep their cause, guidance, and one-send boundary."""
from types import SimpleNamespace

import httpx
import pytest

from fi.gateway import AsyncGateway, Gateway, StreamError


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("resource", ["chat", "completions", "responses"])
@pytest.mark.parametrize("callback_mode", ["published", "snapshot"])
@pytest.mark.parametrize("expanded", [False, True])
async def test_late_failure_guidance_in_every_stream_mode(async_mode, resource, callback_mode, expanded):
    secret = "synthetic-stream-private-value"
    attempts, errors = [], []
    cause = httpx.ReadTimeout(secret)
    payload = {
        "chat": b'data: {"id":"fixture","object":"chat.completion.chunk","created":0,"model":"fixture","choices":[]}\n\n',
        "completions": b'data: {"id":"fixture","object":"text_completion","created":0,"model":"fixture","choices":[]}\n\n',
        "responses": b'event: response.output_text.delta\ndata: {"type":"response.output_text.delta","delta":"ok","item_id":"fixture","output_index":0,"content_index":0}\n\n',
    }[resource]

    class Body(httpx.SyncByteStream, httpx.AsyncByteStream):
        def __iter__(self):
            yield payload
            raise cause

        async def __aiter__(self):
            for part in self:
                yield part

    def handler(request):
        attempts.append(request)
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=Body())

    options = dict(api_key=secret, base_url="https://gateway.test", max_retries=4,
                   callback_mode=callback_mode, expanded_callback_events=expanded,
                   callbacks=[SimpleNamespace(on_error=lambda request, error: errors.append(error))])
    args = {"model": "fixture", "stream": True}
    args.update({"messages": []} if resource == "chat" else {"prompt": "fixture"} if resource == "completions" else {"input": "fixture"})
    if async_mode:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            async with AsyncGateway(http_client=http, **options) as client:
                endpoint = client.chat.completions if resource == "chat" else getattr(client, resource)
                stream = await endpoint.create(**args)
                await stream.__anext__()
                with pytest.raises(StreamError) as caught:
                    await stream.__anext__()
    else:
        with httpx.Client(transport=httpx.MockTransport(handler)) as http:
            with Gateway(http_client=http, **options) as client:
                endpoint = client.chat.completions if resource == "chat" else getattr(client, resource)
                stream = endpoint.create(**args)
                next(stream)
                with pytest.raises(StreamError) as caught:
                    next(stream)
    assert len(attempts) == 1
    assert caught.value.__cause__ is cause
    assert "check whether" in str(caught.value)
    assert secret not in str(caught.value) + repr(cause)
    expected_events = not async_mode or resource == "chat" or expanded
    assert errors == ([caught.value] if expected_events else [])
