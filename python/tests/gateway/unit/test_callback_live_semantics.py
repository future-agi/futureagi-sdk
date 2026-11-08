"""Independent offline published-contract differential probes; synthetic values only."""
import copy
import inspect
import json
from contextlib import asynccontextmanager
from email.parser import BytesParser
from email.policy import default

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway.callbacks.base import CallbackHandler
from ._callback_live_fixtures import (
    anyio_backend, resolve, form, client_for, assert_caller_values_visible, reachable_text,
)

pytestmark = [pytest.mark.anyio, pytest.mark.filterwarnings("ignore::DeprecationWarning")]

@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("operation", ["rotate", "insert", "delete", "slice", "replace", "copy_record"])
async def test_record_mutations(async_mode, redact, operation):
    a = {"label": "a", "password": "synthetic-a", "nested": {"api_key": "synthetic-inner-a", "value": 1}}
    b = {"label": "b", "password": "synthetic-b", "nested": {"api_key": "synthetic-inner-b", "value": 2}}
    c = {"label": "c", "password": "synthetic-c", "nested": {"api_key": "synthetic-inner-c", "value": 3}}
    expected = {"rotate": [c, a, b], "insert": [a, {"label": "new"}, b, c], "delete": [a, c],
                "slice": [c, {"label": "new"}, a], "replace": [a, {"label": "new"}, c],
                "copy_record": [{**a, "label": "copied-a"}, b, c]}[operation]
    snapshots = []
    called = []

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            snapshots.append(copy.deepcopy(request.body))
            rows = request.body["metadata"]["records"]
            if operation == "rotate":
                rows.insert(0, rows.pop())
            elif operation == "insert":
                rows.insert(1, {"label": "new"})
            elif operation == "delete":
                del rows[1]
            elif operation == "slice":
                rows[:] = [rows[2], {"label": "new"}, rows[0]]
            elif operation == "replace":
                rows[1] = {"label": "new"}
            else:
                rows[0] = {**rows[0], "label": "copied-a"}
            called.append("complete")

    async with client_for(async_mode, [Edit()], redact) as (client, seen):
        await resolve(client.chat.completions.create(model="test", messages=[{"role": "user", "content": "text"}],
                                                   metadata={"records": copy.deepcopy([a, b, c])}))
    assert called == ["complete"]
    assert_caller_values_visible(snapshots, ["synthetic-a", "synthetic-b", "synthetic-c", "synthetic-inner"])
    assert json.loads(seen[0].content)["metadata"]["records"] == expected

@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("arguments", ["argument text", None])
async def test_nested_annotations_and_tool_schema(async_mode, redact, arguments):
    called = []
    observed = []
    message = {"role": "assistant", "content": "message text",
               "annotations": {"api_key": "synthetic-annotation", "items": [{"n": 1}, {"n": 2}]},
               "tool_calls": [{"id": "tool", "type": "function", "function": {
                   "name": "before", "arguments": arguments,
                   "parameters": {"password": "synthetic-schema", "properties": {"x": {"description": "before"}}}}}],
               "function_call": {"name": "legacy", "arguments": arguments, "schema": {"labels": ["before"]}}}
    expected = copy.deepcopy(message)
    expected["annotations"]["items"] = [{"n": 2}, {"n": 3}, {"n": 1}]
    function = expected["tool_calls"][0]["function"]
    function["parameters"]["properties"]["x"]["description"] = "after"
    expected["function_call"]["schema"]["labels"].append("after")
    if not redact or arguments is None:
        function["name"] = "after"
    if not redact:
        expected["role"] = "user"
        expected["content"] = "edited"

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            m = request.body["messages"][0]
            observed.append(copy.deepcopy(m))
            rows = m["annotations"]["items"]
            rows[:] = [rows[1], {"n": 3}, rows[0]]
            f = m["tool_calls"][0]["function"]
            f["parameters"]["properties"]["x"]["description"] = "after"
            f["name"] = "after"
            m["function_call"]["schema"]["labels"].append("after")
            m["role"] = "user"
            m["content"] = "edited"
            called.append("complete")

    async with client_for(async_mode, [Edit()], redact) as (client, seen):
        await resolve(client.chat.completions.create(model="test", messages=[message]))
    assert called == ["complete"]
    assert_caller_values_visible(observed, ["synthetic-annotation", "synthetic-schema"])
    assert json.loads(seen[0].content)["messages"] == [expected]

