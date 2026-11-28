"""Shared offline callback observation fixtures."""
import inspect
from contextlib import asynccontextmanager
from email.parser import BytesParser
from email.policy import default
import httpx
import pytest
from fi.gateway import AgentCC, AsyncAgentCC


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


def form(request):
    envelope = b"Content-Type: " + request.headers["content-type"].encode() + b"\r\nMIME-Version: 1.0\r\n\r\n" + request.content
    parts = BytesParser(policy=default).parsebytes(envelope).iter_parts()
    return {p.get_param("name", header="content-disposition"):
            (p.get_filename(), p.get_payload(decode=True)) for p in parts}


@asynccontextmanager
async def client_for(async_mode, callbacks, redact, handler=None):
    seen = []

    def serve(request):
        seen.append(request)
        if handler:
            return handler(request)
        if request.url.path.endswith(("/transcriptions", "/translations")):
            return httpx.Response(200, json={"text": "ok"})
        return httpx.Response(200, json={"id": "reply", "object": "chat.completion", "created": 0,
                                         "model": "test", "choices": []})

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve))
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key="synthetic-client-key", base_url="https://gateway.example.test", http_client=http,
        max_retries=0, callbacks=callbacks, redact_messages=redact)
    try:
        yield client, seen
    finally:
        await resolve(http.aclose() if async_mode else http.close())


def assert_caller_values_visible(observed, markers):
    # Per-request values belong to the caller, including credential-named keys.
    assert all(marker in repr(observed) for marker in markers)


def reachable_text(value, seen=None):
    """Inspect stored object state, including private response/request links."""
    seen = set() if seen is None else seen
    if id(value) in seen:
        return ""
    seen.add(id(value))
    if isinstance(value, (str, bytes, int, float, bool, type(None))):
        return repr(value)
    if isinstance(value, dict):
        children = list(value.keys()) + list(value.values())
    elif isinstance(value, (list, tuple, set)):
        children = value
    else:
        children = list(vars(value).values()) if hasattr(value, "__dict__") else []
        if isinstance(value, BaseException):
            children += [value.args, value.__cause__, value.__context__]
    return " ".join(reachable_text(child, seen) for child in children)
