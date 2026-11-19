"""Pin the released async stream callback-to-wire contract and explicit opt-in."""

import inspect
import json

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, APIStatusError, StreamError
from fi.gateway.callbacks.base import CallbackHandler

pytestmark = [pytest.mark.anyio, pytest.mark.filterwarnings("ignore::DeprecationWarning")]


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


def stream_frame(resource):
    if resource == "responses":
        return {"type": "response.output_text.delta", "delta": "synthetic text"}
    return {
        "id": "synthetic-result", "object": "text_completion" if resource == "completions" else "chat.completion.chunk",
        "created": 0, "model": "synthetic", "choices": [{"index": 0, "finish_reason": "stop",
            **({"text": "synthetic text"} if resource == "completions" else {"delta": {"content": "synthetic text"}})}],
    }


async def capture(resource, async_mode, redact, *, options=None, finish="consume"):
    events, sent, responses, reads, callback_errors = [], [], [], [], []
    frame = stream_frame(resource)

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            events.append("start")
            try:
                request.body["callback_marker"] = "synthetic edit"
            except Exception as exc:
                callback_errors.append(type(exc).__name__)

        def on_stream_start(self, *args):
            events.append("stream_start")

        def on_stream_chunk(self, *args):
            events.append("chunk")

        def on_stream_end(self, *args):
            events.append("stream_end")

        def on_request_end(self, *args):
            events.append("end")

        def on_error(self, *args):
            events.append("error")

    class DeferredBody(httpx.SyncByteStream, httpx.AsyncByteStream):
        def __iter__(self):
            reads.append(dict(responses[0].request.headers))
            yield ("data: " + json.dumps(frame) + "\n\n").encode()
            if finish == "late_error":
                yield b'data: {"type":"error","error":{"message":"synthetic failure"}}\n\n'
            yield b"data: [DONE]\n\n"

        async def __aiter__(self):
            for part in self:
                yield part

    def serve(request):
        sent.append({"body": request.content, "headers": dict(request.headers), "path": request.url.path})
        if finish == "send_error":
            response = httpx.Response(400, json={"error": {"message": "synthetic failure"}})
        else:
            response = httpx.Response(200, headers={"content-type": "text/event-stream"}, stream=DeferredBody())
        responses.append(response)
        return response

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve))
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key="synthetic-stream-key", base_url="https://gateway.example.test", http_client=http,
        callbacks=[Edit()], redact_messages=redact, max_retries=0, **(options or {}),
    )
    stream = None
    chunks, before_consume = [], []
    stream_type = None
    try:
        target = client.chat.completions if resource == "chat" else getattr(client, resource)
        argument = {"chat": {"messages": []}, "completions": {"prompt": "synthetic prompt"},
                    "responses": {"input": "synthetic input"}}[resource]
        if finish == "send_error":
            with pytest.raises(APIStatusError):
                await resolve(target.create(model="synthetic", stream=True, **argument))
        else:
            stream = await resolve(target.create(model="synthetic", stream=True, **argument))
            stream_type = type(stream).__name__
            before_consume = list(events)
            assert not reads and not responses[0].is_stream_consumed

            async def consume():
                if async_mode:
                    async for chunk in stream:
                        chunks.append(chunk.model_dump(exclude_none=True))
                else:
                    chunks.extend(chunk.model_dump(exclude_none=True) for chunk in stream)

            if finish == "late_error":
                with pytest.raises(StreamError):
                    await consume()
            elif finish == "consume":
                await consume()
            await resolve(stream.aclose() if async_mode else stream.close())
        assert not callback_errors
        return {"events": events, "before_consume": before_consume, "sent": sent, "reads": reads,
                "retained_headers": dict(responses[0].request.headers), "closed": responses[0].is_closed,
                "chunks": chunks, "stream_type": stream_type, "frame": frame}
    finally:
        if stream is not None:
            await resolve(stream.aclose() if async_mode else stream.close())
        await resolve(http.aclose() if async_mode else http.close())