@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("route", ["transcriptions", "translations"])
@pytest.mark.parametrize("operation", ["in_place", "replace", "edit_then_replace"])
async def test_header_and_file_mutations(async_mode, redact, route, operation):
    called = []

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            if operation != "replace":
                request.headers["X-Original"] = "edited"
                request.headers["X-Added"] = "added"
                del request.headers["X-Delete"]
                request.files["file"] = ("edited.wav", b"edited")
            if operation != "in_place":
                request.headers = {"X-Replacement": "replacement"}
                request.files = {"file": ("replacement.wav", b"replacement")}
            called.append("complete")

    async with client_for(async_mode, [Edit()], redact) as (client, seen):
        await resolve(getattr(client.audio, route).create(model="test", file=("original.wav", b"original"),
                      prompt="text", extra_headers={"X-Original": "original", "X-Delete": "delete"}))
    assert called == ["complete"]
    if operation != "in_place" and not redact:
        expected_headers = {"x-replacement": "replacement"}
        expected_file = ("replacement.wav", b"replacement")
    elif operation != "replace":
        expected_headers = {"x-original": "edited", "x-added": "added"}
        expected_file = ("edited.wav", b"edited")
    else:
        expected_headers = {"x-original": "original", "x-delete": "delete"}
        expected_file = ("original.wav", b"original")
    actual_headers = {k: v for k, v in seen[0].headers.items() if k.startswith("x-") and not k.startswith("x-agentcc")}
    assert actual_headers == expected_headers
    assert form(seen[0])["file"] == expected_file
    assert form(seen[0])["prompt"] == (None, b"text")

