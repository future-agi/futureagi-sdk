"""Every sandbox operation through ``client.sandboxes`` (sync and async), against the mock server
routed by the frozen scoped OpenAPI: the method named by its ``x-sdk-operation`` (snake_case per
segment), one request, the contract's method and path, the declared query, header and body, and
no retries for operations that permit only one attempt. This is the sandbox rows' oracle; the
generic one in test_operation_contracts.py skips them (see its ``own_oracle``)."""

from __future__ import annotations

import inspect
import json
import re
from urllib.parse import parse_qsl

import pytest
from fi.sandbox import AsyncSandbox, AsyncSandboxes, Sandbox, SandboxError, Sandboxes

from ._gates_support import REPO
from ._sandbox_mock import (
    EXEC,
    MODES,
    SBX,
    SNAP,
    MockServer,
    api,
    collect,
    load_spec,
    resolve,
    routes,
    run,
)

DATA = json.loads((REPO / "tests/fixtures/contracts/operations.json").read_text())

#: The 24 wrapped sandbox operations. The SDK omits settings.update, which an admin runs in the Console.
OPERATIONS = {
    "sandboxes.list", "sandboxes.create", "sandboxes.settings.get", "sandboxes.getInfo",
    "sandboxes.update", "sandboxes.kill", "sandboxes.networkPolicy.get",
    "sandboxes.networkPolicy.update", "sandboxes.files.list", "sandboxes.files.read",
    "sandboxes.files.write", "sandboxes.files.remove", "sandboxes.files.download",
    "sandboxes.files.upload", "sandboxes.files.rename", "sandboxes.files.makeDir",
    "sandboxes.snapshots.list", "sandboxes.snapshots.create", "sandboxes.snapshots.restore",
    "sandboxes.activity.list", "sandboxes.hibernate", "sandboxes.resume",
    "sandboxes.commands.run", "sandboxes.commands.cancel",
}
NO_RETRY = {
    "sandboxes.create", "sandboxes.commands.run", "sandboxes.files.upload", "sandboxes.files.write",
    "sandboxes.files.rename", "sandboxes.files.makeDir", "sandboxes.files.remove",
    "sandboxes.snapshots.create", "sandboxes.snapshots.restore", "sandboxes.hibernate",
    "sandboxes.resume", "sandboxes.networkPolicy.update",
}
S = f"/omega/api/workspace/sandboxes/{SBX}"

