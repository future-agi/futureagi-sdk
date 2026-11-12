"""The MCP server's tool bodies (``fi.sandbox_integrations.mcp_server._tools``), framework-free, over the
frozen-OpenAPI mock: each tool's result shape, the whole exit record, output clipping, the time-limit
clamp (1 to the workspace's ``caps.exec.maxTimeoutSeconds``), the command's folder sent relative to
``/workspace`` (the mock's exec route refuses an absolute one, as the service does), file paths sent
relative to ``/workspace`` too (one outside it refused before any request), writes that rely on the
write creating folders, pinned mode, the ``created`` set and cleanup (its deletes sent
together), and error texts with a next step and no key. Fake credentials only; no ``mcp`` package
needed."""

from __future__ import annotations

import asyncio
import base64
import inspect
from urllib.parse import unquote

import httpx
import pytest

from fi.sandbox_integrations.mcp_server import SandboxTools, SandboxToolError
from tests.platform._sandbox_cli_support import (
    OTHER,
    answer,
    exec_body,
    file_answer,
    names,
    no_secret,
    record,
    refuse,
)
from tests.platform._sandbox_mock import EXEC, EXIT0, SBX, MockServer, api, run

SCHEMA = "omega-workspace-sandboxes/v1"
CAPS = {
    "maxActiveSandboxes": 2,
    "defaultTemplate": "base",
    "templates": [{"id": "base", "name": "Base", "available": True, "scan": {"critical": 0}},
                  {"id": "python-data", "name": "Python data", "available": False, "reason": "host"}],
    "defaultSize": "small",
    "sizes": [{"id": "small", "label": "Small", "cpus": 1, "memoryMb": 1024, "pidsLimit": 256,
               "goodFor": "scripts", "available": True}],
    "idleTtlSeconds": 900,
    "exec": {"defaultTimeoutSeconds": 60, "maxTimeoutSeconds": 3600, "maxOutputBytes": 1048576},
    "egressAllowList": [],
}
ROW = {"id": SBX, "name": "job", "state": "active", "template": "base", "size": "small",
       "lastActivityAt": "2026-01-01T00:00:00Z", "image": None, "readOnly": False}


def listing(caps=None):
    return answer(200, json={"schemaVersion": SCHEMA, "sandboxes": [ROW], "caps": CAPS if caps is None else caps,
                             "provider": "docker"})


@pytest.fixture(name="server")
def server_fixture():
    mock = MockServer()
    mock.on("sandboxes.getInfo", answer(200, json=record()))
    return mock


def tools_for(server, **kwargs):
    return SandboxTools(api(server, "async"), **kwargs)


def call(server, method, *args, tools=None, **kwargs):
    """One tool call in its own event loop, over a fresh client unless ``tools`` is given."""
    tools = tools or tools_for(server)
    return run(getattr(tools, method)(*args, **kwargs))


def refused(server, method, *args, tools=None, **kwargs) -> SandboxToolError:
    with pytest.raises(SandboxToolError) as caught:
        call(server, method, *args, tools=tools, **kwargs)
    return caught.value


def test_list_returns_sandboxes_and_caps(server):
    server.on("sandboxes.list", listing())
    result = call(server, "sandbox_list")
    assert result["sandboxes"] == [{key: ROW[key] for key in
                                    ("id", "name", "state", "template", "size", "lastActivityAt")}]
    caps = result["caps"]
    assert caps["maxActiveSandboxes"] == 2 and caps["defaultTemplate"] == "base" and caps["defaultSize"] == "small"
    assert caps["templates"] == [{"id": "base", "name": "Base", "available": True},
                                 {"id": "python-data", "name": "Python data", "available": False}]
    assert caps["sizes"] == [{"id": "small", "available": True}]
    assert caps["exec"] == CAPS["exec"] and caps["idleTtlSeconds"] == 900
    assert "egressAllowList" not in caps


