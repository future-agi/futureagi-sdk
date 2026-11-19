"""Stored HTTPX data is reachable without invoking caller code or unbounded discovery."""
import inspect
from collections import deque
from types import SimpleNamespace

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway._transport import _scrub

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
ORIGIN = "https://gateway.example.test"
KEY = "synthetic-stored-request"
MASK = "[REDACTED]"
CHAT = {"id": "reply", "object": "chat.completion", "created": 0, "model": "fixture", "choices": []}


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


def fresh_request():
    return httpx.Request("GET", ORIGIN, headers={"Authorization": "Bearer " + KEY,
                                               "X-Private": "synthetic-default"})


@pytest.mark.parametrize("holder", ["request", "response", "headers"])
@pytest.mark.parametrize("location", ["attribute", "extension", "stream", "slot"])
def test_httpx_stored_data_is_not_terminal(holder, location):
    class SlotRequest(httpx.Request):
        __slots__ = ("diagnostic",)

    class SlotResponse(httpx.Response):
        __slots__ = ("diagnostic",)

    class SlotHeaders(httpx.Headers):
        __slots__ = ("diagnostic",)

    held = fresh_request()
    if holder == "request":
        root = SlotRequest("GET", ORIGIN)
    elif holder == "response":
        root = SlotResponse(200, headers={"X-Private": "gateway-value", "Set-Cookie": "synthetic-cookie"})
    else:
        root = SlotHeaders({"Authorization": "synthetic-key"})
    diagnostic = SimpleNamespace(request=held)
    if location == "extension":
        root.extensions = {"diagnostic": diagnostic}
    elif location == "stream":
        class Stream(httpx.SyncByteStream):
            def __iter__(self):
                pytest.fail("scrubbing must not consume a stream")
        root.stream = Stream()
        root.stream.diagnostic = diagnostic
    elif location == "slot":
        root.diagnostic = diagnostic
    else:
        root.custom = diagnostic
    _scrub.scrub_reachable([root], frozenset({"x-private"}))
    assert held.headers["authorization"] == MASK
    assert held.headers["x-private"] == MASK
    if holder == "response":
        assert root.headers["x-private"] == "gateway-value"
        assert root.headers["set-cookie"] == MASK


@pytest.mark.anyio
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("snapshot", [False, True])
@pytest.mark.parametrize("location", ["attribute", "extension"])
async def test_original_auth_exchange_inside_response_data(asynchronous, snapshot, location):
    first, sent, wire, callbacks = [], [], [], []

    class Auth(httpx.Auth):
        def auth_flow(self, request):
            first.append((yield request))
            yield httpx.Request(request.method, request.url, headers=request.headers, content=request.content)

    class Capture:
        def on_error(self, request, error):
            response = error.__cause__.diagnostic
            original = response.auth_response if location == "attribute" else response.extensions["auth_response"]
            callbacks.append(original.request.headers["authorization"])

    def serve(request):
        sent.append(request)
        wire.append(request.headers["authorization"])
        if len(sent) == 1:
            return httpx.Response(401)
        response = httpx.Response(502, request=request)
        if location == "attribute":
            response.auth_response = first[0]
        else:
            response.extensions["auth_response"] = first[0]
        error = httpx.ConnectError("offline", request=request)
        error.diagnostic = response
        raise error

    http = (httpx.AsyncClient if asynchronous else httpx.Client)(
        auth=Auth(), transport=httpx.MockTransport(serve), trust_env=False)
    sdk = (AsyncAgentCC if asynchronous else AgentCC)(api_key=KEY, base_url=ORIGIN, http_client=http,
        max_retries=0, callbacks=[Capture()], callback_mode="snapshot" if snapshot else "published")
    try:
        with pytest.raises(Exception) as caught:
            await resolve(sdk.chat.completions.create(model="fixture", messages=[]))
        assert first[0].request is sent[0]
        assert caught.value.__cause__.diagnostic.request is sent[1]
        assert wire == ["Bearer " + KEY] * 2
        assert callbacks == [MASK]
        assert all(request.headers["authorization"] == MASK for request in sent)
    finally:
        await resolve(http.aclose() if asynchronous else http.close())


