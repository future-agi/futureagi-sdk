"""Every httpx request reachable from returned, raised or callback objects is scrubbed.

The guarantee covers data attributes only: exception args, ``__dict__``/``__slots__``
values, ``__cause__``/``__context__``, exception-group children, ``__notes__``,
containers, ``Response.request``/``history`` and ``Headers``. Interpreter introspection
(frames, tracebacks, closures, gc) is outside it, and tracebacks are never cleared.
"""
import builtins
import inspect
import sys
import types
from types import SimpleNamespace

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway._gateway_config import GatewayConfig
from fi.gateway._transport import _scrub

pytestmark = [pytest.mark.anyio, pytest.mark.filterwarnings("ignore::DeprecationWarning")]
ORIGIN = "https://gateway.example.test"
KEY = "synthetic-reach-key"
DEFAULT = "synthetic-reach-default"
CONFIG = "synthetic-reach-config"
SESSION = "synthetic-reach-session"
META = "synthetic-reach-metadata"
SECRETS = (KEY, DEFAULT, CONFIG, SESSION, META)
MASK = "[REDACTED]"
CHAT = {"id": "reply", "object": "chat.completion", "created": 0, "model": "fixture", "choices": []}
HAS_GROUPS = hasattr(builtins, "ExceptionGroup")

_LEAVES = (str, bytes, bytearray, memoryview)
_NOT_DATA = (type, types.ModuleType, types.FunctionType, types.MethodType,
             types.BuiltinFunctionType, types.GeneratorType, types.CoroutineType,
             types.AsyncGeneratorType, types.FrameType, types.TracebackType)


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


def reachable(root, limit=50000):
    """Independent value-aware walk over stored data; returns paths holding a secret.

    No globals, closures, frames, tracebacks or gc. Headers are read through their
    stored raw list so a masked header can never be mistaken for a live one.
    """
    stack, seen, hits = [("$", root)], set(), []
    while stack:
        path, value = stack.pop()
        if isinstance(value, _LEAVES):
            text = value if isinstance(value, str) else bytes(value).decode("utf-8", "replace")
            hits.extend(path for secret in SECRETS if secret in text)
            continue
        if value is None or isinstance(value, (bool, int, float, complex, *_NOT_DATA)):
            continue
        if id(value) in seen:
            continue
        seen.add(id(value))
        assert len(seen) < limit, "reachability walk exceeded its bound"
        if isinstance(value, dict):
            for index, (key, item) in enumerate(value.items()):
                stack.extend(((f"{path}.key[{index}]", key), (f"{path}[{key!r}]", item)))
        elif isinstance(value, (list, tuple, set, frozenset)):
            stack.extend((f"{path}[{i}]", item) for i, item in enumerate(value))
        if isinstance(value, BaseException):
            for name in ("args", "__cause__", "__context__", "exceptions", "__notes__"):
                stack.append((f"{path}.{name}", getattr(value, name, None)))
        try:
            stored = vars(value)
        except TypeError:
            stored = {}
        stack.extend((f"{path}.{name}", item) for name, item in stored.items() if name != "__traceback__")
        for cls in type(value).__mro__:
            slots = cls.__dict__.get("__slots__", ())
            for name in (slots,) if isinstance(slots, str) else slots:
                if name not in {"__dict__", "__weakref__"}:
                    try:
                        stack.append((f"{path}.{name}", getattr(value, name)))
                    except (AttributeError, TypeError):
                        pass
    return hits


def requests_in(root):
    """Every httpx.Request reachable through the same data attributes."""
    stack, seen, found = [root], set(), []
    while stack:
        value = stack.pop()
        if value is None or isinstance(value, (*_LEAVES, bool, int, float, *_NOT_DATA)) or id(value) in seen:
            continue
        seen.add(id(value))
        if isinstance(value, httpx.Request):
            found.append(value)
            continue
        if isinstance(value, dict):
            stack.extend([*value, *value.values()])
        elif isinstance(value, (list, tuple, set, frozenset)):
            stack.extend(value)
        if isinstance(value, BaseException):
            stack.extend((value.args, value.__cause__, value.__context__,
                          getattr(value, "exceptions", ()), getattr(value, "__notes__", ())))
        try:
            stack.extend(vars(value).values())
        except TypeError:
            pass
        for cls in type(value).__mro__:
            slots = cls.__dict__.get("__slots__", ())
            for name in (slots,) if isinstance(slots, str) else slots:
                if name not in {"__dict__", "__weakref__"}:
                    stack.append(getattr(value, name, None))
    return found


