"""Sent request credentials are masked in place, never before the wire exchange."""
import builtins
import inspect
import json
from collections import namedtuple
from dataclasses import dataclass

import httpx
import pytest
from pydantic import BaseModel, ValidationError

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway._constants import CREDENTIAL_HEADER_NAMES
from fi.gateway.callbacks.base import CallbackHandler, redact_credentials
from fi.gateway.testing.recorder import RequestRecorder

pytestmark = [pytest.mark.anyio, pytest.mark.filterwarnings("ignore::DeprecationWarning")]
ORIGIN = "https://gateway.example.test"
KEY = "synthetic-sdk-key"
MASK = "[REDACTED]"
CHAT = {"id": "reply", "object": "chat.completion", "created": 0, "model": "test", "choices": []}


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


def reachable_requests(value, seen=None):
    """Walk stored diagnostics, not interpreter frames or arbitrary properties."""
    seen = set() if seen is None else seen
    if id(value) in seen:
        return
    seen.add(id(value))
    if isinstance(value, httpx.Request):
        yield value
        return
    if isinstance(value, (str, bytes, int, float, bool, type(None), type)):
        return
    if isinstance(value, dict):
        children = [*value, *value.values()]
    elif isinstance(value, (list, tuple, set, frozenset)):
        children = list(value)
    else:
        children = list(vars(value).values()) if hasattr(value, "__dict__") else []
        if isinstance(value, BaseException):
            children += [value.args, value.__cause__, value.__context__, getattr(value, "exceptions", ())]
        if isinstance(value, ValidationError):
            children.append(value.errors())
        for cls in type(value).__mro__:
            slots = cls.__dict__.get("__slots__", ())
            for name in (slots,) if isinstance(slots, str) else slots:
                if name not in {"__dict__", "__weakref__"}:
                    children.append(getattr(value, name, None))
    for child in children:
        yield from reachable_requests(child, seen)


class Capture(CallbackHandler):
    def __init__(self):
        self.events = []

    def capture(self, name, request, *args):
        self.events.append((name, request, args))

    def on_request_start(self, request):
        self.capture("start", request)

    def on_request_end(self, request, response):
        self.capture("end", request, response)

    def on_error(self, request, error):
        self.capture("error", request, error)

    def on_retry(self, request, error, attempt, delay):
        self.capture("retry", request, error, attempt, delay)

    def on_stream_start(self, request, info):
        self.capture("stream-start", request, info)

    def on_stream_chunk(self, request, chunk):
        self.capture("chunk", request, chunk)

    def on_stream_end(self, request, info, completion):
        self.capture("stream-end", request, info, completion)


class ChallengeAuth(httpx.Auth):
    """Two exchanges must both send real credentials, including reused requests."""
    def __init__(self, reuse):
        self.reuse = reuse

    def auth_flow(self, request):
        response = yield request
        if response.status_code == 401:
            yield request if self.reuse else httpx.Request(
                request.method, request.url, headers=request.headers, content=request.content)


@dataclass(slots=True)
class Diagnostic:
    request: httpx.Request


class Count(BaseModel):
    count: int


def diagnostic_error(request):
    leaf = httpx.ConnectError("synthetic child", request=request)
    leaf.headers = request.headers
    leaf.requests = {request}
    leaf.by_request = {request: "attempt"}
    leaf.diagnostic = Diagnostic(request)
    try:
        Count.model_validate({"count": request})
    except ValidationError as validation:
        leaf.validation = validation
    if hasattr(builtins, "ExceptionGroup"):
        class DiagnosticGroup(builtins.ExceptionGroup):
            __slots__ = ("label",)

            def __init__(self, message, children):
                self.label = "safe label"

        group = DiagnosticGroup("synthetic group", [leaf, leaf])
        leaf.__context__ = group
        outer = httpx.ConnectError("synthetic outer", request=request)
        outer.__cause__ = group
        return outer
    return leaf


CASES = [(resource, outcome) for resource in ("json", "form", "binary", "stream")
         for outcome in ("success", "status", "timeout", "connection", "group", "auth", "auth-reuse", "auth-error")]
