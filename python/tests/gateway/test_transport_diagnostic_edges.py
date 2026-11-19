"""Offline regressions for cache-hit reads and built-in exception diagnostics."""
import inspect
import traceback
from types import SimpleNamespace

import httpx
import pytest

import fi.gateway as gw
from fi.gateway._transport._scrub import scrub_error_text

KEY = "synthetic-diagnostic-credential"
PRIVATE = "synthetic-diagnostic-private-header"


def diagnostic_text(error):
    """Capture diagnostics now, including buffer contents hidden by their repr."""
    rows = ["".join(traceback.format_exception(type(error), error, error.__traceback__))]
    pending, seen = [error], set()
    while pending:
        value = pending.pop()
        if value is None or id(value) in seen:
            continue
        seen.add(id(value))
        rows.extend((str(value), repr(value)))
        if isinstance(value, BaseException):
            pending.extend((value.args, value.__cause__, value.__context__, vars(value)))
            pending.extend(getattr(value, "exceptions", ()))
        elif isinstance(value, (httpx.Request, httpx.Response)):
            pending.append(dict(value.headers))
            if isinstance(value, httpx.Response):
                pending.extend((value._request, value.next_request, *value.history))
        elif isinstance(value, dict):
            pending.extend(value)
            pending.extend(value.values())
        elif isinstance(value, (tuple, list, set, frozenset)):
            pending.extend(value)
        elif isinstance(value, (bytearray, memoryview)):
            rows.append(repr(bytes(value)))
    return "\n".join(rows)


def assert_clean(text):
    assert KEY not in text
    assert PRIVATE not in text


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


async def failing_call(handler, async_mode, expanded, *, streaming=False, endpoint="chat"):
    callbacks, snapshots, starts = [], [], []

    def on_error(request, error):
        callbacks.append(error)
        snapshots.append(diagnostic_text(error))

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(handler))
    client = (gw.AsyncAgentCC if async_mode else gw.AgentCC)(
        api_key=KEY, base_url="https://gateway.test", default_headers={"x-private": PRIVATE},
        http_client=http, max_retries=0, expanded_callback_events=expanded,
        callbacks=[SimpleNamespace(on_error=on_error, on_stream_start=lambda *args: starts.append(args))],
    )
    try:
        with pytest.raises(gw.AgentCCError) as caught:
            if endpoint == "responses":
                result = await resolve(client.responses.create(model="fixture", input="fixture", stream=streaming))
            elif endpoint == "completions":
                result = await resolve(client.completions.create(model="fixture", prompt="fixture", stream=streaming))
            else:
                result = await resolve(client.chat.completions.create(model="fixture", messages=[], stream=streaming))
            if streaming:
                if async_mode:
                    async for _ in result:
                        pass
                else:
                    for _ in result:
                        pass
    finally:
        await resolve(client.aclose() if async_mode else client.close())
        await resolve(http.aclose() if async_mode else http.close())
    error = caught.value
    assert len(callbacks) == len(snapshots) == 1
    assert callbacks[0] is error
    assert_clean(snapshots[0])
    assert_clean(diagnostic_text(error))
    return error, starts


@pytest.mark.parametrize("endpoint,async_mode", [
    ("chat", False), ("chat", True), ("completions", False), ("responses", False),
], ids=["chat-sync", "chat-async", "completions-sync", "responses-sync"])
@pytest.mark.parametrize("expanded", [False, True], ids=["published", "expanded"])
@pytest.mark.parametrize("cache_hit", [False, True], ids=["sse", "json-cache"])
async def test_stream_body_diagnostics_are_credential_free(async_mode, expanded, cache_hit, endpoint, caplog):
    requests, responses, originals, closes = [], [], [], []

    class Body(httpx.SyncByteStream, httpx.AsyncByteStream):
        def __iter__(self):
            assert requests[0].headers["authorization"] == "[REDACTED]"
            assert requests[0].headers["x-private"] == "[REDACTED]"
            original = httpx.ReadTimeout("late body authorization=Bearer " + KEY + "; private=" + PRIVATE,
                                         request=requests[0])
            originals.append(original)
            raise original
            yield b""  # pragma: no cover

        async def __aiter__(self):
            for chunk in self:
                yield chunk

        def close(self):
            closes.append("close")

        async def aclose(self):
            self.close()

    def handler(request):
        requests.append(request)
        response = httpx.Response(200, headers={
            "content-type": "application/json" if cache_hit else "text/event-stream",
            "x-agentcc-dispatched": "true",
        }, stream=Body())
        responses.append(response)
        return response

    error, starts = await failing_call(handler, async_mode, expanded, streaming=True, endpoint=endpoint)
    assert len(requests) == len(originals) == len(responses) == len(closes) == 1
    assert type(originals[0]) is httpx.ReadTimeout
    assert originals[0].request is requests[0]
    assert responses[0].is_closed
    assert error.dispatched is True
    assert error.gateway_evidence is responses[0].extensions["fi.gateway_evidence"]
    if cache_hit and not async_mode:
        # Synchronous JSON bodies are consumed during stream construction. Keep
        # that eager failure and the original timeout, as at the send boundary.
        assert type(error) is gw.APITimeoutError
        assert error.__cause__ is originals[0]
        assert_clean(diagnostic_text(originals[0]))
        assert starts == []
    else:
        # Iteration failures retain the published StreamError callback contract;
        # async JSON must not become eager merely to fix sync construction.
        assert type(error) is gw.StreamError
        # Preserve the original diagnostic, but never its credential values.
        assert error.__cause__ is originals[0]
        assert error.__context__ is originals[0] or error.__context__ is None
        assert_clean(diagnostic_text(originals[0]))
        assert len(starts) == 1
    assert_clean(caplog.text)