def test_create_records_id_in_created(server):
    server.on("sandboxes.create", answer(201, json=record(name="job", template="base", size="small")))
    tools = tools_for(server)
    result = call(server, "sandbox_create", "job", size="small", tools=tools)
    assert result == {"id": SBX, "name": "job", "state": "active", "template": "base", "size": "small"}
    assert tools.created == {SBX}
    assert server.last.json() == {"name": "job", "size": "small"}
    assert call(server, "sandbox_create", "é" * 60, tools=tools)["id"] == SBX  # 120 bytes
    sent = len(server.seen)
    for name in ("", "   ", "é" * 61, "line\nbreak"):
        assert refused(server, "sandbox_create", name, tools=tools).code == "invalid_name"
    assert len(server.seen) == sent


def test_exec_returns_whole_exit_record(server):
    server.on("sandboxes.commands.run", exec_body(
        ("stdout", {"data": "so far\n"}), ("stderr", {"data": "warn\n"}),
        ("exit", {**EXIT0, "exitCode": None, "signal": "SIGTERM", "durationMs": 70, "truncated": True})))
    result = call(server, "sandbox_exec", "python3 app.py", SBX, cwd="src")
    assert result == {
        "exit_code": None, "signal": "SIGTERM", "timed_out": False, "cancelled": False, "truncated": True,
        "duration_ms": 70, "error": None, "exec_id": EXEC, "stdout": "so far\n", "stderr": "warn\n",
        "stdout_clipped": False, "stderr_clipped": False,
    }
    server.on("sandboxes.commands.run", exec_body(("exit", {**EXIT0, "exitCode": 3})))
    assert call(server, "sandbox_exec", "false", SBX)["exit_code"] == 3  # a non-zero exit is a result
    server.on("sandboxes.commands.run", exec_body(
        ("exit", {**EXIT0, "exitCode": None, "signal": "SIGKILL", "timedOut": True})))
    assert call(server, "sandbox_exec", "sleep 99", SBX)["timed_out"] is True
    server.on("sandboxes.commands.run", exec_body(("exit", {**EXIT0, "exitCode": None, "error": "spawn ENOENT"})))
    assert call(server, "sandbox_exec", "x", SBX)["error"] == "spawn ENOENT"


def test_exec_clips_output_tail_and_sets_flags(server):
    server.on("sandboxes.commands.run", exec_body(
        ("stdout", {"data": "0123456789"}), ("stderr", {"data": "abc"}), ("exit", EXIT0)))
    result = call(server, "sandbox_exec", "x", SBX, tools=tools_for(server, max_output_chars=5))
    assert result["stdout"] == "[... 5 earlier characters dropped ...]\n56789"
    assert result["stdout_clipped"] is True
    assert result["stderr"] == "abc" and result["stderr_clipped"] is False
    with pytest.raises(ValueError):
        tools_for(server, max_output_chars=0)


def test_exec_timeout_clamped_1_to_the_workspace_limit(server):
    """Replaces the 1-to-900 clamp: the longest limit is the workspace's caps.exec.maxTimeoutSeconds,
    read once, never a number written here."""
    server.on("sandboxes.list", listing())
    tools = tools_for(server)

    async def go():
        sent = []
        for asked in (0, -5, 5000, 30):
            await tools.sandbox_exec("x", SBX, timeout_seconds=asked)
            sent.append(server.last.json().get("timeoutSeconds"))
        await tools.sandbox_exec("x", SBX)
        sent.append(server.last.json().get("timeoutSeconds"))
        return sent

    assert run(go()) == [1, 1, 3600, 30, None]
    assert names(server).count("sandboxes.list") == 1
    server.on("sandboxes.list", listing(caps={**CAPS, "exec": {"defaultTimeoutSeconds": 60}}))
    call(server, "sandbox_exec", "x", SBX, timeout_seconds=5000)
    assert server.last.json()["timeoutSeconds"] == 5000  # no limit given: only the floor applies


def test_exec_sends_one_request_and_no_env(server):
    server.on("sandboxes.commands.run", exec_body(("exit", EXIT0)))
    call(server, "sandbox_exec", "echo hi", SBX, cwd="src")
    assert names(server).count("sandboxes.commands.run") == 1
    assert server.last.json() == {"command": "echo hi", "cwd": "src"}
    assert "env" not in inspect.signature(SandboxTools.sandbox_exec).parameters
    server.on("sandboxes.commands.run", exec_body(("stdout", {"data": "half"})))  # no exit frame
    error = refused(server, "sandbox_exec", "make", SBX)
    assert error.code == "command_incomplete" or "unknown" in str(error)
    assert "not run again" in str(error)
    assert names(server).count("sandboxes.commands.run") == 2  # one more call, one more request


