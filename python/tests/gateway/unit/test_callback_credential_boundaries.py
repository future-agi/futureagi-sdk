"""Live aliases must not expose SDK-composed headers through callback graphs."""
import builtins
import inspect
import json

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway._gateway_config import GatewayConfig, LoadBalanceConfig, LoadBalanceTarget
from fi.gateway.callbacks.base import CallbackHandler

pytestmark = [pytest.mark.anyio, pytest.mark.filterwarnings("ignore::DeprecationWarning")]


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


def graph_text(value, seen=None):
    """Include read-only exception children as well as stored Python state."""
    seen = set() if seen is None else seen
    if id(value) in seen:
        return ""
    seen.add(id(value))
    if isinstance(value, (str, bytes, int, float, bool, type(None))):
        return repr(value)
    if isinstance(value, dict):
        children = list(value) + list(value.values())
    elif isinstance(value, (list, tuple, set, frozenset)):
        children = list(value)
    else:
        children = list(vars(value).values()) if hasattr(value, "__dict__") else []
        if isinstance(value, BaseException):
            children += [value.args, value.__cause__, value.__context__]
            children.append(getattr(value, "exceptions", ()))
        for name in ("request", "response", "http_response", "next_request", "history"):
            try:
                child = getattr(value, name, None)
            except (RuntimeError, AttributeError):
                continue
            if child is not None and not callable(child):
                children.append(child)
    return " ".join(graph_text(child, seen) for child in children)


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("alias_case", ["within", "between", "caller_source", "credential_source"])
@pytest.mark.parametrize("outcome", ["success", "status", "connection", "exception_group", "base_group", "retry", "stream"])
async def test_composed_headers_stay_private_with_live_aliases(async_mode, redact, alias_case, outcome):
    if outcome in {"exception_group", "base_group"} and not hasattr(builtins, "BaseExceptionGroup"):
        pytest.skip("Native exception groups require Python 3.11")
    markers = ["synthetic-sdk-key", "synthetic-default", "synthetic-secondary",
               "synthetic-config", "synthetic-session", "synthetic-metadata",
               "synthetic-active-session", "synthetic-active-metadata"]
    shared = {"label": "before"}
    if alias_case == "credential_source":
        shared["password"] = "synthetic-caller-password"
    metadata = {"records": [shared, shared]}
    calls, mutations, sent, originals, wire_headers = [], [], [], [], []

    class Capture(CallbackHandler):
        def capture(self, request, *args):
            calls.append((request, args))

        def on_request_start(self, request):
            rows = request.body["metadata"]["records"]
            assert rows[0] is rows[1] is shared
            rows[0]["label"] = "after"
            if alias_case == "within":
                rows[0]["observed"] = rows[1]["label"]
            elif alias_case in {"caller_source", "credential_source"}:
                rows[0]["observed"] = shared["label"]
            mutations.append("first")
            self.capture(request)

        on_request_end = capture
        on_error = capture
        on_retry = capture
        on_stream_start = capture
        on_stream_chunk = capture
        on_stream_end = capture

    class Second(CallbackHandler):
        def on_request_start(self, request):
            assert request is calls[0][0]
            if alias_case == "between":
                rows = request.body["metadata"]["records"]
                rows[1]["observed"] = rows[0]["label"]
            mutations.append("second")

    def serve(request):
        sent.append(request)
        wire_headers.append(dict(request.headers))
        if outcome in {"connection", "exception_group", "base_group"}:
            leaf = httpx.ConnectError("offline child", request=request)
            outer = httpx.ConnectError("offline outer", request=request)
            if outcome == "connection":
                outer.__cause__ = leaf
            else:
                children = [leaf]
                if outcome == "base_group":
                    children.append(KeyboardInterrupt("offline cancellation"))
                group_type = getattr(builtins, "BaseExceptionGroup" if outcome == "base_group" else "ExceptionGroup")
                outer.__cause__ = group_type("offline group", children)
            originals.append(outer)
            raise outer
        if outcome == "status" or (outcome == "retry" and len(sent) == 1):
            response = httpx.Response(400 if outcome == "status" else 500,
                headers={"retry-after": "0", "x-visible": "yes"}, json={"error": {"message": "offline status"}})
        elif outcome == "stream":
            chunk = {"id": "reply", "object": "chat.completion.chunk", "created": 0,
                     "model": "test", "choices": []}
            response = httpx.Response(200, headers={"content-type": "text/event-stream", "x-visible": "yes"},
                text="data: " + json.dumps(chunk) + "\n\ndata: [DONE]\n\n")
        else:
            response = httpx.Response(200, headers={"x-visible": "yes"}, json={"id": "reply",
                "object": "chat.completion", "created": 0, "model": "test", "choices": []})
        originals.append(response)
        return response

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve))
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key=markers[0], base_url="https://gateway.example.test", http_client=http,
        default_headers={"X-Custom": markers[1], "X-Api-Key": markers[2]},
        config=GatewayConfig(load_balance=LoadBalanceConfig(targets=[LoadBalanceTarget(model="test", virtual_key=markers[3])])),
        session_id=markers[4], metadata={"label": markers[5]},
        callbacks=[Capture(), Second()], redact_messages=redact, max_retries=1 if outcome == "retry" else 0)
    result = error = None
    try:
        with client.session(session_id=markers[6], metadata={"label": markers[7]}):
            try:
                result = await resolve(client.chat.completions.create(model="test", messages=[], metadata=metadata,
                    extra_headers={"X-Caller": "synthetic-caller-header"}, stream=outcome == "stream"))
                if outcome == "stream":
                    if async_mode:
                        async for _ in result:
                            pass
                    else:
                        list(result)
            except Exception as exc:
                error = exc
        assert mutations == ["first", "second"]
        assert shared["observed"] == "after"
        assert all(row["observed"] == "after" for row in json.loads(sent[0].content)["metadata"]["records"])
        assert len(calls) >= 2 and all(req is calls[0][0] for req, _ in calls)
        request = calls[0][0]
        assert request.body["metadata"] is metadata
        assert request.headers["X-Caller"] == "synthetic-caller-header"
        if alias_case == "credential_source":
            assert request.body["metadata"]["records"][0]["password"] == "synthetic-caller-password"
        wire = wire_headers[0]
        assert wire["authorization"] == "Bearer " + markers[0]
        assert wire["x-custom"] == markers[1] and wire["x-api-key"] == markers[2]
        assert markers[3] in wire["x-agentcc-config"]
        assert wire["x-agentcc-session-id"] == markers[6]
        assert markers[5] in wire["x-agentcc-metadata"]
        assert wire["x-agentcc-metadata-label"] == markers[7]
        text = graph_text(calls)
        assert all(marker not in text for marker in markers)
        if outcome in {"connection", "exception_group", "base_group"}:
            assert error.__cause__ is originals[0]
            view = calls[-1][1][0]
            assert view is error
            assert view.request is error.request is None
            assert view.__cause__.request.headers["authorization"] == "[REDACTED]"
            child = view.__cause__.__cause__
            original_child = originals[0].__cause__
            if outcome != "connection":
                assert type(child) is type(original_child) and child.message == original_child.message
                child, original_child = child.exceptions[0], original_child.exceptions[0]
            assert child is original_child
            assert child.request.headers["authorization"] == "[REDACTED]"
            assert original_child.request is sent[0]
        elif outcome == "status":
            assert error.response is originals[0]
            view = calls[-1][1][0]
            assert view.response is error.response
            assert view.response.request.headers["authorization"] == "[REDACTED]"
            assert view.response.status_code == 400 and view.response.content == error.response.content
        else:
            assert error is None and result.agentcc.http_response is originals[-1]
            response = calls[-1][1][0]
            assert response.agentcc.http_response is originals[-1]
            assert response.agentcc.http_response.request.headers["authorization"] == "[REDACTED]"
            assert response.agentcc.http_response.headers["x-visible"] == "yes"
            if outcome != "stream":
                assert response._parsed.agentcc.http_response is response.agentcc.http_response
    finally:
        await resolve(http.aclose() if async_mode else http.close())