class SlotError(Exception):
    __slots__ = ("held",)


class Config(GatewayConfig):
    def to_headers(self):
        return {"X-Reach-Config": CONFIG}


OUTCOMES = [
    "auth_diagnostic", "error_attribute", "args_namespace", "containers", "slots",
    "notes", "chain", "history", "headers_alias", "status_diagnostic",
]
if HAS_GROUPS:
    OUTCOMES.append("group")
FAILING = set(OUTCOMES) - {"history"}


def raise_custom(outcome, request, first):
    if outcome == "auth_diagnostic":
        error = httpx.ConnectError("second auth exchange failed", request=request)
        error.diagnostic = SimpleNamespace(auth_response=first[0])
    elif outcome == "error_attribute":
        error = RuntimeError("custom transport failure")
        error.request = request
    elif outcome == "args_namespace":
        error = RuntimeError(SimpleNamespace(request=request))
    elif outcome == "containers":
        error = RuntimeError("containers")
        error.by_request = {request: "attempt"}
        error.frozen = frozenset({request})
        error.pairs = [("attempt", (request,))]
        error.nested = ({"deep": [request]},)
    elif outcome == "slots":
        error = SlotError("slots")
        error.held = SimpleNamespace(response=httpx.Response(500, request=request))
    elif outcome == "notes":
        error = RuntimeError("notes")
        error.__notes__ = [SimpleNamespace(request=request)]
    elif outcome == "chain":
        inner = RuntimeError("inner")
        inner.request = request
        error = RuntimeError("outer")
        error.__cause__ = RuntimeError("middle")
        error.__cause__.__context__ = inner
    elif outcome == "headers_alias":
        error = RuntimeError("alias")
        error.captured = request.headers
    elif outcome == "status_diagnostic":
        error = RuntimeError("status")
        error.response = httpx.Response(502, request=request)
    else:
        child = RuntimeError("child")
        child.request = request
        error = builtins.ExceptionGroup("grouped", [RuntimeError("other"), child])
    raise error


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("snapshot", [False, True])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("outcome", OUTCOMES)
async def test_requests_reachable_from_results_errors_and_callbacks_are_scrubbed(
    async_mode, snapshot, redact, outcome,
):
    sent, wire, callbacks, immediate, first = [], [], [], [], []

    class Capture:
        def __getattr__(self, name):
            if not name.startswith("on_"):
                raise AttributeError(name)

            def capture(*args):
                callbacks.append((name, args))
                immediate.extend(f"{name}{hit[1:]}" for hit in reachable(args))
            return capture

    class Challenge(httpx.Auth):
        def auth_flow(self, request):
            response = yield request
            first.append(response)
            if response.status_code == 401:
                yield httpx.Request(request.method, request.url, headers=request.headers,
                                    content=request.content)

    uses_auth = outcome in {"auth_diagnostic", "history"}

    def serve(request):
        sent.append(request)
        wire.append(dict(request.headers))
        if uses_auth and len(sent) == 1:
            return httpx.Response(401, json={"error": {"message": "challenge"}})
        if outcome == "history":
            return httpx.Response(200, json=CHAT)
        raise_custom(outcome, request, first)

    http = (httpx.AsyncClient if async_mode else httpx.Client)(
        transport=httpx.MockTransport(serve), trust_env=False, auth=Challenge() if uses_auth else None)
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key=KEY, base_url=ORIGIN, http_client=http, default_headers={"X-Reach-Default": DEFAULT},
        config=Config(), session_id=SESSION, metadata={"private": META}, max_retries=0,
        callback_mode="snapshot" if snapshot else "published", redact_messages=redact,
        callbacks=[Capture()])
    returned = raised = None
    try:
        try:
            returned = await resolve(client.chat.completions.create(model="fixture", messages=[]))
        except Exception as exc:
            raised = exc
        assert (raised is not None) is (outcome in FAILING)
        for headers in wire:
            assert headers["authorization"] == "Bearer " + KEY
            assert headers["x-reach-default"] == DEFAULT
            assert headers["x-reach-config"] == CONFIG
            assert headers["x-agentcc-session-id"] == SESSION
            assert META in headers["x-agentcc-metadata"]
        roots = {"returned": returned, "raised": raised, "callbacks": callbacks}
        assert not immediate, immediate[:4]
        assert not reachable(roots), reachable(roots)[:4]
        names = ("authorization", "x-reach-default", "x-reach-config",
                 "x-agentcc-session-id", "x-agentcc-metadata")
        if outcome == "headers_alias":
            # Only the Headers object is stored, not a Request: the alias itself is masked.
            assert all(raised.captured[name] == MASK for name in names)
            assert not requests_in(roots) or all(
                r.headers[name] == MASK for r in requests_in(roots) for name in names)
        else:
            reached = requests_in(roots)
            assert reached
            for request in reached:
                for name in names:
                    assert request.headers[name] == MASK, name
            # Every exchange of these scenarios is reachable (history or a diagnostic holds
            # the challenge), so none may be left out of the strict check above.
            reached_ids = {id(request) for request in reached}
            assert all(id(request) in reached_ids for request in sent)
        if outcome == "auth_diagnostic":
            # Only SDK-mapped errors reach on_error; the original error is not copied.
            assert [args[1] for name, args in callbacks if name == "on_error"] == [raised]
            assert raised.__cause__.diagnostic.auth_response is first[0]
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("async_mode", [False, True])
async def test_original_error_identity_diagnostics_and_traceback_survive(async_mode):
    first, wire = [], []

    class Challenge(httpx.Auth):
        def auth_flow(self, request):
            response = yield request
            first.append(response)
            yield httpx.Request(request.method, request.url, headers=request.headers,
                                content=request.content)

    def serve(request):
        wire.append(dict(request.headers))
        if len(wire) == 1:
            return httpx.Response(401)
        error = httpx.ConnectError("offline", request=request)
        error.diagnostic = SimpleNamespace(auth_response=first[0])
        raise error

    http = (httpx.AsyncClient if async_mode else httpx.Client)(
        transport=httpx.MockTransport(serve), trust_env=False, auth=Challenge())
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key=KEY, base_url=ORIGIN, http_client=http, max_retries=0)
    try:
        with pytest.raises(Exception) as caught:
            await resolve(client.chat.completions.create(model="fixture", messages=[]))
        original = caught.value.__cause__
        assert isinstance(original, httpx.ConnectError)
        # Identity is preserved: the diagnostic still holds the very first response,
        # now bearing a scrubbed request. Nothing was copied.
        assert original.diagnostic.auth_response is first[0]
        assert first[0].request.headers["authorization"] == MASK
        assert wire[0]["authorization"] == "Bearer " + KEY
        assert original.__traceback__ is not None
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("async_mode", [False, True])
async def test_streaming_send_error_with_reachable_request_is_scrubbed(async_mode):
    sent = []

    def serve(request):
        sent.append(request)
        error = RuntimeError("stream transport failure")
        error.request = request
        raise error

    http = (httpx.AsyncClient if async_mode else httpx.Client)(
        transport=httpx.MockTransport(serve), trust_env=False)
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key=KEY, base_url=ORIGIN, http_client=http, max_retries=0)
    try:
        with pytest.raises(RuntimeError) as caught:
            await resolve(client.chat.completions.create(model="fixture", messages=[], stream=True))
        assert caught.value.request is sent[0]
        assert sent[0].headers["authorization"] == MASK
        assert not reachable(caught.value)
    finally:
        await resolve(http.aclose() if async_mode else http.close())