@pytest.mark.parametrize("cwd,sent", [
    ("/workspace/src", "src"),
    ("/workspace", None),
    ("/workspace/", None),
    ("/workspace/a/../b", "b"),
    ("//workspace/src", "src"),
    ("src", "src"),
    ("./src/", "src"),
    (".", None),
    ("", None),
    (None, None),
])
def test_exec_sends_cwd_relative_to_the_workspace(server, cwd, sent):
    server.on("sandboxes.commands.run", exec_body(("exit", EXIT0)))
    assert call(server, "sandbox_exec", "pwd", SBX, cwd=cwd)["exit_code"] == 0
    body = server.last.json()
    assert body.get("cwd") == sent and ("cwd" in body) == (sent is not None)


@pytest.mark.parametrize("cwd", ["/tmp", "/", "/workspacex/a", "/workspace/../etc", "..", "../x", "src/../../x"])
def test_exec_refuses_a_folder_outside_the_workspace_before_any_request(server, cwd):
    server.on("sandboxes.list", listing())
    error = refused(server, "sandbox_exec", "ls", SBX, cwd=cwd, timeout_seconds=30)
    assert error.code == "invalid_cwd" and str(error).startswith("invalid_cwd: ")
    assert "relative to /workspace" in str(error) and "cd /tmp" in str(error)
    assert server.seen == []  # not the limit read, the connect or the exec


def test_read_file_text_and_base64(server):
    server.on("sandboxes.files.read", file_answer("hello"))
    assert call(server, "sandbox_read_file", "notes.txt", SBX) == {
        "path": "f", "encoding": "utf8", "content": "hello", "bytes": 6, "truncated": False}
    data = base64.b64encode(b"\x00\x01\xff").decode()
    server.on("sandboxes.files.read", file_answer(data, encoding="base64", truncated=True))
    result = call(server, "sandbox_read_file", "blob.bin", SBX, max_bytes=3)
    assert result["encoding"] == "base64" and result["content"] == data and result["truncated"] is True
    assert server.last.request.url.params["maxBytes"] == "3"
    server.on("sandboxes.files.read", refuse(400, "validation", detail={"reason": "wrong_type"}))
    error = refused(server, "sandbox_read_file", "src", SBX)
    assert str(error).startswith("validation: ") and "sandbox_list_files" in str(error)


def file_path(seen):
    """The decoded path a read or write carried: what follows ``files/`` in its URL."""
    raw = seen.request.url.raw_path.decode("ascii").split("?", 1)[0]
    return unquote(raw.split(f"/{SBX}/files/", 1)[1])


@pytest.mark.parametrize("path,sent", [
    ("/workspace/notes.txt", "notes.txt"), ("notes.txt", "notes.txt"), ("/workspace/src/a.py", "src/a.py"),
])
def test_read_file_sends_the_path_relative_to_the_workspace(server, path, sent):
    """The mock refuses ``workspace/notes.txt`` (an absolute path whose slash was lost), as the service
    would put it at /workspace/workspace/notes.txt: a read sent that way fails here."""
    server.on("sandboxes.files.read", file_answer("hello"))
    assert call(server, "sandbox_read_file", path, SBX)["content"] == "hello"
    assert server.last.name == "sandboxes.files.read" and file_path(server.last) == sent


def test_write_then_read_reach_the_same_file(server):
    server.on("sandboxes.files.read", file_answer("hello"))
    tools = tools_for(server)

    async def go():
        await tools.sandbox_write_file("/workspace/out/a.txt", "hello", SBX)
        return await tools.sandbox_read_file("/workspace/out/a.txt", SBX)

    assert run(go())["content"] == "hello"
    files = [seen for seen in server.seen if seen.name.startswith("sandboxes.files.")]
    assert [(seen.name, file_path(seen)) for seen in files] == [
        ("sandboxes.files.write", "out/a.txt"), ("sandboxes.files.read", "out/a.txt")]


