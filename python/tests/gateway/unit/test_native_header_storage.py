"""Offline regressions for native storage names and bounded target admission."""
import inspect
from types import SimpleNamespace

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway._transport import _scrub

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
ORIGIN = "https://gateway.example.test"
KEY = "synthetic-storage-key"
PRIVATE = "synthetic-client-default"
MASK = "[REDACTED]"
CHAT = {"id": "reply", "object": "chat.completion", "created": 0, "model": "fixture", "choices": []}


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


class AttributeName(str):
    pass


def rename_storage(headers):
    state = vars(headers)
    key = AttributeName("_list")
    headers.__dict__ = {key: state["_list"], **{k: v for k, v in state.items() if k != "_list"}}
    assert next(iter(vars(headers))) is key
    return key


@pytest.mark.parametrize("root_kind", ["request", "response", "headers"])
def test_str_subclass_native_storage_name_is_scrubbed(root_kind):
    headers = httpx.Headers({"Authorization": "Bearer " + KEY, "X-Private": PRIVATE})
    key = rename_storage(headers)
    if root_kind == "request":
        root = httpx.Request("GET", ORIGIN)
        root.headers = headers
    elif root_kind == "response":
        root = httpx.Response(200)
        root.headers = headers
    else:
        root = headers
    report = _scrub.scrub_reachable([RuntimeError(SimpleNamespace(payload=root))], frozenset({"x-private"}))
    assert not report.node_capped and not report.depth_capped
    assert not report.inspection_errors
    assert next(iter(vars(headers))) is key
    assert headers["authorization"] == MASK
    assert headers["x-private"] == (PRIVATE if root_kind == "response" else MASK)


@pytest.mark.anyio
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("snapshot", [False, True])
async def test_success_callback_cannot_reach_subclass_named_storage(asynchronous, snapshot):
    held, wire, observed = [], [], []

    def inject(response):
        headers = response.request.headers
        rename_storage(headers)
        held.append(headers)
        return response

    class SyncClient(httpx.Client):
        def request(self, *args, **kwargs):
            return inject(super().request(*args, **kwargs))

    class AsyncClient(httpx.AsyncClient):
        async def request(self, *args, **kwargs):
            return inject(await super().request(*args, **kwargs))

    class Capture:
        def on_request_end(self, request, response):
            observed.append(response.agentcc.http_response.request.headers["authorization"])

    def serve(request):
        wire.append(dict(request.headers))
        return httpx.Response(200, json=CHAT)

    defaults = {"X-Private": PRIVATE}
    http = (AsyncClient if asynchronous else SyncClient)(transport=httpx.MockTransport(serve), trust_env=False)
    sdk = (AsyncAgentCC if asynchronous else AgentCC)(api_key=KEY, base_url=ORIGIN, http_client=http,
        default_headers=defaults, max_retries=0, callbacks=[Capture()],
        callback_mode="snapshot" if snapshot else "published")
    try:
        result = await resolve(sdk.chat.completions.create(model="fixture", messages=[]))
        assert wire[0]["authorization"] == "Bearer " + KEY
        assert wire[0]["x-private"] == PRIVATE
        assert observed == [MASK]
        assert result.agentcc.http_response.request.headers["authorization"] == MASK
        assert held[0]["x-private"] == MASK
        assert defaults == {"X-Private": PRIVATE}
    finally:
        await resolve(http.aclose() if asynchronous else http.close())


@pytest.mark.parametrize("field", ["headers", "_list"])
def test_native_storage_string_coercion_never_executes_caller_hooks(field):
    calls = []
    armed = [False]

    class Name(str):
        def __getattribute__(self, name):
            if armed[0]:
                calls.append("getattribute")
                raise AssertionError("caller attribute hook")
            return super().__getattribute__(name)

        def __hash__(self):
            if armed[0]:
                calls.append("hash")
                raise AssertionError("caller hash")
            return str.__hash__(self)

        def __eq__(self, other):
            if armed[0]:
                calls.append("eq")
                raise AssertionError("caller equality")
            return str.__eq__(self, other)

        def __str__(self):
            calls.append("str")
            raise AssertionError("caller string conversion")

        def __iter__(self):
            calls.append("iter")
            raise AssertionError("caller iteration")

        def __len__(self):
            calls.append("len")
            raise AssertionError("caller length")

        def __getitem__(self, item):
            calls.append("getitem")
            raise AssertionError("caller item access")

    request = httpx.Request("GET", ORIGIN, headers={"Authorization": "Bearer " + KEY})
    headers = request.headers
    rows = headers._list
    owner = request if field == "headers" else headers
    state = vars(owner)
    key = Name(field)
    owner.__dict__ = {key: state[field], **{k: v for k, v in state.items() if k != field}}
    armed[0] = True
    try:
        report = _scrub.scrub_reachable([request])
        assert calls == []
        assert not report.inspection_errors
        assert next(iter(vars(owner))) is key
        assert next(row[2] for row in rows if row[1] == b"authorization") == b"[REDACTED]"
    finally:
        armed[0] = False