CASES += [(resource, "retry") for resource in ("json", "form", "binary")]
CASES += [("stream", "body-error")]


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("resource,outcome", CASES)
async def test_wire_credentials_and_all_retained_requests(async_mode, redact, resource, outcome):
    capture = Capture()
    requests, wire, responses, errors = [], [], [], []
    defaults = {name.swapcase(): "synthetic-default-" + name for name in CREDENTIAL_HEADER_NAMES
                if name not in {"authorization", "cookie"}}
    defaults["X-Visible"] = "visible"
    extra = {"CoOkIe": "synthetic-caller-cookie"}
    before_defaults, before_extra = dict(defaults), dict(extra)

    class Body(httpx.SyncByteStream, httpx.AsyncByteStream):
        def __iter__(self):
            yield b'data: {"id":"reply","object":"chat.completion.chunk","created":0,"model":"test","choices":[]}\n\n'
            if outcome == "body-error":
                error = httpx.ReadTimeout("synthetic stream failure", request=requests[-1])
                errors.append(error)
                raise error
            yield b"data: [DONE]\n\n"

        async def __aiter__(self):
            for chunk in self:
                yield chunk

    def serve(request):
        requests.append(request)
        wire.append(dict(request.headers))
        if outcome in {"timeout", "connection", "group"} or (outcome == "auth-error" and len(requests) == 2):
            error = (diagnostic_error(request) if outcome == "group" else
                     (httpx.ReadTimeout if outcome == "timeout" else httpx.ConnectError)("synthetic failure", request=request))
            errors.append(error)
            raise error
        if outcome.startswith("auth") and len(requests) == 1:
            response = httpx.Response(401, headers={"www-authenticate": "synthetic"})
        elif outcome == "status" or (outcome == "retry" and len(requests) == 1):
            response = httpx.Response(503 if outcome == "retry" else 400,
                headers={"retry-after": "0"}, json={"error": {"message": "synthetic status"}})
        elif resource == "stream":
            response = httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=Body())
        elif resource == "binary":
            response = httpx.Response(200, content=b"synthetic audio")
        else:
            response = httpx.Response(200, json={"text": "ok"} if resource == "form" else CHAT)
        responses.append(response)
        return response

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve),
        auth=ChallengeAuth(outcome == "auth-reuse") if outcome.startswith("auth") else None, trust_env=False)
    client = (AsyncAgentCC if async_mode else AgentCC)(api_key=KEY, base_url=ORIGIN, http_client=http,
        callbacks=[capture], redact_messages=redact, default_headers=defaults,
        max_retries=1 if outcome == "retry" else 0)
    result = caught = None
    try:
        try:
            if resource == "form":
                result = await resolve(client.audio.transcriptions.create(model="test", file=("sample.wav", b"sample"), extra_headers=extra))
            elif resource == "binary":
                result = await resolve(client.audio.speech.create(model="test", input="hello", voice="alloy", extra_headers=extra))
            else:
                result = await resolve(client.chat.completions.create(model="test", messages=[],
                    stream=resource == "stream", extra_headers=extra))
                if resource == "stream":
                    if async_mode:
                        async for _ in result:
                            pass
                    else:
                        list(result)
        except Exception as exc:
            caught = exc
        failing = outcome in {"status", "timeout", "connection", "group", "auth-error", "body-error"}
        assert (caught is not None) is failing
        assert len(wire) == (2 if outcome == "retry" or outcome.startswith("auth") else 1)
        for headers in wire:
            assert headers["authorization"] == "Bearer " + KEY
            assert headers["cookie"] == extra["CoOkIe"]
            for name, value in defaults.items():
                assert headers[name.lower()] == value
        assert defaults == before_defaults and extra == before_extra
        descriptors = [event[1] for event in capture.events]
        assert descriptors and all(request is descriptors[0] for request in descriptors)
        assert descriptors[0].headers["CoOkIe"] == extra["CoOkIe"]
        assert all(name.lower() not in descriptors[0].headers for name in defaults)
        retained = list(reachable_requests([result, caught, capture.events, requests, responses, errors]))
        assert retained
        for request in retained:
            for name in CREDENTIAL_HEADER_NAMES:
                if name in request.headers:
                    assert request.headers[name] == MASK, name
            # Even a benign arbitrary default is client-composed private data.
            assert request.headers["x-visible"] == MASK
        terminal = [args[0] for name, _, args in capture.events if name == "error"]
        if caught is not None:
            assert terminal == [caught] and terminal[0] is caught
        if outcome == "group":
            original = errors[0]
            assert caught.__cause__ is original
            group = original.__cause__
            if group is not None:
                assert group.label == "safe label"
                leaf = group.exceptions[0]
                assert group.exceptions[1] is leaf and leaf.__context__ is group
                assert leaf.headers is requests[0].headers
                assert leaf.diagnostic.request is requests[0]
                assert leaf.validation.errors()[0]["input"] is requests[0]
        if caught is None and resource in {"json", "form"}:
            callback_response = capture.events[-1][2][0]
            assert callback_response._parsed is result
            assert callback_response.agentcc is result.agentcc
            assert callback_response.agentcc.http_response is responses[-1]
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
async def test_composed_default_and_session_values_are_not_callback_data(async_mode, redact):
    """Composed defaults and session metadata must not become callback arguments."""
    capture = Capture()
    defaults = {"X-Custom-Default": "synthetic-private-default"}
    http = (httpx.AsyncClient if async_mode else httpx.Client)(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=CHAT)))
    client = (AsyncAgentCC if async_mode else AgentCC)(api_key=KEY, base_url=ORIGIN,
        http_client=http, callbacks=[capture], default_headers=defaults, redact_messages=redact,
        session_id="synthetic-private-session", metadata={"label": "synthetic-private-metadata"})
    try:
        await resolve(client.chat.completions.create(model="test", messages=[]))
        text = repr([dict(request.headers) for request in reachable_requests(capture.events)])
        assert not any(marker in text for marker in
            (KEY, "synthetic-private-default", "synthetic-private-session", "synthetic-private-metadata"))
        assert defaults == {"X-Custom-Default": "synthetic-private-default"}
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("async_mode", [False, True])
async def test_namedtuple_metadata_is_recorded_and_redacted(async_mode, tmp_path):
    Metadata = namedtuple("Metadata", "visible nested")
    metadata = Metadata("kept", {"password": "synthetic-caller-secret"})
    output = tmp_path / "recording.json"
    recorder = RequestRecorder(str(output))
    http = (httpx.AsyncClient if async_mode else httpx.Client)(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=CHAT)))
    client = (AsyncAgentCC if async_mode else AgentCC)(api_key=KEY, base_url=ORIGIN,
        http_client=http, callbacks=[recorder])
    try:
        await resolve(client.chat.completions.create(model="test", messages=[], metadata={"record": metadata}))
        recorder.save()
        rows = json.loads(output.read_text())
        assert len(rows) == 1
        assert rows[0]["request"]["body"]["metadata"]["record"] == ["kept", {"password": MASK}]
        assert metadata.nested["password"] == "synthetic-caller-secret"
        redacted = redact_credentials(metadata)
        assert type(redacted) is Metadata and redacted.visible == "kept"
        assert redacted.nested == {"password": MASK}
    finally:
        await resolve(http.aclose() if async_mode else http.close())