def assert_wire(record, resource, edited):
    expected = {"model": "synthetic"}
    if resource == "responses":
        expected.update(input="synthetic input", store=True, stream=True)
    elif resource == "completions":
        expected.update(prompt="synthetic prompt", stream=True)
    else:
        expected.update(messages=[], stream=True)
    if edited:
        expected["callback_marker"] = "synthetic edit"
    assert len(record["sent"]) == 1
    wire = record["sent"][0]
    assert wire["headers"]["content-type"] == "application/json"
    assert wire["body"] == json.dumps(expected, separators=(",", ":")).encode()
    assert wire["path"] == ("/v1/chat/completions" if resource == "chat" else "/v1/" + resource)


@pytest.mark.parametrize("resource", ["chat", "completions", "responses"])
@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
async def test_published_stream_callback_to_wire(resource, async_mode, redact):
    # These expectations are executable against the released 0.7.0 source too:
    # do not pass new callback options to the published constructor.
    result = await capture(resource, async_mode, redact)
    enabled = not async_mode or resource == "chat"
    assert_wire(result, resource, enabled and not redact)
    assert result["before_consume"] == (["start", "stream_start"] if enabled else [])
    assert result["events"] == (["start", "stream_start", "chunk", "stream_end", "end"] if enabled else [])
    assert len(result["chunks"]) == 1
    for key, value in result["frame"].items():
        assert result["chunks"][0][key] == value
    # The response parser's concrete wrapper class is not the callback contract.
    # Keep the typed chunk assertions above for both published and current parsers.
    assert result["closed"]


@pytest.mark.parametrize("resource", ["chat", "completions", "responses"])
@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("callback_mode", ["published", "snapshot"])
@pytest.mark.parametrize("expanded", [False, True])
async def test_expanded_stream_callbacks_require_explicit_event_opt_in(resource, async_mode, redact, callback_mode, expanded):
    result = await capture(resource, async_mode, redact, options={
        "callback_mode": callback_mode, "expanded_callback_events": expanded,
    })
    enabled = not async_mode or resource == "chat" or expanded
    assert_wire(result, resource, enabled and not redact and callback_mode == "published")
    assert result["before_consume"] == (["start", "stream_start"] if enabled else [])
    assert result["events"] == (["start", "stream_start", "chunk", "stream_end", "end"] if enabled else [])
    assert len(result["chunks"]) == 1 and result["closed"]
    assert result["sent"][0]["headers"]["authorization"] == "Bearer synthetic-stream-key"
    assert result["retained_headers"]["authorization"] == "[REDACTED]"
    assert len(result["reads"]) == 1 and result["reads"][0]["authorization"] == "[REDACTED]"


@pytest.mark.parametrize("resource", ["completions", "responses"])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("finish", ["close", "send_error", "late_error"])
async def test_published_async_stream_terminal_paths_have_no_callbacks(resource, redact, finish):
    result = await capture(resource, True, redact, finish=finish)
    assert_wire(result, resource, False)
    assert result["events"] == []
    assert result["closed"]


@pytest.mark.parametrize("resource", ["completions", "responses"])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("callback_mode", ["published", "snapshot"])
@pytest.mark.parametrize("finish", ["close", "send_error", "late_error"])
async def test_expanded_async_stream_terminal_callbacks_and_scrub(resource, redact, callback_mode, finish):
    result = await capture(resource, True, redact, finish=finish, options={
        "callback_mode": callback_mode, "expanded_callback_events": True,
    })
    expected = {"close": ["start", "stream_start", "stream_end", "end"],
                "send_error": ["start", "error"],
                "late_error": ["start", "stream_start", "chunk", "error"]}[finish]
    assert result["events"] == expected
    assert_wire(result, resource, not redact and callback_mode == "published")
    assert result["retained_headers"]["authorization"] == "[REDACTED]"
    assert result["closed"]