def fresh_request(**headers):
    return httpx.Request("POST", ORIGIN, headers={
        "Authorization": "Bearer " + KEY, "X-Private": "synthetic-private",
        "X-Visible": "caller-visible", **headers})


def test_the_walk_is_bounded_and_documented():
    assert _scrub.DEPTH_CAP == 12
    assert _scrub.NODE_CAP == 10000


@pytest.mark.parametrize("name", ["X_Api_Key", "Api-Key", "TOKEN", "Secret", "Client_Secret", "Cookie", "X-Goog-Api-Key"])
def test_credential_names_are_matched_case_and_separator_insensitively(name):
    request = fresh_request(**{name: "synthetic-value"})
    _scrub.scrub_reachable([request], frozenset())
    assert request.headers[name] == MASK
    assert request.headers["authorization"] == MASK
    assert request.headers["x-private"] == "synthetic-private"
    assert request.headers["x-visible"] == "caller-visible"


def test_composed_names_are_masked_for_this_exchange_only():
    request = fresh_request()
    _scrub.scrub_reachable([request], frozenset({"x-private"}))
    assert request.headers["x-private"] == MASK and request.headers["x-visible"] == "caller-visible"


def test_a_response_keeps_the_gateway_s_header_even_when_the_name_is_client_composed():
    request = fresh_request()
    response = httpx.Response(200, headers={"X-Private": "gateway-echo", "Set-Cookie": "c"}, request=request)
    _scrub.scrub_reachable([response], frozenset({"x-private"}))
    assert request.headers["x-private"] == MASK
    assert response.headers["x-private"] == "gateway-echo"
    assert response.headers["set-cookie"] == MASK


