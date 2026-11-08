"""Offline regressions for safe keyed reads, key data and late stream errors."""
import inspect
from types import SimpleNamespace

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway._transport import _scrub

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
ORIGIN = "https://gateway.example.test"
KEY = "synthetic-inspection-key"
MASK = "[REDACTED]"
CHAT = {"id": "reply", "object": "chat.completion", "created": 0, "model": "fixture", "choices": []}


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


@pytest.mark.anyio
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("snapshot", [False, True])
@pytest.mark.parametrize("throwing", [False, True])
async def test_keyed_reads_never_execute_caller_equality(asynchronous, snapshot, throwing):
    calls, wire, headers, observed = [], [], [], []
    armed = [False]

    class CollidingKey:
        def __hash__(self):
            return hash("headers")

        def __eq__(self, other):
            if armed[0]:
                calls.append(True)
                if throwing:
                    raise RuntimeError("caller equality during inspection")
            return False

    def inject(response):
        request = response.request
        state = vars(request).copy()
        headers.append(state["headers"])
        request.__dict__ = {CollidingKey(): None, **state}
        armed[0] = True
        return response

    class SyncClient(httpx.Client):
        def request(self, *args, **kwargs):
            return inject(super().request(*args, **kwargs))

    class AsyncClient(httpx.AsyncClient):
        async def request(self, *args, **kwargs):
            return inject(await super().request(*args, **kwargs))

    class Capture:
        def on_request_end(self, *args):
            observed.append(headers[0]["authorization"])

    def serve(request):
        wire.append(request.headers["authorization"])
        return httpx.Response(200, json=CHAT)

    http = (AsyncClient if asynchronous else SyncClient)(transport=httpx.MockTransport(serve), trust_env=False)
    sdk = (AsyncAgentCC if asynchronous else AgentCC)(api_key=KEY, base_url=ORIGIN, http_client=http,
        callbacks=[Capture()], max_retries=0, callback_mode="snapshot" if snapshot else "published")
    try:
        result = error = None
        try:
            result = await resolve(sdk.chat.completions.create(model="fixture", messages=[]))
        except Exception as exc:
            error = exc
        assert wire == ["Bearer " + KEY]
        assert calls == []
        assert error is None and result is not None
        assert observed == [MASK]
        assert headers[0]["authorization"] == MASK
    finally:
        armed[0] = False
        await resolve(http.aclose() if asynchronous else http.close())


@pytest.mark.parametrize("name", ["__dict__", "headers", "_list"])
def test_class_namespace_reads_ignore_non_exact_string_keys(name):
    calls = []
    armed = [False]

    class Key(str):
        def __hash__(self):
            return hash(name)

        def __eq__(self, other):
            if armed[0]:
                calls.append(True)
                raise RuntimeError("caller class key equality")
            return False

    cls = type("Diagnostic", (httpx.Request,), {Key("diagnostic"): None})
    request = cls("GET", ORIGIN, headers={"Authorization": "Bearer " + KEY})
    headers = request.headers
    armed[0] = True
    try:
        _scrub.scrub_reachable([request])
        assert calls == []
        assert headers["authorization"] == MASK
    finally:
        armed[0] = False


@pytest.mark.anyio
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("snapshot", [False, True])
async def test_instance_dictionary_keys_are_data(asynchronous, snapshot):
    wire, originals, keys, dictionaries = [], [], [], []

    class AttributeName(str):
        pass

    def serve(request):
        wire.append(request.headers["authorization"])
        name = AttributeName("diagnostic")
        name.request = request
        holder = SimpleNamespace()
        setattr(holder, name, None)
        assert next(iter(holder.__dict__)) is name
        keys.append(name)
        dictionaries.append(holder.__dict__)
        error = RuntimeError(holder)
        originals.append(error)
        raise error

    http = (httpx.AsyncClient if asynchronous else httpx.Client)(transport=httpx.MockTransport(serve), trust_env=False)
    sdk = (AsyncAgentCC if asynchronous else AgentCC)(api_key=KEY, base_url=ORIGIN, http_client=http,
        max_retries=0, callback_mode="snapshot" if snapshot else "published")
    try:
        with pytest.raises(RuntimeError) as caught:
            await resolve(sdk.chat.completions.create(model="fixture", messages=[]))
        assert caught.value is originals[0] and caught.value.__traceback__ is not None
        assert caught.value.args[0].__dict__ is dictionaries[0]
        assert list(dict.items(dictionaries[0])) == [(keys[0], None)]
        assert wire == ["Bearer " + KEY]
        assert keys[0].request.headers["authorization"] == MASK
    finally:
        await resolve(http.aclose() if asynchronous else http.close())