@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
async def test_alias_observation_within_and_between_callbacks(async_mode, redact):
    shared = {"label": "before", "password": "synthetic-alias"}
    observations = []

    class First(CallbackHandler):
        def on_request_start(self, request):
            rows = request.body["metadata"]["records"]
            rows[0]["label"] = "after"
            observations.append(rows[1]["label"])

    class Second(CallbackHandler):
        def on_request_start(self, request):
            observations.append(request.body["metadata"]["records"][1]["label"])

    async with client_for(async_mode, [First(), Second()], redact) as (client, seen):
        await resolve(client.chat.completions.create(model="test", messages=[{"role": "user", "content": "text"}],
                                                   metadata={"records": [shared, shared]}))
    assert observations == ["after", "after"]
    assert [r["label"] for r in json.loads(seen[0].content)["metadata"]["records"]] == ["after", "after"]


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
async def test_shared_source_observation_changes_payload(async_mode, redact):
    shared = {"label": "before"}
    completed = []

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            request.body["metadata"]["label"] = "after"
            request.body["metadata"]["observed"] = shared["label"]
            completed.append(True)

    async with client_for(async_mode, [Edit()], redact) as (client, seen):
        await resolve(client.chat.completions.create(model="test", messages=[{"role": "user", "content": "text"}],
                                                   metadata=shared))
    assert completed == [True]
    assert json.loads(seen[0].content)["metadata"] == {"label": "after", "observed": "after"}


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("hook", ["end", "error"])
async def test_callback_response_does_not_expose_authentication(async_mode, redact, hook):
    observed = []

    class Capture(CallbackHandler):
        def on_request_end(self, request, response):
            if hook == "end":
                meta = response.agentcc
                raw = getattr(meta, "http_response", None)
                observed.append(dict(raw.request.headers) if raw is not None else {})

        def on_error(self, request, error):
            if hook == "error":
                raw = getattr(error, "response", None)
                observed.append(dict(raw.request.headers) if raw is not None else {})

    def handler(request):
        if hook == "error":
            return httpx.Response(400, json={"error": {"message": "bad request", "type": "bad_request"}})
        return httpx.Response(200, json={"id": "reply", "object": "chat.completion", "created": 0,
                                        "model": "test", "choices": []})

    async with client_for(async_mode, [Capture()], redact, handler) as (client, seen):
        try:
            await resolve(client.chat.completions.create(model="test", messages=[], extra_headers={
                "Authorization": "Bearer synthetic-request-key",
                "X-AgentCC-Config": '{"virtual_key":"synthetic-config-key"}'}))
        except Exception:
            if hook != "error":
                raise
    assert len(seen) == 1 and len(observed) == 1
    # Do not print synthetic values as failure output: expose booleans only.
    exposed = {marker: marker in repr(observed) for marker in
               ["synthetic-client-key", "synthetic-request-key", "synthetic-config-key"]}
    assert not any(exposed.values()), {"credential_exposed": any(exposed.values()), "hook": hook}


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("outcome", ["success", "error", "retry", "stream", "connection", "session"])
async def test_composed_headers_unreachable_and_originals_preserved(async_mode, redact, outcome):
    from fi.gateway._gateway_config import GatewayConfig, LoadBalanceConfig, LoadBalanceTarget

    markers = ["synthetic-sdk-key", "synthetic-default", "synthetic-session",
               "synthetic-metadata", "synthetic-virtual"]
    requests, arguments, originals, sent, wire_headers = [], [], [], [], []

    class Capture(CallbackHandler):
        def capture(self, request, *args):
            requests.append(request)
            arguments.extend(args)

        on_request_start = capture
        on_request_end = capture
        on_error = capture
        on_retry = capture
        on_stream_start = capture
        on_stream_chunk = capture
        on_stream_end = capture

    def serve(request):
        sent.append(request)
        wire_headers.append(dict(request.headers))
        if outcome == "connection":
            error = httpx.ConnectError("offline failure", request=request)
            originals.append(error)
            raise error
        if outcome == "error" or (outcome == "retry" and len(sent) == 1):
            response = httpx.Response(400 if outcome == "error" else 500,
                headers={"retry-after": "0", "x-visible": "response-value"},
                json={"error": {"message": "bad request", "type": "bad_request"}})
        elif outcome == "stream":
            chunk = {"id": "reply", "object": "chat.completion.chunk", "created": 0,
                     "model": "test", "choices": []}
            response = httpx.Response(200, headers={"content-type": "text/event-stream"},
                text="data: " + json.dumps(chunk) + "\n\ndata: [DONE]\n\n")
        else:
            response = httpx.Response(200, headers={"x-visible": "response-value"},
                json={"id": "reply", "object": "chat.completion", "created": 0,
                      "model": "test", "choices": []})
        originals.append(response)
        return response

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve))
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key=markers[0], base_url="https://gateway.example.test", http_client=http,
        callbacks=[Capture()], redact_messages=redact, max_retries=1 if outcome == "retry" else 0,
        default_headers={"X-Custom-Default": markers[1]}, session_id=markers[2],
        metadata={"label": markers[3]}, config=GatewayConfig(load_balance=LoadBalanceConfig(
            targets=[LoadBalanceTarget(model="test", virtual_key=markers[4])])))
    result = caller_error = None
    if outcome == "session":
        from fi.gateway._session import Session
        client._active_session = Session(session_id=markers[2], metadata={"label": markers[3]})
    try:
        try:
            result = await resolve(client.chat.completions.create(model="test", messages=[],
                stream=outcome == "stream", metadata={"password": "synthetic-caller"}))
            if outcome == "stream":
                if async_mode:
                    async for _ in result:
                        pass
                else:
                    list(result)
        except Exception as error:
            caller_error = error
        assert requests and arguments
        assert all(request is requests[0] for request in requests)
        assert requests[0].body["metadata"]["password"] == "synthetic-caller"
        text = reachable_text([requests, arguments])
        assert not any(marker in text for marker in markers)
        assert all(marker in repr(wire_headers[0]) for marker in markers)
        for argument in arguments:
            raw = getattr(getattr(argument, "agentcc", None), "http_response", None)
            if raw is not None:
                assert isinstance(raw, httpx.Response)
                assert raw in originals
                assert raw.request.method == "POST" and raw.request.url == sent[0].url
                assert raw.headers == originals[-1].headers
            parsed = getattr(argument, "_parsed", None)
            if getattr(parsed, "agentcc", None) is not None:
                assert parsed.agentcc.http_response is raw
        if caller_error is not None:
            view = next(arg for arg in arguments if isinstance(arg, type(caller_error)))
            assert view is caller_error
            if outcome == "connection":
                assert caller_error.__cause__ is originals[0]
                assert view.__cause__.request.headers["authorization"] == "[REDACTED]"
            else:
                assert caller_error.response is originals[0]
                assert view.response.content == caller_error.response.content
        else:
            assert result.agentcc.http_response is originals[-1]
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("multipart", [False, True])
def test_transport_descriptor_is_live_and_copy_is_shallow(redact, multipart):
    from fi.gateway._transport._base import RequestOptions
    from fi.gateway._transport._sync import SyncBaseClient

    shared = {"password": "synthetic-caller", "label": "before"}
    body = {"messages": [], "metadata": shared}
    headers = {"Authorization": "synthetic-request"}
    files = {"file": ("sample.wav", b"sample")} if multipart else None
    options = RequestOptions(method="POST", url="/v1/test", headers=headers, files=files,
                             body=None if multipart else body, form=body if multipart else None)
    transport = SyncBaseClient(api_key="synthetic-sdk", base_url="https://gateway.example.test",
                               redact_messages=redact)
    transport._bind_request(options)
    request = transport._for_callbacks(options)
    assert transport._for_callbacks(options) is request
    assert request.headers is headers and request.files is files
    assert request.body["metadata"] is shared
    request.body["metadata"]["label"] = "after"
    assert shared["label"] == "after"
    if not redact and not multipart:
        assert request is options
    request.headers = {"X-New": "new"}
    request.body = {"model": "replacement"}
    assert (options.headers is headers) is redact
    assert (options.form if multipart else options.body) == (body if redact else {"model": "replacement"})


