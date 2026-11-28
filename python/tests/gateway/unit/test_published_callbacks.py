"""The 0.7.0 callback descriptor, events and built-in defaults."""

import json

import pytest

from fi.gateway.callbacks.base import CallbackHandler
from fi.gateway.callbacks.logging import LoggingCallback, MetricsCallback
from fi.gateway.testing.recorder import RequestRecorder

from ._forms import read_form
from ._published_helpers import call_resource, client_for, clear_platform_keys, resolve

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


class Capture(CallbackHandler):
    def __init__(self):
        self.requests = []
        self.responses = []
        self.events = []

    def on_request_start(self, request):
        self.requests.append(request)
        self.events.append("start")

    def on_request_end(self, request, response):
        self.responses.append(response)
        self.events.append("end")

    def on_stream_start(self, *args):
        self.events.append("stream_start")

    def on_stream_chunk(self, *args):
        self.events.append("chunk")

    def on_stream_end(self, *args):
        self.events.append("stream_end")

    def on_cache_hit(self, *args):
        self.events.append("cache")

    def on_cost_update(self, *args):
        self.events.append("cost")

    def on_fallback(self, *args):
        self.events.append("fallback")

    def on_session_start(self, *args):
        self.events.append("session_start")

    def on_session_end(self, *args):
        self.events.append("session_end")


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("resource", ["chat", "stream", "transcriptions", "translations", "files"])
async def test_published_descriptor_and_mutation(async_mode, redact, resource):
    capture = Capture()

    class Mutate(CallbackHandler):
        def on_request_start(self, request):
            request.body["model"] = "changed"
            request.headers["X-Callback"] = "present"

    async with client_for(async_mode, callbacks=[capture, Mutate()], redact_messages=redact) as (client, seen):
        await call_resource(client, resource)
    request = capture.requests[0]
    assert request.url.startswith("/v1/")
    assert request.timeout is None and request.max_retries is None
    if resource in ("chat", "stream"):
        assert request.files is None
        wire = json.loads(seen[0].content)
    else:
        assert "file" in request.files
        wire, _ = read_form(seen[0])
    if resource != "files":
        expected = "test" if redact else "changed"
        assert wire["model"] == ([expected] if isinstance(wire["model"], list) else expected)
    assert seen[0].headers["x-callback"] == "present"


@pytest.mark.parametrize("async_mode", [False, True])
async def test_published_model_body_events_metrics_and_recording(async_mode, tmp_path):
    capture, metrics = Capture(), MetricsCallback()
    recorder = RequestRecorder(str(tmp_path / "recording.json"))
    async with client_for(async_mode, callbacks=[capture, metrics, recorder]) as (client, seen):
        with client.session(metadata={"step": "one"}) as session:
            result = await call_resource(client, "chat")
    assert capture.events == ["start", "end"]
    assert capture.responses[0].body == result.model_dump()
    assert "agentcc" in capture.responses[0].body
    assert metrics.total_tokens == 0
    assert metrics.total_requests == 1 and metrics.total_cost == 0.25
    assert session.request_count == 1 and session.total_tokens == 5
    assert recorder.recordings[0]["request"]["url"] == "/v1/chat/completions"
    assert recorder.recordings[0]["response"]["body"] == result.model_dump()


def test_published_default_logger():
    assert LoggingCallback()._logger.name == "agentcc"


@pytest.mark.parametrize("async_mode", [False, True])
async def test_published_stream_events_and_session_accounting(async_mode):
    capture = Capture()
    async with client_for(async_mode, callbacks=[capture]) as (client, seen):
        with client.session() as session:
            await call_resource(client, "stream")
    assert capture.events == ["start", "stream_start", "chunk", "stream_end", "end"]
    assert session.request_count == 1 and session.total_tokens == 5
    assert capture.responses[0].body is None