@pytest.mark.parametrize("method,args", [
    ("sandbox_read_file", ("/tmp/notes.txt",)), ("sandbox_read_file", ("/workspace/../etc/passwd",)),
    ("sandbox_read_file", ("a\\b.txt",)), ("sandbox_read_file", ("/workspace",)),
    ("sandbox_write_file", ("/tmp/notes.txt", "x")), ("sandbox_list_files", ("/etc",)),
])
def test_file_tools_refuse_a_path_outside_the_workspace_before_any_request(server, method, args):
    error = refused(server, method, *args, sandbox_id=SBX)
    text = str(error)
    assert error.code == "invalid_path" and text.startswith("invalid_path: sandboxes.files.")
    assert repr(args[0]) in text and "relative to /workspace" in text and "sandbox_exec" in text
    assert "setup problem" not in text and "OMEGA_BASE_URL" not in text  # a path, not the server's setup
    assert server.seen == []  # not the connect, not the file call


def test_write_file_creates_folders_by_the_write_utf8_and_base64(server):
    """Replaces "makes parent then writes": the JSON write creates missing folders itself, and
    make_dir on an existing folder is refused, so no make_dir is sent."""
    server.on("sandboxes.files.write", answer(200, json={
        "schemaVersion": SCHEMA, "file": {"path": "a/b/c.txt", "bytes": 5, "modifiedAt": "2026-01-01T00:00:00Z"}}))
    assert call(server, "sandbox_write_file", "a/b/c.txt", "hello", SBX) == {"path": "a/b/c.txt", "bytes": 5}
    assert server.last.json() == {"content": "hello", "encoding": "utf8"}
    data = base64.b64encode(b"\x00\x01\x02").decode()
    call(server, "sandbox_write_file", "a/b/c.bin", data, SBX, encoding="base64")
    assert server.last.json() == {"content": data, "encoding": "base64"}
    assert "sandboxes.files.makeDir" not in names(server)
    sent = len(server.seen)
    assert refused(server, "sandbox_write_file", "x.bin", "not base64!", SBX, encoding="base64").code == \
        "invalid_content"
    assert refused(server, "sandbox_write_file", "x.bin", "x", SBX, encoding="latin1").code == "invalid_encoding"
    assert len(server.seen) == sent


def test_list_files_entries(server):
    server.on("sandboxes.files.list", answer(200, json={"schemaVersion": SCHEMA, "path": "src", "entries": [
        {"name": "app.py", "size": 12, "mode": "0644"},
        {"name": "lib", "size": 0, "mode": "0755", "directory": True}]}))
    assert call(server, "sandbox_list_files", "src", SBX) == {"path": "src", "entries": [
        {"name": "app.py", "size": 12, "directory": False, "mode": "0644"},
        {"name": "lib", "size": 0, "directory": True, "mode": "0755"}]}
    assert server.last.request.url.params["path"] == "src"
    call(server, "sandbox_list_files", sandbox_id=SBX)
    assert "path" not in server.last.request.url.params  # the root: no path (the route refuses ".")


def test_delete_removes_from_created_and_404_is_ok(server):
    server.on("sandboxes.create", answer(201, json=record()))
    server.on("sandboxes.kill", answer(200, json=record(state="destroyed")))
    tools = tools_for(server)

    async def go():
        await tools.sandbox_create()
        return await tools.sandbox_delete(SBX)

    assert run(go()) == {"id": SBX, "state": "destroyed"}
    assert tools.created == set() and names(server) == ["sandboxes.create", "sandboxes.kill"]
    server.on("sandboxes.kill", refuse(404, "not_found"))
    assert call(server, "sandbox_delete", OTHER) == {"id": OTHER, "state": "destroyed"}
    assert "sandboxes.getInfo" not in names(server)  # delete never reads first