@pytest.mark.parametrize("async_mode", [False, True])
async def test_gateway_echo_of_a_client_composed_header_name_survives(async_mode):
    sent = []

    def serve(request):
        sent.append(request)
        return httpx.Response(200, json=CHAT, headers={
            "x-agentcc-trace-id": "gateway-trace", "x-agentcc-session-id": "gateway-session"})

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve), trust_env=False)
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key=KEY, base_url=ORIGIN, http_client=http, session_id=SESSION, max_retries=0,
        default_headers={"x-agentcc-trace-id": "client-trace"})
    try:
        result = await resolve(client.chat.completions.create(model="fixture", messages=[]))
        assert sent[0].headers["x-agentcc-trace-id"] == MASK
        assert sent[0].headers["x-agentcc-session-id"] == MASK
        assert result.agentcc.trace_id == "gateway-trace"
        assert result.agentcc.http_response.headers["x-agentcc-session-id"] == "gateway-session"
    finally:
        await resolve(http.aclose() if async_mode else http.close())


def test_response_headers_history_and_next_request_are_followed():
    requests = [fresh_request() for _ in range(3)]
    response = httpx.Response(200, headers={"Set-Cookie": "synthetic-cookie"}, request=requests[0])
    response.history = [httpx.Response(401, request=requests[1])]
    response.next_request = requests[2]
    report = _scrub.scrub_reachable([response], frozenset())
    assert response.headers["set-cookie"] == MASK
    assert all(r.headers["authorization"] == MASK for r in requests)
    assert report.visited >= 4 and not report.node_capped and not report.depth_capped


@pytest.mark.skipif(not HAS_GROUPS, reason="exception groups need Python 3.11")
def test_group_children_notes_slots_and_cycles_terminate_with_identity():
    requests = [fresh_request() for _ in range(3)]
    child = RuntimeError("child")
    child.request = requests[0]
    group = builtins.ExceptionGroup("g", [child, child])
    group.__notes__ = [SimpleNamespace(request=requests[1])]
    slot = SlotError("slot")
    slot.held = requests[2]
    group.slot = slot
    child.__context__ = group  # cycle
    try:
        raise group
    except builtins.ExceptionGroup:
        traceback = group.__traceback__
    _scrub.scrub_reachable([group], frozenset())
    assert all(r.headers["authorization"] == MASK for r in requests)
    assert group.__traceback__ is traceback and group.exceptions[0] is child
    assert child.__context__ is group and slot.held is requests[2]