@pytest.mark.parametrize("width", [8, 64, 512])
def test_native_field_instance_dictionary_reads_fit_budget(width, monkeypatch):
    request = httpx.Request("GET", ORIGIN, headers={"Authorization": "Bearer " + KEY})
    request.__dict__ = {**{f"padding_{i}": None for i in range(width)}, **vars(request)}
    native = _scrub._named
    reads = []
    source = inspect.getsource(native)
    assert source.count("for key, value in entries:") == 1
    source = source.replace("for key, value in entries:", "for key, value in track(entries):")

    def track(entries):
        for entry in entries:
            reads.append(1)
            yield entry

    namespace = dict(native.__globals__, track=track)
    exec(compile(source, "<counted-native-field-scans>", "exec"), namespace)
    monkeypatch.setattr(_scrub, "_named", namespace["_named"])
    monkeypatch.setattr(_scrub, "SCAN_CAP", 2)
    walk = _scrub._Walk()
    walk.run([request])
    walk.mask(frozenset())
    assert len(reads) <= walk.report.scanned <= 2
    assert walk.report.node_capped
    assert id(request) not in walk.seen
    assert not walk.header_rows and not walk.sent


def test_unresolved_header_storage_is_not_silently_admitted():
    headers = httpx.Headers({"Authorization": "Bearer " + KEY})
    del headers.__dict__["_list"]
    walk = _scrub._Walk()
    walk.run([headers])
    walk.mask(frozenset())
    assert id(headers) not in walk.seen
    assert id(headers) not in walk.sent
    assert walk.report.inspection_errors


@pytest.mark.parametrize("root_kind", ["request", "response", "headers"])
@pytest.mark.parametrize("limit", [1, 2, 4, 8, 16])
def test_storage_must_be_captured_before_target_admission(root_kind, limit, monkeypatch):
    headers = httpx.Headers({"Authorization": "Bearer " + KEY})
    rename_storage(headers)
    headers.__dict__ = {**{f"padding_{i}": None for i in range(8)}, **vars(headers)}
    root = headers if root_kind == "headers" else (
        httpx.Request("GET", ORIGIN) if root_kind == "request" else httpx.Response(200))
    if root is not headers:
        root.headers = headers
    monkeypatch.setattr(_scrub, "SCAN_CAP", limit)
    walk = _scrub._Walk()
    walk.run([root])
    scanned = walk.report.scanned

    def forbidden(*args, **kwargs):
        pytest.fail("masking may not rediscover native fields")

    monkeypatch.setattr(_scrub, "_named", forbidden)
    monkeypatch.setattr(_scrub, "_data_attribute", forbidden)
    walk.mask(frozenset())
    assert not walk.report.inspection_errors
    assert walk.report.scanned == scanned <= limit
    if id(root) in walk.seen:
        assert id(headers) in walk.header_rows
        assert headers["authorization"] == MASK
    else:
        assert walk.report.node_capped
        assert id(headers) not in walk.sent and id(headers) not in walk.received
    if limit == 16:
        assert id(root) in walk.seen


@pytest.mark.parametrize("root_kind", ["request", "response", "headers"])
def test_captured_rows_fully_mask_when_later_target_exhausts_budget(root_kind, monkeypatch):
    pairs = [("Authorization", "Bearer " + KEY)]
    pairs += [(f"X-Private-{index}", PRIVATE) for index in range(64)]
    headers = httpx.Headers(pairs)
    rename_storage(headers)
    root = headers if root_kind == "headers" else (
        httpx.Request("GET", ORIGIN) if root_kind == "request" else httpx.Response(200))
    if root is not headers:
        root.headers = headers
    later = httpx.Headers({"Authorization": "Bearer " + KEY})
    later.__dict__ = {**{f"padding_{i}": None for i in range(64)}, **vars(later)}
    walk = _scrub._Walk()
    walk.offer(root, 0)
    assert id(root) in walk.seen
    admitted_scans = walk.report.scanned
    assert admitted_scans > 0
    monkeypatch.setattr(_scrub, "SCAN_CAP", admitted_scans + 2)
    walk.run([later])
    assert walk.report.node_capped and id(later) not in walk.seen
    assert walk.report.scanned == admitted_scans + 2
    scans = walk.report.scanned

    def forbidden(*args, **kwargs):
        pytest.fail("captured targets need no field discovery after exhaustion")

    monkeypatch.setattr(_scrub, "_named", forbidden)
    monkeypatch.setattr(_scrub, "_data_attribute", forbidden)
    walk.mask(frozenset(f"x-private-{index}" for index in range(64)))
    assert walk.report.scanned == scans
    assert not walk.report.inspection_errors
    assert headers["authorization"] == MASK
    assert all(headers[f"x-private-{index}"] == (PRIVATE if root_kind == "response" else MASK)
               for index in range(64))