@pytest.mark.anyio
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("snapshot", [False, True])
@pytest.mark.parametrize("resource", ["chat", "completions", "responses"])
async def test_late_stream_errors_scrub_newly_reachable_auth_request(asynchronous, snapshot, resource):
    middle, wire, observed, originals, late = [], [], [], [], []

    class Auth(httpx.Auth):
        def auth_flow(self, request):
            yield request
            retained = httpx.Request(request.method, request.url, headers=request.headers, content=request.content)
            middle.append((yield retained))
            yield httpx.Request(request.method, request.url, headers=request.headers, content=request.content)

    class Capture:
        def on_error(self, request, error):
            diagnostic = error.__cause__.__cause__.args[0]
            observed.append((dict(diagnostic.request.headers), dict(diagnostic.late_request.headers)))

    def serve(request):
        wire.append(dict(request.headers))
        if len(wire) < 3:
            return httpx.Response(401)
        retained = middle[0].request

        def fail():
            # Keep a genuinely late graph edge even though per-exchange capture
            # now masks every actual auth request before the stream is returned.
            late.append(httpx.Request(retained.method, retained.url, headers=wire[1]))
            original = RuntimeError(SimpleNamespace(request=retained, late_request=late[-1]))
            error = ValueError("late body failure")
            error.__cause__ = original
            originals.append(error)
            raise error

        class SyncBody(httpx.SyncByteStream):
            def __iter__(self):
                fail()
                yield b""

        class AsyncBody(httpx.AsyncByteStream):
            async def __aiter__(self):
                fail()
                yield b""

        return httpx.Response(200, stream=(AsyncBody if asynchronous else SyncBody)(),
                              headers={"content-type": "text/event-stream"})

    class SyncClient(httpx.Client):
        def send(self, *args, **kwargs):
            response = super().send(*args, **kwargs)
            response.history.clear()
            return response

    class AsyncClient(httpx.AsyncClient):
        async def send(self, *args, **kwargs):
            response = await super().send(*args, **kwargs)
            response.history.clear()
            return response

    defaults = {"X-Client-Private": "synthetic-client-value"}
    extras = {"X-Caller": "caller-visible"}
    http = (AsyncClient if asynchronous else SyncClient)(transport=httpx.MockTransport(serve), auth=Auth(), trust_env=False)
    sdk = (AsyncAgentCC if asynchronous else AgentCC)(api_key=KEY, base_url=ORIGIN, http_client=http,
        max_retries=0, default_headers=defaults, callbacks=[Capture()], expanded_callback_events=True,
        callback_mode="snapshot" if snapshot else "published")
    try:
        endpoint = sdk.chat.completions if resource == "chat" else getattr(sdk, resource)
        body = {"messages": []} if resource == "chat" else {"prompt": "hello"} if resource == "completions" else {"input": "hello"}
        stream = await resolve(endpoint.create(model="fixture", stream=True, extra_headers=extras, **body))
        assert stream.response.history == []
        # Every actual exchange is captured without closure/frame traversal.
        assert middle[0].request.headers["authorization"] == MASK
        assert stream.response.request.headers["authorization"] == MASK
        # The late walk must use this exchange's name set, not current client state.
        sdk._default_headers = {}
        sdk._get_base_client()._default_headers = {}
        with pytest.raises(Exception) as caught:
            if asynchronous:
                async for _ in stream:
                    pass
            else:
                list(stream)
        assert caught.value.__cause__ is originals[0]
        assert originals[0].__traceback__ is not None
        assert len(wire) == 3
        assert all(row["authorization"] == "Bearer " + KEY for row in wire)
        assert all(row["x-client-private"] == "synthetic-client-value" for row in wire)
        assert len(observed) == 1
        assert len(late) == 1
        for row in (*observed[0], middle[0].request.headers, late[0].headers):
            assert row["authorization"] == row["x-client-private"] == MASK
            assert row["x-caller"] == "caller-visible"
        assert defaults == {"X-Client-Private": "synthetic-client-value"}
        assert extras == {"X-Caller": "caller-visible"}
    finally:
        await resolve(http.aclose() if asynchronous else http.close())


def test_native_mro_namespace_reads_share_discovery_budget(monkeypatch):
    reads = []
    original = _scrub._class_dicts

    def tracked(value):
        for namespace in original(value):
            reads.append(1)
            yield namespace

    monkeypatch.setattr(_scrub, "_class_dicts", tracked)
    monkeypatch.setattr(_scrub, "SCAN_CAP", 2)
    cls = type("Root", (), {"__slots__": ()})
    for index in range(40):
        cls = type("Layer" + str(index), (cls,), {"__slots__": ()})
    report = _scrub.scrub_reachable([cls()])
    assert len(reads) <= 2
    assert report.scanned <= 2 and report.node_capped


