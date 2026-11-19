"""Stored exchange graphs retain their identity and mask credentials."""
import builtins
import inspect
import sys
import types
from types import SimpleNamespace
import httpx
import pytest
from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway._transport import _scrub
from ._exchange_scrub_fixtures import (
    ORIGIN, KEY, DEFAULT, CONFIG, SESSION, META, SECRETS, MASK, CHAT, HAS_GROUPS,
    anyio_backend, resolve, reachable, requests_in, SlotError, Config, OUTCOMES, FAILING, raise_custom,
)
pytestmark = [pytest.mark.anyio, pytest.mark.filterwarnings("ignore::DeprecationWarning")]


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