@pytest.mark.anyio
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("snapshot", [False, True])
async def test_auth_in_error_args_retains_requests_not_live_credentials(asynchronous, snapshot):
    wire, originals = [], []
    config = {"Authorization": "synthetic-caller-configuration"}

    class Auth(httpx.Auth):
        def auth_flow(self, request):
            self.last_response = yield request
            self.last_request = request
            self.config = config
            error = RuntimeError(self)
            originals.append(error)
            raise error

    def serve(request):
        wire.append(dict(request.headers))
        return httpx.Response(200, json=CHAT)

    auth = Auth()
    http = (httpx.AsyncClient if asynchronous else httpx.Client)(
        auth=auth, transport=httpx.MockTransport(serve), trust_env=False)
    sdk = (AsyncAgentCC if asynchronous else AgentCC)(api_key=KEY, base_url=ORIGIN, http_client=http,
        max_retries=0, callback_mode="snapshot" if snapshot else "published")
    try:
        with pytest.raises(RuntimeError) as caught:
            await resolve(sdk.chat.completions.create(model="fixture", messages=[]))
        assert caught.value is originals[0] and caught.value.args[0] is auth
        assert caught.value.__traceback__ is not None
        assert wire[0]["authorization"] == "Bearer " + KEY
        assert auth.last_request.headers["authorization"] == MASK
        assert auth.last_response.request is auth.last_request
        assert config == {"Authorization": "synthetic-caller-configuration"}
    finally:
        await resolve(http.aclose() if asynchronous else http.close())


@pytest.mark.parametrize("kind", ["client", "transport", "auth"])
def test_live_object_stored_data_without_calling_methods(kind):
    class Client(httpx.Client):
        def request(self, *args, **kwargs):
            pytest.fail("walker called request")

    class Transport(httpx.BaseTransport):
        def handle_request(self, request):
            pytest.fail("walker called transport")

    root = Client(trust_env=False) if kind == "client" else Transport() if kind == "transport" else httpx.Auth()
    request = fresh_request()
    root.last_request = request
    root.config = {"Authorization": "synthetic-caller-configuration"}
    try:
        _scrub.scrub_reachable([RuntimeError(root)])
        assert request.headers["authorization"] == MASK
        assert root.config == {"Authorization": "synthetic-caller-configuration"}
    finally:
        if kind == "client":
            httpx.Client.close(root)


@pytest.mark.parametrize("base", [list, tuple, set, frozenset, deque, dict])
@pytest.mark.parametrize("error_class", [RuntimeError, BaseException])
def test_container_overrides_are_never_executed(base, error_class):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise error_class("caller code was invoked")

    class Diagnostic(base):
        __iter__ = __getitem__ = __getattr__ = keys = items = values = forbidden

    member, attribute = fresh_request(), fresh_request()
    diagnostic = Diagnostic({"request": member} if base is dict else [member])
    diagnostic.request = attribute
    _scrub.scrub_reachable([diagnostic])
    assert calls == []
    assert member.headers["authorization"] == attribute.headers["authorization"] == MASK


@pytest.mark.anyio
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("error_class", [RuntimeError, BaseException])
async def test_inspection_cannot_replace_original_transport_error(asynchronous, error_class):
    originals, calls = [], []

    class Diagnostic(list):
        def __iter__(self):
            calls.append(True)
            raise error_class("unexpected iteration")

    def serve(request):
        diagnostic = Diagnostic()
        diagnostic.request = request
        error = RuntimeError(diagnostic)
        originals.append(error)
        raise error

    http = (httpx.AsyncClient if asynchronous else httpx.Client)(transport=httpx.MockTransport(serve), trust_env=False)
    sdk = (AsyncAgentCC if asynchronous else AgentCC)(api_key=KEY, base_url=ORIGIN, http_client=http, max_retries=0)
    caught = None
    try:
        try:
            await resolve(sdk.chat.completions.create(model="fixture", messages=[]))
        except BaseException as error:
            caught = error
        assert caught is originals[0]
        assert caught.args[0].request.headers["authorization"] == MASK
        assert calls == [] and caught.__traceback__ is not None
    finally:
        await resolve(http.aclose() if asynchronous else http.close())


def test_properties_class_spoofing_and_attribute_hooks_are_never_executed():
    calls = []

    def forbidden(*args):
        calls.append(True)
        raise BaseException("unexpected descriptor")

    class Diagnostic:
        __slots__ = ("request",)
        __dict__ = __class__ = property(forbidden)
        __getattr__ = forbidden

        def __getattribute__(self, name):
            return forbidden()

    diagnostic = Diagnostic()
    request = fresh_request()
    Diagnostic.request.__set__(diagnostic, request)
    _scrub.scrub_reachable([diagnostic])
    assert request.headers["authorization"] == MASK
    assert calls == []


def test_httpx_header_and_exception_overrides_are_not_called():
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise BaseException("unexpected override")

    class Headers(httpx.Headers):
        keys = get_list = __setitem__ = forbidden

    class Error(RuntimeError):
        args = __cause__ = __context__ = property(forbidden)

    request = fresh_request()
    request.headers = Headers(request.headers)
    error = Error(request)
    _scrub.scrub_reachable([error])
    assert request.headers["authorization"] == MASK
    assert calls == []


