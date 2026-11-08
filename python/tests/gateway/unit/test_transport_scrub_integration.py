"""Synthetic cross-transport controls for composed headers and redirects."""
from __future__ import annotations

import asyncio
import inspect
import types

import httpx
import pytest

from fi.gateway import AgentCC, AgentCCError, AsyncAgentCC
from fi.gateway._transport._base import RequestOptions

KEY = "synthetic-integration-key-not-a-credential"
SESSION = "synthetic-integration-session-not-a-credential"
CONFIG = "synthetic-integration-config-not-a-credential"
MATERIAL = (KEY, SESSION, CONFIG)
PATHS = ("json", "form", "binary", "chat-stream", "completion-stream", "response-stream")


def assert_no_composed_material(root):
    """Inspect stored state and exception links, never interpreter frames."""
    seen = set()

    def visit(value):
        if value is None or id(value) in seen:
            return
        seen.add(id(value))
        if isinstance(value, (str, bytes)):
            text = value.decode(errors="replace") if isinstance(value, bytes) else value
            assert not any(token in text for token in MATERIAL)
        elif isinstance(value, httpx.Request):
            visit(dict(value.headers))
        elif isinstance(value, httpx.Response):
            visit(value._request)
            visit(value.history)
            visit(value.next_request)
        elif isinstance(value, dict):
            for key, item in value.items():
                visit(key)
                visit(item)
        elif isinstance(value, (tuple, list, set)):
            for item in value:
                visit(item)
        elif isinstance(value, BaseException):
            visit(value.args)
            visit(vars(value))
            visit(value.__cause__)
            visit(value.__context__)
        elif not isinstance(value, (type, types.FunctionType, types.MethodType, types.ModuleType)) and hasattr(value, "__dict__"):
            visit(vars(value))

    visit(root)


