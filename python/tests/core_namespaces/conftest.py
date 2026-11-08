import inspect
from types import SimpleNamespace

import httpx
import pytest_asyncio

from fi import AsyncFutureAGIClient, FutureAGIClient
from fi.knowledge_bases import AsyncKnowledgeBasesClient, KnowledgeBasesClient
from fi.prompts import AsyncPromptsClient, PromptsClient
from fi.scores import AsyncScoresClient, ScoresClient


async def invoke(method, *args, **kwargs):
    result = method(*args, **kwargs)
    return await result if inspect.isawaitable(result) else result


@pytest_asyncio.fixture(params=[False, True], ids=["sync", "async"])
async def resources(request):
    """Both root clients on a loopback mock: queued ``replies``, or a stateful ``server`` callable."""
    state = SimpleNamespace(requests=[], replies=[], server=None, call=invoke)

    def handle(req):
        assert req.url.host == "127.0.0.1"
        assert req.headers["X-Api-Key"] == "fixture-api"
        assert req.headers["X-Secret-Key"] == "fixture-secret"
        assert req.headers["X-Test"] == "inherited"
        state.requests.append(req)
        if state.server is not None:
            return state.server(req)
        return state.replies.pop(0) if state.replies else httpx.Response(200, json={"status": True, "result": {"ok": True}})

    async_mode = request.param
    root = (AsyncFutureAGIClient if async_mode else FutureAGIClient)(
        api_key="fixture-api", secret_key="fixture-secret",
        base_url="http://127.0.0.1:9", headers={"X-Test": "inherited"}, retries=0,
    )
    transport = root.generated_client._httpx_args["transport"]
    transport._wrapped = transport._wrapped_async = httpx.MockTransport(handle)
    generated = root.generated_client
    state.root = root
    state.prompts = (AsyncPromptsClient if async_mode else PromptsClient)(generated)
    state.knowledge_bases = (AsyncKnowledgeBasesClient if async_mode else KnowledgeBasesClient)(generated)
    state.scores = (AsyncScoresClient if async_mode else ScoresClient)(generated)
    yield state
    if async_mode:
        await root.aclose()
    else:
        root.close()
