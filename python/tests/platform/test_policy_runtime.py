"""The generated operation table, read by the platform core's own executor (no network).

The core (``fi._core``) looks every platform operation up in ``fi.generated.platform.policy`` by SDK
name. These tests use the generated table as a client does: every operation goes through
``PlatformCore`` over ``httpx.MockTransport`` and must build the method and path the contract gives,
send an ``Idempotency-Key`` exactly when the contract makes it idempotent, and carry the retry class the
contract implies. The table is also checked field by field against the core's dataclass annotations,
so a reshaped ``OperationSpec`` fails here before any client does.
"""

from __future__ import annotations

import ast
import dataclasses
import typing

import httpx
from fi._core.origins import PlatformOrigin
from fi._core.platform_base import PlatformCore
from fi._core.policy import (
    OperationSpec,
    PaginationSpec,
    StreamSpec,
    counts,
    lookup,
    retry_class_of,
)
from fi._core.transport import PlatformShared

from ._feature_scope import (
    HTTP_IDEMPOTENT_COUNT,
    OPERATION_COUNT,
    PAGINATED_COUNT,
    assert_credential_scope,
)
from ._gates_support import REPO, SCOPED, read_json, routes, spec_retry_class

BASE = "http://127.0.0.1:9/omega/api"
POLICY_SOURCE = REPO / "python" / "fi" / "generated" / "platform" / "policy.py"
CALLS = {"Op": OperationSpec, "Stream": StreamSpec, "Page": PaginationSpec}


def _matches(value: typing.Any, hint: typing.Any) -> bool:
    origin, args = typing.get_origin(hint), typing.get_args(hint)
    if hint is typing.Any:
        return True
    if origin is typing.Literal:
        return value in args
    if origin is typing.Union:
        return any(_matches(value, arg) for arg in args)
    if origin is tuple:
        return isinstance(value, tuple) and all(_matches(v, args[0]) for v in value)
    if hint is type(None):
        return value is None
    if dataclasses.is_dataclass(hint):
        return isinstance(value, hint) and not _mismatches(value)
    if hint in (bool, int):
        return type(value) is hint
    return isinstance(value, hint)


def _mismatches(value: typing.Any) -> list[str]:
    """The fields of a core dataclass whose value is not of the annotated type."""
    hints = typing.get_type_hints(type(value))
    return [
        f"{f.name}={getattr(value, f.name)!r}"
        for f in dataclasses.fields(value)
        if not _matches(getattr(value, f.name), hints[f.name])
    ]


def test_the_table_is_the_cores_own_type_field_by_field() -> None:
    from fi.generated.platform.policy import EXTRAS, OPERATIONS

    assert len(OPERATIONS) == OPERATION_COUNT
    assert_credential_scope(OPERATIONS)
    for name, op in OPERATIONS.items():
        assert type(op) is OperationSpec, name
        assert op.name == name
        assert _mismatches(op) == [], name
    assert set(EXTRAS) <= set(OPERATIONS)


def test_the_emitter_writes_every_field_of_the_cores_dataclasses() -> None:
    """A field the core adds (or renames) must be a conscious change to the emitter."""
    tree = ast.parse(POLICY_SOURCE.read_text(encoding="utf-8"))
    seen = {name: 0 for name in CALLS}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            cls = CALLS.get(node.func.id)
            if cls is None:
                continue
            seen[node.func.id] += 1
            written = [k.arg for k in node.keywords]
            assert not node.args, node.func.id
            assert written == [f.name for f in dataclasses.fields(cls)], node.func.id
    assert seen == {"Op": OPERATION_COUNT, "Stream": 2, "Page": PAGINATED_COUNT}
    assert_credential_scope(read_json(REPO / "openapi/platform/scope.json")["operations"])


def test_the_core_derives_the_contracts_retry_class_for_every_operation() -> None:
    from fi.generated.platform.policy import OPERATIONS

    spec = routes(read_json(SCOPED))
    assert sorted(spec) == sorted(OPERATIONS)
    assert_credential_scope(OPERATIONS)
    for name, (method, _route, op) in spec.items():
        assert retry_class_of(lookup(OPERATIONS, name)) == spec_retry_class(
            method, op
        ), name
    assert counts(OPERATIONS) == {
        "keyed": 13,
        "keyed-not-durable": 3,
        "http-idempotent": HTTP_IDEMPOTENT_COUNT,
        "unsafe": 6,
        "stream": 2,
        "paginated": PAGINATED_COUNT,
    }


class _Server:
    """Answers every request with an empty success (an SSE response for a stream) and records it."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.headers.get("accept") == "text/event-stream":
            return httpx.Response(
                200, content=b": ok\n\n", headers={"content-type": "text/event-stream"}
            )
        return httpx.Response(200, json={})


def _core(server: _Server) -> PlatformCore:
    origin = PlatformOrigin(
        httpx.URL(BASE),
        "keys",
        "derived",
        {"X-Api-Key": "k-test-1234", "X-Secret-Key": "s-test-1234"},
        ("k-test-1234", "s-test-1234"),
    )
    # table=None: the core loads fi.generated.platform.policy itself, as a client's first call does
    shared = PlatformShared(
        lambda: origin,
        retries=0,
        table=None,
        transport=httpx.MockTransport(server),
        sleep=lambda _seconds: None,
    )
    return PlatformCore(shared)


def test_the_core_calls_every_operation_from_the_generated_table() -> None:
    server = _Server()
    core = _core(server)
    for name, (method, route, op) in routes(read_json(SCOPED)).items():
        spec = core.operation(name)
        path = {
            p: "dir/file.txt" if p in spec.multi_segment else f"v-{p}"
            for p in spec.path_params
        }
        body: typing.Any = None
        if spec.body != "none":
            body = b"x" if spec.content_type == "application/octet-stream" else {}
        before = len(server.requests)
        if spec.stream is None:
            core.call(name, path=path, body=body)
        else:
            core.open_stream(name, path=path, body=body).response.close()
        assert len(server.requests) == before + 1, name
        request = server.requests[-1]
        expected = route
        for key, value in path.items():
            expected = expected.replace("{" + key + "}", value)
        assert (request.method, request.url.path) == (method, "/omega/api" + expected)
        keyed = op.get("x-omega-idempotent") is True
        assert ("idempotency-key" in request.headers) is keyed, name
        assert request.extensions["fi.retry"]["class"] == spec_retry_class(method, op)
    assert len(server.requests) == OPERATION_COUNT
    assert_credential_scope(routes(read_json(SCOPED)))