def test_pinned_mode_refuses_other_ids(server):
    server.on("sandboxes.commands.run", exec_body(("exit", EXIT0)))
    tools = tools_for(server, pinned=SBX)
    error = refused(server, "sandbox_exec", "ls", OTHER, tools=tools)
    assert error.code == "pinned" and SBX in str(error) and OTHER in str(error)
    for method, args in (("sandbox_read_file", ("f", OTHER)), ("sandbox_write_file", ("f", "x", OTHER)),
                         ("sandbox_list_files", (".", OTHER))):
        assert refused(server, method, *args, tools=tools).code == "pinned"
    for method, args in (("sandbox_list", ()), ("sandbox_create", ()), ("sandbox_delete", (SBX,))):
        assert refused(server, method, *args, tools=tools).code == "pinned"
    assert server.seen == []
    assert call(server, "sandbox_exec", "ls", tools=tools)["exit_code"] == 0
    assert SBX in str(server.last.request.url)
    assert refused(server, "sandbox_exec", "ls").code == "missing_sandbox_id"  # unpinned: say which


def test_cleanup_deletes_only_created_and_reports_failures(server):
    made = iter([SBX, OTHER])
    server.on("sandboxes.create", lambda request: httpx.Response(201, json=record(ident=next(made))))
    server.on("sandboxes.kill", lambda request: (
        httpx.Response(403, json={"code": "forbidden", "message": "not yours"})
        if OTHER in str(request.url) else httpx.Response(200, json=record(state="destroyed"))))
    server.on("sandboxes.commands.run", exec_body(("exit", EXIT0)))
    third = "sbx_" + "d" * 24
    server.on("sandboxes.getInfo", answer(200, json=record(ident=third)))
    tools = tools_for(server)

    async def go():
        await tools.sandbox_create()
        await tools.sandbox_create()
        await tools.sandbox_exec("ls", third)  # used, not created: never deleted on exit
        return await tools.cleanup()

    assert run(go()) == [SBX]
    assert tools.created == {OTHER}
    assert len(tools.cleanup_failures) == 1
    failed, text = tools.cleanup_failures[0]
    assert failed == OTHER and text.startswith("forbidden: ")
    killed = [str(seen.request.url) for seen in server.seen if seen.name == "sandboxes.kill"]
    assert len(killed) == 2 and not any(third in url for url in killed)


def test_cleanup_sends_the_deletes_together(server):
    """A client waits about 2 s for a server to stop: deleting one sandbox after another could run
    past that. Each fake delete here ends only once every delete has started, so deletes sent one at a
    time would never end (the wait_for limit fails the test instead)."""
    tools = tools_for(server)
    tools.created.update({SBX, OTHER})
    started = []

    async def delete(sandbox_id):
        started.append(sandbox_id)
        while len(started) < 2:
            await asyncio.sleep(0.01)
        if sandbox_id == OTHER:
            raise SandboxToolError("forbidden: not yours", code="forbidden")
        tools.created.discard(sandbox_id)
        return {"state": "destroyed"}

    tools._delete = delete
    assert run(asyncio.wait_for(tools.cleanup(), 5)) == [SBX]
    assert sorted(started) == sorted([SBX, OTHER])
    assert tools.created == {OTHER}
    assert tools.cleanup_failures == [(OTHER, "forbidden: not yours")]
    assert server.seen == []


def test_quota_and_hibernated_errors_have_next_step_and_no_secret(server):
    server.on("sandboxes.create", refuse(409, "quota_exceeded"))
    quota = str(refused(server, "sandbox_create"))
    assert quota.startswith("quota_exceeded: ") and "sandbox_list" in quota and "ask an admin" in quota
    server.on("sandboxes.getInfo", refuse(409, "sandbox_hibernated", detail={"state": "hibernated"}))
    hibernated = str(refused(server, "sandbox_exec", "ls", SBX))
    assert hibernated.startswith("sandbox_hibernated: ") and f"sandbox resume {SBX}" in hibernated

    def drop(request):
        raise httpx.ReadError("connection reset", request=request)

    server.on("sandboxes.create", drop)
    unknown = str(refused(server, "sandbox_create"))
    assert "unknown" in unknown and "sandbox_list" in unknown
    assert names(server).count("sandboxes.create") == 2  # never sent again
    no_secret(quota, hibernated, unknown)
