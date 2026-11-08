"""Credential-bearing transport diagnostics stay safe without replacing causes."""
import builtins
import traceback
from types import SimpleNamespace

import h11
import httpx
import pytest

import fi.gateway as gw

KEY = "synthetic-transport-text-credential"
PRIVATE = "synthetic-private-header-value"


def assert_clean(error):
    rendered = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    assert KEY not in rendered and PRIVATE not in rendered
    pending, seen = [error], set()
    while pending:
        value = pending.pop()
        if value is None or id(value) in seen:
            continue
        seen.add(id(value))
        text = str(value) + repr(value)
        assert KEY not in text and PRIVATE not in text
        if isinstance(value, BaseException):
            pending.extend((value.args, value.__cause__, value.__context__, vars(value)))
            pending.extend(getattr(value, "exceptions", ()))
            for name in ("message", "strerror", "filename", "__notes__"):
                pending.append(getattr(value, name, None))
        elif isinstance(value, (httpx.Request, httpx.Response)):
            pending.append(dict(value.headers))
            if isinstance(value, httpx.Response):
                pending.extend((value._request, value.next_request, *value.history))
        elif isinstance(value, dict):
            pending.extend(value)
            pending.extend(value.values())
        elif isinstance(value, (list, tuple)):
            pending.extend(value)


async def failing_call(handler, async_mode, expanded, *, key=KEY, streaming=False, http_type=None, preflight=False):
    callbacks, snapshots = [], []

    def on_error(request, error):
        callbacks.append(error)
        # Capture text at callback time, not only after the SDK has raised it.
        snapshots.append("".join(traceback.format_exception(type(error), error, error.__traceback__)))

    kwargs = dict(api_key=key, base_url="https://gateway.test", max_retries=0,
                  default_headers={"x-private": PRIVATE},
                  expanded_callback_events=expanded,
                  callbacks=[SimpleNamespace(on_error=on_error)])
    if async_mode:
        async with (http_type or httpx.AsyncClient)(transport=httpx.MockTransport(handler)) as http:
            async with gw.AsyncAgentCC(http_client=http, **kwargs) as client:
                with pytest.raises(gw.AgentCCError if preflight else gw.APIConnectionError) as caught:
                    await client.chat.completions.create(model="fixture", messages=[], stream=streaming)
    else:
        with (http_type or httpx.Client)(transport=httpx.MockTransport(handler)) as http:
            with gw.AgentCC(http_client=http, **kwargs) as client:
                with pytest.raises(gw.AgentCCError if preflight else gw.APIConnectionError) as caught:
                    client.chat.completions.create(model="fixture", messages=[], stream=streaming)
    error = caught.value
    if preflight:
        assert type(error) is gw.AgentCCError
        assert str(error) == "Invalid HTTP header value for authorization."
    assert callbacks == [error] and callbacks[0] is error
    assert len(snapshots) == 1
    assert KEY not in snapshots[0] and PRIVATE not in snapshots[0]
    assert_clean(error)
    return error


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("expanded", [False, True], ids=["published", "expanded"])
@pytest.mark.parametrize("protocol", [False, True], ids=["diagnostic", "h11-invalid-header"])
async def test_preserved_transport_text_is_credential_free(async_mode, expanded, protocol):
    requests, originals, inner_errors = [], [], []
    key = KEY

    def handler(request):
        requests.append(request)
        assert request.headers["authorization"] == "Bearer " + key
        if protocol:
            # Inject malformed data at the transport, after SDK preflight. This
            # still exercises actual h11 diagnostics with the composed key.
            request.headers['authorization'] += '\nsynthetic-suffix'
            try:
                # Actual HTTP/1.1 header validation, without opening a socket.
                h11.Request(method=request.method, target=request.url.raw_path, headers=request.headers.raw)
            except h11.LocalProtocolError as inner:
                inner_errors.append(inner)
                original = httpx.LocalProtocolError(str(inner), request=request)
                originals.append(original)
                raise original from inner
            raise AssertionError("expected h11 to reject the malformed header")
        original = httpx.ConnectError("diagnostic authorization=" + request.headers["authorization"],
                                      request=request)
        originals.append(original)
        raise original

    if protocol:
        await failing_call(handler, async_mode, expanded, key=KEY + '\nsynthetic-suffix', preflight=True)
        assert requests == originals == inner_errors == []
    error = await failing_call(handler, async_mode, expanded, key=key)
    assert len(requests) == len(originals) == 1
    assert error.__cause__ is originals[0]
    assert type(originals[0]) is (httpx.LocalProtocolError if protocol else httpx.ConnectError)
    assert originals[0].request is requests[0]
    assert requests[0].headers["authorization"] == "[REDACTED]"
    if protocol:
        assert originals[0].__cause__ is inner_errors[0]
        assert originals[0].__context__ is inner_errors[0]
        assert "Illegal header value" in str(inner_errors[0])
    else:
        assert "diagnostic authorization=" in str(originals[0])