@pytest.mark.parametrize("sink", ["recorder", "json", "logging", "otel"])
def test_builtin_sink_writes_without_caller_credentials(sink, tmp_path):
    import logging
    from types import SimpleNamespace
    from fi.gateway.callbacks.base import CallbackRequest, CallbackResponse

    output = tmp_path / "output.json"
    request = CallbackRequest("POST", "/v1/test", {"Authorization": "synthetic-header"},
        {"model": "test", "metadata": {"password": "synthetic-body", "visible": "yes"}},
        files={"api_key": "synthetic-file"})
    response = CallbackResponse(200, {}, body={"model": "test"})
    if sink == "recorder":
        from fi.gateway.testing.recorder import RequestRecorder
        callback = RequestRecorder(str(output))
        callback.on_request_end(request, response)
        callback.save()
    elif sink == "json":
        from fi.gateway.callbacks.json_logger import JSONLoggingCallbackHandler
        JSONLoggingCallbackHandler(str(output)).on_request_end(request, response)
    elif sink == "logging":
        from fi.gateway.callbacks.logging import LoggingCallback
        logger = logging.getLogger("callback-output-test")
        handler = logging.FileHandler(output)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        try:
            LoggingCallback(logger_name=logger.name).on_request_start(request)
        finally:
            logger.removeHandler(handler)
            handler.close()
    else:
        from fi.gateway.callbacks.opentelemetry import OpenTelemetryCallback

        class Span:
            def __init__(self):
                self.attributes = {}

            def set_attribute(self, key, value):
                self.attributes[key] = value

            def end(self):
                output.write_text(json.dumps(self.attributes))

        callback = OpenTelemetryCallback(tracer=SimpleNamespace(start_span=lambda name: Span()))
        callback.on_request_start(request)
        callback.on_request_end(request, response)
    text = output.read_text()
    assert text.strip()
    assert all(marker not in text for marker in ("synthetic-header", "synthetic-body", "synthetic-file"))
    assert request.body["metadata"]["password"] == "synthetic-body"
    assert request.headers["Authorization"] == "synthetic-header"
    if sink in {"recorder", "otel"}:
        assert "[REDACTED]" in text and "yes" in text