def payload(kind):
    if kind == "set":
        return {KEY, PRIVATE.encode(), (KEY.encode(), PRIVATE)}
    if kind == "frozenset":
        return frozenset((KEY, PRIVATE.encode(), (KEY.encode(), PRIVATE)))
    data = bytearray((KEY + ";" + PRIVATE).encode())
    return data if kind == "bytearray" else memoryview(data)


def payload_contents(value):
    return bytes(value) if isinstance(value, (bytearray, memoryview)) else set(value)


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("expanded", [False, True], ids=["published", "expanded"])
@pytest.mark.parametrize("kind", ["set", "frozenset", "bytearray", "memoryview"])
async def test_container_cause_diagnostics_are_credential_free(async_mode, expanded, kind, caplog):
    requests, originals = [], []
    caller_value = payload(kind)
    before = payload_contents(caller_value)

    def handler(request):
        requests.append(request)
        inner = ValueError(caller_value)
        outer = httpx.ConnectError("transport failed", request=request)
        originals.extend((outer, inner))
        raise outer from inner

    error, starts = await failing_call(handler, async_mode, expanded)
    assert len(requests) == 1
    assert starts == []
    assert error.__cause__ is originals[0]
    assert originals[0].__cause__ is originals[1]
    assert originals[0].request is requests[0]
    assert type(originals[0]) is httpx.ConnectError
    assert type(originals[1]) is ValueError
    assert type(originals[1].args[0]) is type(caller_value)
    assert originals[1].args[0] is not caller_value
    assert payload_contents(caller_value) == before
    if isinstance(caller_value, memoryview):
        assert bytes(caller_value.obj) == before
        assert originals[1].args[0].obj is not caller_value.obj
    assert_clean(caplog.text)


@pytest.mark.parametrize("kind", ["set", "frozenset", "bytearray", "memoryview"])
def test_nested_diagnostic_aliases_are_copied_not_mutated(kind):
    caller_value = payload(kind)
    before = payload_contents(caller_value)
    shared = {"value": caller_value, "alias": caller_value}
    cycle = [shared]
    cycle.append(cycle)
    error = ValueError(caller_value, shared, cycle)
    error.diagnostic = shared
    original = error
    scrub_error_text(error, (KEY.encode(), PRIVATE.encode()))
    assert error is original and type(error) is ValueError
    assert type(error.args[0]) is type(caller_value)
    assert error.args[0] is not caller_value
    assert error.args[1] is error.diagnostic
    assert error.args[1]["value"] is error.args[1]["alias"] is error.args[0]
    assert error.args[2][0] is error.args[1]
    assert error.args[2][1] is error.args[2]
    assert shared["value"] is shared["alias"] is caller_value
    assert cycle[0] is shared and cycle[1] is cycle
    assert payload_contents(caller_value) == before
    assert_clean(diagnostic_text(error))


@pytest.mark.parametrize("layout", ["readonly", "writable", "strided", "typed"])
def test_memoryview_diagnostics_use_detached_buffers(layout):
    data = (KEY + ";" + PRIVATE).encode()
    if layout == "readonly":
        view = memoryview(data)
    elif layout == "writable":
        view = memoryview(bytearray(data))
    elif layout == "strided":
        view = memoryview(bytearray(b"".join(bytes((b, 0)) for b in data)))[::2]
    else:
        view = memoryview(bytearray(data.ljust((len(data) + 3) // 4 * 4, b" "))).cast("I")
    before, backing = view.tobytes(), bytes(view.obj)
    error = ValueError(view)
    scrub_error_text(error, (KEY.encode(), PRIVATE.encode()))
    cleaned = error.args[0]
    assert type(cleaned) is memoryview
    assert cleaned is not view and cleaned.obj is not view.obj
    assert cleaned.readonly is view.readonly
    assert view.tobytes() == before and bytes(view.obj) == backing
    assert_clean(diagnostic_text(error))


def test_readonly_buffer_diagnostics_remain_hashable():
    view = memoryview(KEY.encode())
    caller_value = {view: frozenset((view, PRIVATE))}
    error = ValueError(caller_value)
    scrub_error_text(error, (KEY.encode(), PRIVATE.encode()))
    cleaned_key = next(iter(error.args[0]))
    assert type(cleaned_key) is memoryview
    assert cleaned_key in error.args[0][cleaned_key]
    assert caller_value == {view: frozenset((view, PRIVATE))}
    assert view.tobytes() == KEY.encode()
    assert_clean(diagnostic_text(error))


def test_released_memoryview_diagnostic_does_not_mask_transport_error():
    view = memoryview(KEY.encode())
    view.release()
    error = ValueError(view, KEY)
    scrub_error_text(error, (KEY.encode(),))
    assert type(error) is ValueError
    assert error.args[0] is view
    assert error.args[1] == "[REDACTED]"