class MessageError(Exception):
    def __init__(self, message):
        super().__init__("cached diagnostic")
        self.message = message

    def __str__(self):
        return self.message


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("expanded", [False, True], ids=["published", "expanded"])
@pytest.mark.parametrize("streaming", [False, True], ids=["request", "stream-open"])
async def test_cause_context_groups_and_byte_args_keep_identity(async_mode, expanded, streaming):
    requests, originals, links = [], [], []
    caller_data = {PRIVATE: [PRIVATE.encode(), KEY]}

    def handler(request):
        requests.append(request)
        # Include byte repr escapes, bare keys, cached string attributes, and
        # the separate client-composed header; the group title itself is public.
        diagnostic = ValueError(KEY.encode(), caller_data)
        cached = MessageError("cached " + PRIVATE)
        os_error = OSError(22, "invalid " + KEY, PRIVATE)
        children = [diagnostic, cached, os_error]
        if hasattr(builtins, "ExceptionGroup"):
            inner = builtins.ExceptionGroup("transport diagnostics", children)
        else:
            inner = cached
            cached.__cause__ = diagnostic
            diagnostic.__cause__ = os_error
        context = RuntimeError("context " + KEY)
        outer = httpx.ReadError("authorization=" + request.headers["authorization"], request=request)
        outer.__cause__ = inner
        outer.__context__ = context
        context.__context__ = outer  # A cycle must not lose identity or hang.
        if hasattr(cached, "add_note"):
            cached.add_note("note " + PRIVATE)
        originals.extend([outer, inner, context, *children])
        links.extend((value, value.__cause__, value.__context__) for value in originals)
        raise outer

    error = await failing_call(handler, async_mode, expanded, streaming=streaming)
    assert len(requests) == 1
    assert error.__cause__ is originals[0]
    for original, cause, context in links:
        assert original.__cause__ is cause and original.__context__ is context
        assert_clean(original)
    assert caller_data == {PRIVATE: [PRIVATE.encode(), KEY]}
    assert type(originals[0]) is httpx.ReadError
    assert type(originals[-2]) is MessageError
    assert type(originals[-1]) is OSError
    if hasattr(builtins, "ExceptionGroup"):
        assert originals[1].exceptions == tuple(originals[-3:])
        assert all(a is b for a, b in zip(originals[1].exceptions, originals[-3:]))


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("expanded", [False, True], ids=["published", "expanded"])
async def test_composed_values_survive_missing_request_and_escaped_diagnostics(async_mode, expanded):
    requests, originals = [], []
    key = KEY + "\\quoted'\"\tend"

    def handler(request):
        requests.append(request)
        # HTTPX permits a transport error without a request. The original
        # request may also have been masked already by another diagnostic path.
        request.headers["authorization"] = "[REDACTED]"
        original = httpx.ConnectError("bare=" + repr(key.encode()) + "; private=" + PRIVATE)
        originals.append(original)
        raise original

    error = await failing_call(handler, async_mode, expanded, key=key)
    assert len(requests) == 1
    assert error.__cause__ is originals[0]
    assert "bare=" in str(originals[0]) and "; private=" in str(originals[0])


class LazyClient(httpx.Client):
    def request(self, method, url, **kwargs):
        follow_redirects = kwargs.pop("follow_redirects")
        return self.send(self.build_request(method, url, **kwargs), stream=True,
                         follow_redirects=follow_redirects)


class LazyAsyncClient(httpx.AsyncClient):
    async def request(self, method, url, **kwargs):
        follow_redirects = kwargs.pop("follow_redirects")
        return await self.send(self.build_request(method, url, **kwargs), stream=True,
                               follow_redirects=follow_redirects)


@pytest.mark.parametrize("async_mode", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("expanded", [False, True], ids=["published", "expanded"])
async def test_post_send_body_failure_redacts_original_text(async_mode, expanded):
    requests, responses, originals = [], [], []

    class Body(httpx.SyncByteStream, httpx.AsyncByteStream):
        def __iter__(self):
            assert requests[0].headers["authorization"] == "[REDACTED]"
            original = httpx.ReadTimeout("body read " + KEY + " " + PRIVATE, request=requests[0])
            originals.append(original)
            raise original
            yield b""  # pragma: no cover

        async def __aiter__(self):
            for chunk in self:
                yield chunk

    def handler(request):
        requests.append(request)
        response = httpx.Response(200, headers={"x-agentcc-dispatched": "true"}, stream=Body())
        responses.append(response)
        return response

    error = await failing_call(handler, async_mode, expanded,
                               http_type=LazyAsyncClient if async_mode else LazyClient)
    assert len(requests) == len(originals) == 1
    assert error.__cause__ is originals[0]
    assert type(originals[0]) is httpx.ReadTimeout
    assert error.dispatched is True
    assert error.gateway_evidence is responses[0].extensions["fi.gateway_evidence"]
    assert responses[0].is_closed