def public_call(client, path):
    if path == "form":
        return client.files.create(file=("sample.txt", b"fixture"), purpose="assistants")
    if path == "binary":
        return client.audio.speech.create(model="fixture", input="hello", voice="alloy")
    if path == "completion-stream":
        return client.completions.create(model="fixture", prompt="hello", stream=True)
    if path == "response-stream":
        return client.responses.create(model="fixture", input="hello", stream=True)
    return client.chat.completions.create(model="fixture", messages=[], stream=path == "chat-stream")


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("expanded", [False, True])
def test_status_hook_error_and_callback_retain_no_composed_credentials(asynchronous, path, expanded):
    async def exercise():
        sent, errors, hook_errors, callback_arguments = [], [], [], []
        caller_headers = {"x-api-key": KEY, "x-agentcc-config": CONFIG}

        def handler(request):
            sent.append(dict(request.headers))
            return httpx.Response(503, headers={"x-agentcc-dispatched": "true"}, json={"error": "fixture"})

        def hook(response):
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                hook_errors.append(error)
                raise

        async def async_hook(response):
            hook(response)

        class Observer:
            def on_error(self, request, error):
                errors.append(error)
                callback_arguments.append((request, error))
                assert_no_composed_material((request, error))

        cls = httpx.AsyncClient if asynchronous else httpx.Client
        http = cls(transport=httpx.MockTransport(handler), follow_redirects=True,
                   event_hooks={"response": [async_hook if asynchronous else hook]}, trust_env=False)
        with pytest.warns(DeprecationWarning, match="^Deprecated gateway compatibility options: callbacks$"):
            client = (AsyncAgentCC if asynchronous else AgentCC)(
                api_key=KEY, base_url="https://gateway.test", http_client=http,
                session_id=SESSION, default_headers=caller_headers, callbacks=[Observer()], max_retries=2,
                expanded_callback_events=expanded,
            )
        caught = None
        try:
            with pytest.raises(httpx.HTTPStatusError) as raised:
                result = public_call(client, path)
                if inspect.isawaitable(result):
                    await result
            caught = raised.value
        finally:
            if asynchronous:
                await client.aclose()
                await http.aclose()
            else:
                client.close()
                http.close()
        assert len(sent) == 1
        assert sent[0]["authorization"] == "Bearer " + KEY
        assert sent[0]["x-agentcc-session-id"] == SESSION
        assert sent[0]["x-agentcc-config"] == CONFIG
        published_direct_stream = asynchronous and path in ("completion-stream", "response-stream") and not expanded
        assert errors == ([] if published_direct_stream else [caught])
        assert hook_errors == [caught]
        assert_no_composed_material((caught, callback_arguments))
        assert caught.request.headers["authorization"] == "[REDACTED]"
        assert caught.response.request is caught.request
        assert caller_headers == {"x-api-key": KEY, "x-agentcc-config": CONFIG}

    asyncio.run(exercise())


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("path", ["json", "form", "binary", "stream"])
@pytest.mark.parametrize("target", ["http://gateway.test/next", "https://other.test/next", "https://gateway.test:444/next", "https://gateway.test/next"])
def test_every_send_disables_redirects_and_never_resends_credentials(asynchronous, path, target):
    async def exercise():
        sent, flags = [], []

        def handler(request):
            sent.append((str(request.url), dict(request.headers)))
            return httpx.Response(307, headers={"location": target}, content=b"fixture")

        class SyncHTTP(httpx.Client):
            def send(self, request, **kwargs):
                flags.append(kwargs.get("follow_redirects"))
                return super().send(request, **kwargs)

        class AsyncHTTP(httpx.AsyncClient):
            async def send(self, request, **kwargs):
                flags.append(kwargs.get("follow_redirects"))
                return await super().send(request, **kwargs)

        http = (AsyncHTTP if asynchronous else SyncHTTP)(
            transport=httpx.MockTransport(handler), follow_redirects=True, trust_env=False,
        )
        client = (AsyncAgentCC if asynchronous else AgentCC)(
            api_key=KEY, base_url="https://gateway.test", http_client=http,
            session_id=SESSION, default_headers={"x-api-key": KEY, "x-agentcc-config": CONFIG},
        )
        base = client._get_base_client()
        options = RequestOptions(method="POST", url="/probe", body={"fixture": True},
                                 files={"file": ("sample.txt", b"fixture")} if path == "form" else None)
        response = None
        try:
            if path == "binary":
                result = base._request_raw(options, None)
            elif path == "stream":
                result = base._stream_request(options, None)
            else:
                result = base._send(options, None)
            if inspect.isawaitable(result):
                result = await result
            if isinstance(result, httpx.Response):
                response = result
                assert response.status_code == 307
            else:
                assert result == b"fixture"
        finally:
            if response is not None:
                if asynchronous:
                    await response.aclose()
                else:
                    response.close()
            if asynchronous:
                await client.aclose()
                await http.aclose()
            else:
                client.close()
                http.close()
        assert flags == [False]
        assert len(sent) == 1
        assert sent[0][0] == "https://gateway.test/probe"
        assert sent[0][1]["authorization"] == "Bearer " + KEY

    asyncio.run(exercise())


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("path", ["json", "form", "binary", "stream"])
@pytest.mark.parametrize("target", ["http://gateway.test/probe", "https://other.test/probe", "https://gateway.test:444/probe"])
def test_every_send_rejects_cross_origin_before_transport(asynchronous, path, target):
    async def exercise():
        sent = []

        def handler(request):
            sent.append(request)
            return httpx.Response(200, json={})

        http = (httpx.AsyncClient if asynchronous else httpx.Client)(transport=httpx.MockTransport(handler), trust_env=False)
        client = (AsyncAgentCC if asynchronous else AgentCC)(api_key=KEY, base_url="https://gateway.test", http_client=http)
        base = client._get_base_client()
        options = RequestOptions(method="POST", url=target, body={},
                                 files={"file": ("sample.txt", b"fixture")} if path == "form" else None)
        try:
            with pytest.raises(AgentCCError, match="explicitly configured origin"):
                method = base._request_raw if path == "binary" else base._stream_request if path == "stream" else base._send
                result = method(options, None)
                if inspect.isawaitable(result):
                    await result
        finally:
            if asynchronous:
                await client.aclose()
                await http.aclose()
            else:
                client.close()
                http.close()
        assert sent == []

    asyncio.run(exercise())
