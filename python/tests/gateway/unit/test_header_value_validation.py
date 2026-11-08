"""Client-owned header validation is value-free on every transport path."""
from __future__ import annotations

import asyncio
import inspect
import traceback
import types

import httpx
import pytest

from fi.gateway import AgentCC, AgentCCError, AsyncAgentCC
from fi.gateway._transport._base import RequestOptions

TOKEN = "synthetic-header-material"
PATHS = ("json", "form", "binary", "chat-stream", "completion-stream", "response-stream")
SOURCES = {"key": "authorization", "default": "x-client-default", "config": "x-client-config", "session": "x-agentcc-session-id"}


def assert_value_free(root):
    seen = set()

    def visit(value):
        if value is None or id(value) in seen:
            return
        seen.add(id(value))
        if isinstance(value, (str, bytes)):
            text = value.decode(errors="replace") if isinstance(value, bytes) else value
            assert TOKEN not in text
        elif isinstance(value, dict):
            for key, item in value.items():
                visit(key)
                visit(item)
        elif isinstance(value, (tuple, list, set, frozenset)):
            for item in value:
                visit(item)
        elif isinstance(value, BaseException):
            assert not isinstance(value, UnicodeEncodeError)
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
@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("invalid", ["é", "\r\n", "\x00"], ids=["non_ascii", "line_break", "nul"])
@pytest.mark.parametrize("expanded", [False, True])
def test_invalid_owned_headers_never_reach_errors_or_callbacks(asynchronous, path, source, invalid, expanded):
    async def exercise():
        sent, errors, arguments = [], [], []

        class Observer:
            def on_error(self, request, error):
                errors.append(error)
                arguments.append((request, error))
                assert_value_free((request, error))

        class Config:
            def to_headers(self):
                return {SOURCES["config"]: TOKEN + (invalid if source == "config" else "")}

        def handle(request):
            sent.append(True)
            return httpx.Response(200, json={})

        http = (httpx.AsyncClient if asynchronous else httpx.Client)(transport=httpx.MockTransport(handle), trust_env=False)
        defaults = {SOURCES["default"]: TOKEN + (invalid if source == "default" else "")}
        with pytest.warns(DeprecationWarning, match="^Deprecated gateway compatibility options: callbacks$"):
            client = (AsyncAgentCC if asynchronous else AgentCC)(
                api_key=TOKEN + (invalid if source == "key" else ""),
                base_url="https://gateway.test", http_client=http, callbacks=[Observer()],
                default_headers=defaults, config=Config(), max_retries=2,
                session_id=TOKEN + (invalid if source == "session" else ""),
                expanded_callback_events=expanded,
            )
        try:
            with pytest.raises(AgentCCError) as raised:
                result = public_call(client, path)
                if inspect.isawaitable(result):
                    await result
            error = raised.value
            assert str(error) == f"Invalid HTTP header value for {SOURCES[source]}."
            assert error.__cause__ is None
            assert error.__context__ is None
            assert_value_free((error, arguments, str(error), repr(error)))
            assert TOKEN not in "".join(traceback.format_exception(error))
            silent = asynchronous and path in ("completion-stream", "response-stream") and not expanded
            assert errors == ([] if silent else [error])
            assert sent == []
            assert defaults[SOURCES["default"]] == TOKEN + (invalid if source == "default" else "")
        finally:
            if asynchronous:
                await client.aclose()
                await http.aclose()
            else:
                client.close()
                http.close()

    asyncio.run(exercise())


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("path", ["json", "form", "binary", "stream"])
@pytest.mark.parametrize("exchange", ["success", "retry", "auth"])
def test_valid_owned_headers_keep_real_values_through_exchanges(asynchronous, path, exchange):
    async def exercise():
        sent, retained = [], []

        class Challenge(httpx.Auth):
            def auth_flow(self, request):
                response = yield request
                if response.status_code == 401:
                    yield request

        def handle(request):
            sent.append(dict(request.headers))
            retained.append(request)
            if len(sent) == 1 and exchange == "retry":
                raise httpx.ConnectError("synthetic connection failure", request=request)
            if len(sent) == 1 and exchange == "auth":
                return httpx.Response(401, json={})
            return httpx.Response(200, json={})

        http = (httpx.AsyncClient if asynchronous else httpx.Client)(
            transport=httpx.MockTransport(handle), trust_env=False,
            auth=Challenge() if exchange == "auth" else None,
        )
        client = (AsyncAgentCC if asynchronous else AgentCC)(
            api_key=TOKEN, base_url="https://gateway.test", http_client=http,
            default_headers={SOURCES["default"]: TOKEN}, session_id=TOKEN, max_retries=1,
        )
        base = client._get_base_client()
        base._calculate_delay = lambda *args: 0
        options = RequestOptions(method="POST", url="/probe", body={}, files={"file": ("sample.txt", b"fixture")} if path == "form" else None)
        response = None
        try:
            if path == "stream":
                # Stream opening has no transport retry, so exercise its retry
                # boundary directly, as the public non-streaming paths do.
                attempt = lambda: base._stream_request(options, None)
                result = base._retrying(options, attempt)
            else:
                result = base._request_raw_with_retry(options)
            if inspect.isawaitable(result):
                result = await result
            if isinstance(result, httpx.Response):
                response = result
            assert len(sent) == (1 if exchange == "success" else 2)
            for headers in sent:
                assert headers["authorization"] == "Bearer " + TOKEN
                assert headers[SOURCES["default"]] == TOKEN
                assert headers[SOURCES["session"]] == TOKEN
            for request in retained:
                assert request.headers["authorization"] == "[REDACTED]"
                assert request.headers[SOURCES["default"]] == "[REDACTED]"
                assert request.headers[SOURCES["session"]] == "[REDACTED]"
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

    asyncio.run(exercise())