# (name, call, path, query, json body or raw bytes, extra request headers)
CASES = [
    ("sandboxes.list", lambda a: a.list(), "/omega/api/workspace/sandboxes", {}, None, {}),
    ("sandboxes.create", lambda a: a.create(body={"name": "n"}), "/omega/api/workspace/sandboxes", {}, {"name": "n"}, {}),
    ("sandboxes.settings.get", lambda a: a.settings.get(), "/omega/api/workspace/sandboxes/settings", {}, None, {}),
    ("sandboxes.getInfo", lambda a: a.get_info(SBX), S, {}, None, {}),
    ("sandboxes.update", lambda a: a.update(SBX, body={"name": "m"}), S, {}, {"name": "m"}, {}),
    ("sandboxes.kill", lambda a: a.kill(SBX), S, {}, None, {}),
    ("sandboxes.networkPolicy.get", lambda a: a.network_policy.get(SBX), S + "/network-policy", {}, None, {}),
    ("sandboxes.networkPolicy.update", lambda a: a.network_policy.update(SBX, body={"mode": "off"}, if_match=3),
     S + "/network-policy", {}, {"mode": "off"}, {"if-match": '"3"'}),
    ("sandboxes.files.list", lambda a: a.files.list(SBX, path="src"), S + "/files", {"path": "src"}, None, {}),
    ("sandboxes.files.read", lambda a: a.files.read(SBX, "dir/a b.txt", max_bytes=10),
     S + "/files/dir/a%20b.txt", {"maxBytes": "10"}, None, {}),
    ("sandboxes.files.write", lambda a: a.files.write(SBX, "a.txt", body={"content": "hi", "encoding": "utf8"}),
     S + "/files/a.txt", {}, {"content": "hi", "encoding": "utf8"}, {}),
    ("sandboxes.files.remove", lambda a: a.files.remove(SBX, "old", recursive=True), S + "/files/old",
     {"recursive": "true"}, None, {}),
    ("sandboxes.files.download", lambda a: a.files.download(SBX, "out/a.bin"), S + "/download/out/a.bin", {}, None,
     {"accept": "application/octet-stream"}),
    ("sandboxes.files.upload", lambda a: a.files.upload(SBX, "a.bin", body=b"\x00\x01"), S + "/upload/a.bin", {},
     b"\x00\x01", {"content-type": "application/octet-stream"}),
    ("sandboxes.files.rename", lambda a: a.files.rename(SBX, body={"from": "a", "to": "b"}), S + "/move", {},
     {"from": "a", "to": "b"}, {}),
    ("sandboxes.files.makeDir", lambda a: a.files.make_dir(SBX, "d/e"), S + "/folders/d/e", {}, None, {}),
    ("sandboxes.snapshots.list", lambda a: a.snapshots.list(SBX), S + "/snapshots", {}, None, {}),
    ("sandboxes.snapshots.create", lambda a: a.snapshots.create(SBX), S + "/snapshots", {}, None, {}),
    ("sandboxes.snapshots.restore", lambda a: a.snapshots.restore(SBX, SNAP, body={"name": "r"}),
     S + f"/snapshots/{SNAP}/restore", {}, {"name": "r"}, {}),
    ("sandboxes.activity.list", lambda a: a.activity.list(SBX), S + "/activity", {}, None, {}),
    ("sandboxes.hibernate", lambda a: a.hibernate(SBX), S + "/hibernate", {}, None, {}),
    ("sandboxes.resume", lambda a: a.resume(SBX), S + "/resume", {}, None, {}),
    ("sandboxes.commands.run", lambda a: collect(a.commands.run(SBX, body={"command": "echo hi"})), S + "/exec", {},
     {"command": "echo hi"}, {"accept": "text/event-stream"}),
    ("sandboxes.commands.cancel", lambda a: a.commands.cancel(SBX, EXEC), S + f"/exec/{EXEC}/cancel", {}, None, {}),
]


def test_the_frozen_contract_has_every_wrapped_sandbox_operation():
    # The scoped spec contains each wrapped operation and omits settings updates.
    found = set(routes(load_spec()))
    assert OPERATIONS <= found, sorted(OPERATIONS - found)
    assert "sandboxes.settings.update" not in found
    assert {name for name, *_ in CASES} == OPERATIONS


def test_the_generated_table_matches_the_contract_routes():
    from fi.generated.platform.policy import OPERATIONS as TABLE

    for name, route in routes(load_spec()).items():
        assert TABLE[name].method == route.method and TABLE[name].path == route.template, name
        assert TABLE[name].retry_class == next(r["retry"] for r in DATA["operations"] if r["name"] == name)


def _snake(segment: str) -> str:
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", segment).lower()