@pytest.mark.parametrize("async_mode", [False, True])
async def test_published_raw_response_and_recording(async_mode, tmp_path):
    capture = Capture()
    recorder = RequestRecorder(str(tmp_path / "raw.json"))
    async with client_for(async_mode, callbacks=[capture, recorder]) as (client, seen):
        with client.session() as session:
            await call_resource(client, "speech")
    assert capture.responses[0].status_code == 200
    assert capture.responses[0].headers == {}
    assert capture.responses[0].body is None and capture.responses[0].agentcc is None
    assert session.request_count == 0
    assert recorder.recordings[0]["response"] == {"status_code": 200, "body": None}


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
async def test_caller_credentials_stay_live_without_changing_wire_values(async_mode, redact):
    capture = Capture()

    class Mutate(CallbackHandler):
        def on_request_start(self, request):
            request.body["metadata"]["visible"] = "updated"
            request.body["metadata"]["nested"][0]["visible"] = "updated"
            request.headers["X-Visible"] = "updated"

    async with client_for(async_mode, callbacks=[capture, Mutate()], redact_messages=redact) as (client, seen):
        await resolve(client.chat.completions.create(model="test", messages=[{"role": "user", "content": "message"}],
            metadata={"api_key": "body-placeholder", "visible": "original",
                      "nested": [{"password": "nested-placeholder", "visible": "original"}]},
            extra_headers={"Authorization": "Bearer header-placeholder", "X-Visible": "original",
                           "X-AgentCC-Config": '{"virtual_key":"config-placeholder"}'}))
    request = capture.requests[0]
    assert request.body["metadata"]["api_key"] == "body-placeholder"
    assert request.headers["Authorization"] == "Bearer header-placeholder"
    assert "config-placeholder" in request.headers["X-AgentCC-Config"]
    assert request.body["metadata"]["nested"][0]["password"] == "nested-placeholder"
    assert request.body["messages"][0]["content"] == ("[REDACTED]" if redact else "message")
    wire = json.loads(seen[0].content)
    assert wire["metadata"]["api_key"] == "body-placeholder"
    assert wire["metadata"]["nested"][0]["password"] == "nested-placeholder"
    assert wire["metadata"]["visible"] == "updated"
    assert wire["metadata"]["nested"][0]["visible"] == "updated"
    assert wire["messages"][0]["content"] == "message"
    assert seen[0].headers["authorization"] == "Bearer header-placeholder"
    assert seen[0].headers["x-visible"] == "updated"


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
async def test_published_redaction_copies_only_the_top_level(async_mode, redact):
    # Message redaction detached top-level fields and messages; nested values were shared.
    class Mutate(CallbackHandler):
        def on_request_start(self, request):
            request.body["temperature"] = 1.0
            request.body["messages"][0]["name"] = "edited"
            request.body["metadata"]["visible"] = "updated"
            request.body["metadata"]["nested"][0]["visible"] = "updated"
            request.body["stop"].append("added")

    async with client_for(async_mode, callbacks=[Mutate()], redact_messages=redact) as (client, seen):
        await resolve(client.chat.completions.create(model="test", stop=["end"],
            messages=[{"role": "user", "content": "message"}],
            metadata={"visible": "original", "nested": [{"visible": "original"}]}))
    wire = json.loads(seen[0].content)
    assert wire["metadata"] == {"visible": "updated", "nested": [{"visible": "updated"}]}
    assert wire["stop"] == ["end", "added"]
    assert wire["messages"] == [{"role": "user", "content": "message", **({} if redact else {"name": "edited"})}]
    assert ("temperature" in wire) is not redact


@pytest.mark.parametrize("async_mode", [False, True])
async def test_snapshot_expanded_events_and_metrics_are_explicit_opt_ins(async_mode, tmp_path):
    capture, metrics = Capture(), MetricsCallback(count_tokens=True)
    recorder = RequestRecorder(str(tmp_path / "compact.json"), format="compact")

    class Mutate(CallbackHandler):
        def on_request_start(self, request):
            request.body["model"] = "not-sent"
            request.headers["X-Detached"] = "not-sent"

    async with client_for(async_mode, callbacks=[capture, metrics, recorder, Mutate()],
                          callback_mode="snapshot", expanded_callback_events=True) as (parent, seen):
        client = parent.with_options()
        with client.session():
            await call_resource(client, "chat")
        await call_resource(client, "speech")
    assert capture.requests[0].url == "https://gateway.example.test/v1/chat/completions"
    assert capture.requests[0].files is None
    assert json.loads(seen[0].content)["model"] == "test"
    assert "x-detached" not in seen[0].headers
    assert capture.events[:7] == ["session_start", "start", "end", "cache", "cost", "fallback", "session_end"]
    assert metrics.total_tokens == 5
    assert "agentcc" not in capture.responses[0].body
    assert "agentcc" not in recorder.recordings[0]["response"]["body"]
    assert recorder.recordings[1]["response"] == {"status_code": 201, "body": {"bytes": 5}}


@pytest.mark.parametrize("async_mode", [False, True])
async def test_body_replacement_and_nested_deletion_write_through(async_mode):
    class Mutate(CallbackHandler):
        def on_request_start(self, request):
            del request.body["metadata"]["delete"]
            request.body["messages"].append({"role": "user", "content": "added"})
            request.body = {**request.body, "model": "replacement"}

    async with client_for(async_mode, callbacks=[Mutate()]) as (client, seen):
        await resolve(client.chat.completions.create(model="test", messages=[], metadata={"delete": "value"}))
    body = json.loads(seen[0].content)
    assert body["metadata"] == {}
    assert body["messages"] == [{"role": "user", "content": "added"}]
    assert body["model"] == "replacement"