@pytest.mark.parametrize("limit", [1, 2, 7])
def test_admitted_httpx_targets_mask_after_discovery_exhaustion(limit, monkeypatch):
    request = httpx.Request("GET", ORIGIN, headers={"Authorization": "Bearer " + KEY,
                                                  "X-Private": "synthetic-default"})
    response = httpx.Response(200, headers={"Set-Cookie": "synthetic-cookie", "X-Private": "gateway-value"})
    headers = httpx.Headers({"Authorization": "Bearer " + KEY})
    reads = []
    original = _scrub._class_dicts

    def tracked(value):
        for namespace in original(value):
            reads.append(1)
            yield namespace

    monkeypatch.setattr(_scrub, "_class_dicts", tracked)
    walk = _scrub._Walk()
    for target in (request, response, headers):
        walk.offer(target, 0)
        assert id(target) in walk.seen
    # Admission now charges native instance fields too. Exhaust only the
    # remaining budget, after proving these targets were actually captured.
    admitted_scans = walk.report.scanned
    monkeypatch.setattr(_scrub, "SCAN_CAP", admitted_scans + limit)
    walk.run([])
    walk.mask(frozenset({"x-private"}))
    assert walk.report.scanned <= admitted_scans + limit
    assert len(reads) <= limit
    assert walk.report.node_capped
    assert request.headers["authorization"] == request.headers["x-private"] == MASK
    assert headers["authorization"] == response.headers["set-cookie"] == MASK
    assert response.headers["x-private"] == "gateway-value"


def test_failed_header_field_does_not_skip_other_stored_children(monkeypatch):
    request = httpx.Request("GET", ORIGIN, headers={"Authorization": "Bearer " + KEY})
    nested = httpx.Request("GET", ORIGIN, headers={"Authorization": "Bearer " + KEY})
    request.diagnostic = nested
    original = _scrub._data_attribute

    def fail_one_field(value, name, report):
        if value is request and name == "headers":
            raise RuntimeError("one unreadable field")
        return original(value, name, report)

    monkeypatch.setattr(_scrub, "_data_attribute", fail_one_field)
    report = _scrub.scrub_reachable([request])
    assert report.inspection_errors == 1
    assert request.headers["authorization"] == nested.headers["authorization"] == MASK


@pytest.mark.parametrize("kind", ["request", "response", "headers"])
def test_discovered_native_storage_slots_need_no_masking_namespace_reads(kind, monkeypatch):
    class Request(httpx.Request):
        __slots__ = ("headers",)

    class Response(httpx.Response):
        __slots__ = ("headers",)

    class Headers(httpx.Headers):
        __slots__ = ("_list",)

    if kind == "headers":
        root = headers = Headers({"Authorization": "Bearer " + KEY, "X-Private": "synthetic-default"})
    else:
        root = Request("GET", ORIGIN) if kind == "request" else Response(200)
        root.headers = headers = Headers({"Authorization": "Bearer " + KEY, "X-Private": "synthetic-default"})
    walk = _scrub._Walk()
    walk.run([root])

    def forbidden(value):
        pytest.fail("masking must not discover native metadata")

    monkeypatch.setattr(_scrub, "_class_dicts", forbidden)
    walk.report.node_capped = True
    walk.mask(frozenset({"x-private"}))
    assert headers["authorization"] == MASK
    assert headers["x-private"] == ("synthetic-default" if kind == "response" else MASK)


@pytest.mark.parametrize("kind", ["request", "response", "headers"])
@pytest.mark.parametrize("limit", [2, 7, 500])
def test_native_slot_storage_is_resolved_before_target_admission(kind, limit, monkeypatch):
    class Headers(httpx.Headers):
        __slots__ = ("_list",)

    headers = Headers({"Authorization": "Bearer " + KEY})
    root = headers if kind == "headers" else httpx.Request("GET", ORIGIN) if kind == "request" else httpx.Response(200)
    if root is not headers:
        root.headers = headers
    reads = []
    original = _scrub._class_dicts

    def tracked(value):
        for namespace in original(value):
            reads.append(1)
            yield namespace

    monkeypatch.setattr(_scrub, "_class_dicts", tracked)
    monkeypatch.setattr(_scrub, "SCAN_CAP", limit)
    walk = _scrub._Walk()
    walk.run([root])
    walk.mask(frozenset())
    assert len(reads) <= walk.report.scanned <= limit
    if id(root) in walk.seen:
        assert headers["authorization"] == MASK
    else:
        assert walk.report.node_capped
    if limit == 500:
        assert id(root) in walk.seen