@pytest.mark.parametrize("mode", MODES)
def test_method_names_are_the_x_omega_sdk_names(mode):
    namespace = (AsyncSandboxes if mode == "async" else Sandboxes)(None)
    for name in OPERATIONS:
        target = namespace
        for segment in name.split(".")[1:]:
            target = getattr(target, _snake(segment))
        assert callable(target), name
    # People update settings in the Console; the SDK exposes no settings write method.
    assert not any(hasattr(namespace.settings, verb) for verb in ("update", "put", "set"))
    for old in ("get", "destroy", "move", "upload", "download", "exec", "exec_cancel", "folders"):
        assert not hasattr(namespace, old), old


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("name,call,path,query,body,headers", CASES, ids=[c[0] for c in CASES])
def test_each_operation_sends_one_contract_request(mode, name, call, path, query, body, headers):
    server = MockServer()
    result = run(resolve(call(api(server, mode))))
    assert [seen.name for seen in server.seen] == [name]
    request = server.last.request
    assert request.url.raw_path.decode().split("?")[0] == path
    assert dict(parse_qsl(request.url.query.decode())) == query
    if isinstance(body, bytes):
        assert server.last.body == body
    else:
        assert server.last.json() == body
    for header, value in headers.items():
        assert request.headers[header] == value
    assert request.headers["x-api-key"] and "authorization" not in request.headers
    retry = request.extensions["fi.retry"]
    if name in NO_RETRY:
        assert retry["retries"] == 0, name
    else:
        assert "retries" not in retry, name
    if name in ("sandboxes.create", "sandboxes.snapshots.restore"):
        assert isinstance(result, AsyncSandbox if mode == "async" else Sandbox)
        assert result.id == SBX
    elif name == "sandboxes.files.download":
        assert result == b"file-bytes"
    elif name == "sandboxes.commands.run":
        assert [frame.event for frame in result] == ["started", "exit"]
    else:
        assert isinstance(result, dict) and result.get("schemaVersion", "").startswith("omega-workspace-sandboxes/")


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("name", sorted(NO_RETRY - {"sandboxes.commands.run"}))
def test_a_call_that_changes_a_sandbox_is_sent_once_even_after_a_429_or_503(mode, name):
    from ._sandbox_mock import error

    call = next(c for n, c, *_ in CASES if n == name)
    for status in (429, 503):
        server = MockServer()
        server.on(name, error(status, retryAfterSeconds=0))
        with pytest.raises(SandboxError):
            run(resolve(call(api(server, mode))))
        assert len(server.seen) == 1, (name, status)


@pytest.mark.parametrize("mode", MODES)
def test_connect_reads_the_record_and_returns_the_handle(mode):
    server = MockServer()
    sbx = run(resolve(api(server, mode).connect(SBX)))
    assert isinstance(sbx, AsyncSandbox if mode == "async" else Sandbox) and sbx.id == SBX
    assert [s.name for s in server.seen] == ["sandboxes.getInfo"]


@pytest.mark.parametrize("mode", MODES)
def test_a_read_keeps_the_transport_retries(mode):
    from ._sandbox_mock import error

    server, answers = MockServer(), iter([error(503)])
    server.on("sandboxes.list", lambda request: next(answers, None))
    run(resolve(api(server, mode).list()))
    assert [s.name for s in server.seen] == ["sandboxes.list", "sandboxes.list"]


def _wrapped_methods():
    mapping = json.loads((REPO / "openapi/platform/wrapper-map.json").read_text())
    for name, entry in sorted(mapping["operations"].items()):
        if name.startswith("sandboxes.") and "methods" in entry:
            for method in entry["methods"]:
                yield name, method


def _resolve(path: str, mode: str):
    root, *parts = path.split(".")
    if root == "client":
        target = (AsyncSandboxes if mode == "async" else Sandboxes)(None)
        parts = parts[1:]
    else:
        target = (AsyncSandbox if mode == "async" else Sandbox)(Sandboxes(None), {"id": SBX})
    for part in parts:
        target = getattr(target, part)
    return target


@pytest.mark.parametrize("name,method", list(_wrapped_methods()), ids=lambda v: v if isinstance(v, str) else v["py"])
def test_public_signatures_follow_the_wrapper_map_in_both_modes(name, method):
    expected = method["py_args"]
    star = expected.index("*") if "*" in expected else len(expected)
    signatures = [inspect.signature(_resolve(method["py"], mode)) for mode in MODES]
    shapes = [[(p.name, p.kind, p.default) for p in s.parameters.values()] for s in signatures]
    assert shapes[0] == shapes[1], name
    params = list(signatures[0].parameters.values())
    assert [p.name for p in params] == [a for a in expected if a != "*"], name
    kinds = [p.kind for p in params]
    assert all(k is inspect.Parameter.POSITIONAL_OR_KEYWORD for k in kinds[:star]), name
    assert all(k is inspect.Parameter.KEYWORD_ONLY for k in kinds[star:]), name