def test_inspection_errors_are_recorded_and_other_nodes_still_scrubbed():
    class Unset:
        __slots__ = ("request",)

    request = fresh_request()
    report = _scrub.scrub_reachable([Unset(), request])
    assert request.headers["authorization"] == MASK
    assert getattr(report, "inspection_errors", 0) >= 1


@pytest.mark.parametrize("location", ["attributes", "slots", "sequence", "mapping"])
def test_wide_discovery_charges_before_collecting_children(location, monkeypatch):
    monkeypatch.setattr(_scrub, "SCAN_CAP", 7)
    if location == "attributes":
        root = SimpleNamespace(**{f"a{i}": SimpleNamespace() for i in range(1000)})
    elif location == "slots":
        cls = type("Wide", (), {"__slots__": tuple(f"a{i}" for i in range(1000))})
        root = cls()
        for i in range(1000):
            setattr(root, f"a{i}", SimpleNamespace())
    elif location == "mapping":
        root = {i: SimpleNamespace() for i in range(1000)}
    else:
        root = [SimpleNamespace() for _ in range(1000)]
    walk = _scrub._Walk()
    children = walk.children(root)
    assert len(children) <= 7
    assert walk.scanned <= 7
    assert walk.report.node_capped


def test_pending_frontier_and_duplicates_are_bounded(monkeypatch):
    monkeypatch.setattr(_scrub, "NODE_CAP", 7)
    walk = _scrub._Walk()
    values = [SimpleNamespace() for _ in range(1000)]
    for item in values:
        walk.offer(item, 0)
        walk.offer(item, 0)
    assert len(walk.queue) <= 7
    assert walk.report.node_capped


def test_scan_cap_stops_discovery_but_scrubs_previously_found_requests(monkeypatch):
    request = fresh_request()
    wide = SimpleNamespace(**{f"a{i}": SimpleNamespace() for i in range(1000)})
    monkeypatch.setattr(_scrub, "SCAN_CAP", 7)
    report = _scrub.scrub_reachable([wide, request])
    assert report.node_capped
    assert request.headers["authorization"] == MASK


def test_native_slot_and_class_inspection_ignores_all_class_overrides():
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise BaseException("unexpected class inspection")

    class Meta(type):
        __getattribute__ = __hash__ = __eq__ = forbidden

    class Base(metaclass=Meta):
        __slots__ = ("__request",)

    class Diagnostic(Base):
        __slots__ = ("other",)

    root = Diagnostic()
    first, second = fresh_request(), fresh_request()
    object.__setattr__(root, "_Base__request", first)
    object.__setattr__(root, "other", second)
    # A replaced declaration must not affect the native storage layout.
    type.__setattr__(Diagnostic, "__slots__", SimpleNamespace(__iter__=forbidden))
    _scrub.scrub_reachable([root])
    assert first.headers["authorization"] == second.headers["authorization"] == MASK
    assert calls == []


def test_scalar_subclass_stored_attributes_are_data():
    class Label(str):
        pass

    root = Label("diagnostic")
    root.request = fresh_request()
    _scrub.scrub_reachable([root])
    assert root.request.headers["authorization"] == MASK


def test_native_header_storage_masks_duplicates_without_calling_overrides():
    headers = httpx.Headers([(b"Authorization", b"synthetic-first"),
                             (b"authorization", b"synthetic-second"),
                             (b"X-Visible", b"visible"),
                             (b"x-visible", b"still-visible")])
    _scrub.scrub_reachable([headers])
    assert headers.get_list("authorization") == [MASK]
    assert headers.get_list("x-visible") == ["visible", "still-visible"]


@pytest.mark.parametrize("limit", [1, 3, 7])
def test_node_cap_drains_all_admitted_requests(limit, monkeypatch):
    monkeypatch.setattr(_scrub, "NODE_CAP", limit)
    requests = [fresh_request() for _ in range(12)]
    report = _scrub.scrub_reachable(requests)
    assert report.node_capped and report.visited == limit
    assert report.pending_peak <= limit
    assert all(request.headers["authorization"] == MASK for request in requests[:limit])
    assert requests[limit].headers["authorization"] == "Bearer " + KEY


def test_header_provenance_survives_early_alias_discovery():
    response = httpx.Response(200, headers={"X-Private": "gateway-value", "Set-Cookie": "synthetic-cookie"})
    request = fresh_request()
    request.custom = response
    _scrub.scrub_reachable([response.headers, request], frozenset({"x-private"}))
    assert response.headers["x-private"] == "gateway-value"
    assert response.headers["set-cookie"] == MASK
    assert request.headers["x-private"] == MASK