def test_depth_cap_scrubs_what_was_found_records_a_counter_and_never_raises():
    def nested(depth):
        request = fresh_request()
        node = SimpleNamespace(req=request)
        for _ in range(depth):
            node = SimpleNamespace(inner=node)
        return node, request

    shallow, kept = nested(10)
    deep, skipped = nested(40)
    before = dict(_scrub.CAP_COUNTERS)
    report = _scrub.scrub_reachable([shallow, deep], frozenset())
    assert kept.headers["authorization"] == MASK
    assert skipped.headers["authorization"] == "Bearer " + KEY
    assert report.depth_capped >= 1
    assert _scrub.CAP_COUNTERS["depth"] > before["depth"]


def test_node_cap_scrubs_what_was_found_records_a_counter_and_never_raises():
    first = fresh_request()
    crowd = [SimpleNamespace() for _ in range(_scrub.NODE_CAP + 500)]
    before = dict(_scrub.CAP_COUNTERS)
    report = _scrub.scrub_reachable([first, crowd, fresh_request()], frozenset())
    assert first.headers["authorization"] == MASK
    assert report.node_capped and report.visited <= _scrub.NODE_CAP
    assert _scrub.CAP_COUNTERS["nodes"] > before["nodes"]


def hold_in_closure(request):
    held = request

    def inner():
        return held
    return inner


class HoldsClassAttribute:
    request = None


def paused_generator(request):
    held = request
    yield held


def raise_with_local(request):
    held = request
    raise RuntimeError(held is request)


@pytest.mark.parametrize("hiding_place", ["closure", "class_attribute", "module", "generator", "frame", "traceback", "bound_method", "function_default"])
def test_interpreter_machinery_is_never_followed(hiding_place):
    request = fresh_request()
    if hiding_place == "closure":
        root = [SimpleNamespace(callback=hold_in_closure(request))]
    elif hiding_place == "class_attribute":
        HoldsClassAttribute.request = request
        root = [HoldsClassAttribute(), HoldsClassAttribute]
    elif hiding_place == "module":
        module = types.ModuleType("synthetic_holder")
        module.request = request
        root = [module]
    elif hiding_place == "generator":
        generator = paused_generator(request)
        next(generator)
        root = [generator]
    elif hiding_place == "frame":
        held = request  # noqa: F841  (the frame's local is the hiding place)
        root = [sys._getframe()]
    elif hiding_place == "traceback":
        try:
            raise_with_local(request)
        except RuntimeError as exc:
            root = [exc]
            traceback = exc.__traceback__
    elif hiding_place == "bound_method":
        holder = SimpleNamespace(request=request)
        root = [types.MethodType(lambda self: None, holder)]
    else:
        def with_default(value=request):
            return value
        root = [with_default]
    report = _scrub.scrub_reachable(root, frozenset())
    assert request.headers["authorization"] == "Bearer " + KEY
    if hiding_place == "traceback":
        assert root[0].__traceback__ is traceback and traceback is not None
    assert not report.node_capped and not report.depth_capped


def test_hostile_objects_never_raise_and_caller_data_is_untouched():
    class Boom:
        def __getattr__(self, name):
            raise RuntimeError(name)

        @property
        def __dict__(self):
            raise RuntimeError("dict")

    class Unset:
        __slots__ = ("never_assigned",)

    class BadMapping(dict):
        def items(self):
            raise RuntimeError("items")

        def values(self):
            raise RuntimeError("values")

    caller_headers = {"Authorization": "synthetic-caller-owned"}
    request = fresh_request()
    root = [Boom(), Unset(), BadMapping(a=request), caller_headers, request]
    _scrub.scrub_reachable(root, frozenset())
    assert request.headers["authorization"] == MASK
    assert caller_headers == {"Authorization": "synthetic-caller-owned"}
