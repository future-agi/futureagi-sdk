"""FutureAGISandboxSession over the frozen-OpenAPI mock, with the Agents SDK faked: exec (argv joined with
shlex.join, the working folder, the time limit, the exit-code rule, one request when the exit is
unknown), read and write through the files API, running(), persist and hydrate through a temporary
archive, and the refusals made before any request. Fake credentials only."""

from __future__ import annotations

import importlib
import io
import json
import shlex
import tarfile
from pathlib import Path

import httpx
import pytest

from fi.sandbox import AsyncSandbox, CommandIncompleteError, PayloadTooLargeError, SandboxHibernatedError
from tests.platform._sandbox_mock import EXEC, EXIT0, SBX, MockServer, api, error, run, sse, stream_response

from . import _fake_openai_agents as fake

STARTED = ("started", {"execId": EXEC, "sandboxId": SBX})


@pytest.fixture(name="adapter")
def adapter_fixture(monkeypatch):
    fake.install(monkeypatch)
    return importlib.import_module(fake.ADAPTER)


def make(adapter, server, *, max_timeout=900, ready=True, manifest=None, **fields):
    """A session on a handle that made no request (its record says ``active``)."""
    sbx = AsyncSandbox(api(server, "async"), {"id": SBX, "state": "active"})
    state = adapter.FutureAGISandboxSessionState(
        manifest=manifest or fake.Manifest(), snapshot=fake.NoopSnapshot(id="snap"),
        sandbox_id=SBX, workspace_root_ready=ready, **fields)
    return adapter.FutureAGISandboxSession(state=state, sandbox=sbx, max_timeout_s=max_timeout)


def ending(server, *frames, **exit_fields):
    body = sse(STARTED, *frames, ("exit", {**EXIT0, **exit_fields}))
    server.on("sandboxes.commands.run", lambda request: stream_response(body))


def names(server):
    return [seen.name for seen in server.seen]


def runs(server):
    return [seen.json() for seen in server.seen if seen.name == "sandboxes.commands.run"]


def path_of(seen):
    return seen.request.url.raw_path.decode("ascii").split("?", 1)[0]


def tar_bytes(**members):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for name, content in members.items():
            info = tarfile.TarInfo(name.replace("__", "/"))
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


def test_the_session_is_concrete(adapter):
    assert issubclass(adapter.FutureAGISandboxSession, fake.BaseSandboxSession)
    assert not getattr(adapter.FutureAGISandboxSession, "__abstractmethods__", None)


def test_exec_joins_argv_with_shlex_join(adapter):
    server = MockServer()
    ending(server, ("stdout", {"data": "it's a b\n"}), ("stderr", {"data": "warn"}))
    session = make(adapter, server)
    argv = ("python3", "-c", "print(\"it's a b\")")
    result = run(session._exec_internal(*argv))
    sent = server.last.json()["command"]
    assert sent == shlex.join(argv) and shlex.split(sent) == list(argv)
    assert (result.stdout, result.stderr, result.exit_code) == (b"it's a b\n", b"warn", 0)
    run(session.exec("echo 'two words'", Path("x y")))  # the SDK's shell=True wrapping
    assert shlex.split(server.last.json()["command"]) == ["sh", "-lc", shlex.join(["echo 'two words'", "x y"])]
    assert len(runs(server)) == 2


def relative_cwd_only(request):
    """The exec route's working-folder rule: relative to /workspace; an absolute folder, or a ``.`` or
    ``..`` segment, is a 400 (absent or empty means /workspace)."""
    cwd = json.loads(request.content or b"{}").get("cwd")
    if cwd is not None and (cwd.startswith("/") or {".", ".."} & set(cwd.split("/"))):
        return error(400, "validation")
    return stream_response(sse(STARTED, ("exit", EXIT0)))


def test_exec_sends_cwd_and_clamps_timeout(adapter):
    server = MockServer()
    server.on("sandboxes.commands.run", relative_cwd_only)
    session = make(adapter, server, max_timeout=900)
    for timeout in (2.2, 0, -5, 5000, None, float("inf")):
        assert run(session._exec_internal("true", timeout=timeout)).exit_code == 0
    sent = runs(server)
    assert all("cwd" not in body for body in sent)  # /workspace itself is the server's default
    assert [body["timeoutSeconds"] for body in sent] == [3, 1, 1, 900, 900, 900]
    assert all("env" not in body for body in sent)
    server = MockServer()
    server.on("sandboxes.commands.run", relative_cwd_only)
    session = make(adapter, server, max_timeout=600, ready=False, exec_timeout_s=120,
                   manifest=fake.Manifest(root="/workspace/proj"))
    run(session._exec_internal("true"))
    assert runs(server) == [{"command": "true", "timeoutSeconds": 120}]  # no cwd before the root exists
    session._root_ready = True
    assert run(session._exec_internal("true")).exit_code == 0
    assert runs(server)[-1]["cwd"] == "proj"


@pytest.mark.parametrize("root,cwd", [
    ("/workspace/my proj/", "my proj"),
    ("/workspace/./a/b", "a/b"),
    ("/workspace/a/../b", "b"),
    ("/workspace/", None),
])
def test_exec_sends_the_root_relative_to_the_workspace(adapter, root, cwd):
    server = MockServer()
    server.on("sandboxes.commands.run", relative_cwd_only)
    session = make(adapter, server, manifest=fake.Manifest(root=root))
    assert run(session._exec_internal("pwd")).exit_code == 0
    assert runs(server)[-1].get("cwd") == cwd


@pytest.mark.parametrize("fields,code,note", [
    ({"exitCode": None, "timedOut": True, "signal": "SIGKILL"}, 124, "Command timed out after 30 seconds"),
    ({"exitCode": None, "signal": "SIGKILL"}, 137, "Command was ended by signal SIGKILL"),
    ({"exitCode": None, "cancelled": True, "signal": "SIGTERM"}, 130, "Command was cancelled"),
    ({"exitCode": None, "error": "spawn /bin/sh ENOENT"}, 1, "The command could not start: spawn /bin/sh ENOENT"),
    ({"exitCode": None, "signal": "SIGNOPE"}, 1, "Command ended without an exit code (SIGNOPE)"),
    ({"exitCode": None}, 1, "Command ended without an exit code"),
    ({"exitCode": 3}, 3, None),
])
def test_exec_exit_mapping_124_137_130_1(adapter, fields, code, note):
    server = MockServer()
    ending(server, ("stderr", {"data": "partial"}), **fields)
    session = make(adapter, server)
    result = run(session._exec_internal("sleep", "100", timeout=30))
    assert result.exit_code == code and isinstance(result.exit_code, int)
    expected = "partial" if note is None else f"partial\n{note}"
    assert result.stderr.decode() == expected


def test_exec_missing_exit_frame_raises_and_sends_one_request(adapter):
    server = MockServer()
    server.on("sandboxes.commands.run", lambda request: stream_response(sse(STARTED, ("stdout", {"data": "x"}))))
    session = make(adapter, server)
    with pytest.raises(fake.ExecTransportError) as caught:
        run(session._exec_internal("make", "deploy"))
    assert caught.value.retryable is False and caught.value.context["reason"] == "exit_unknown"
    assert isinstance(caught.value.__cause__, CommandIncompleteError)
    assert caught.value.command == ("make", "deploy") and len(runs(server)) == 1
    server = MockServer()
    server.on("sandboxes.commands.run",
              lambda request: stream_response(sse(STARTED, ("error", {"message": "runtime gone"}))))
    session = make(adapter, server)
    with pytest.raises(fake.ExecTransportError) as caught:
        run(session._exec_internal("true"))
    assert caught.value.context["reason"] == "server_failed" and len(runs(server)) == 1


def test_read_returns_bytesio(adapter):
    server = MockServer()
    session = make(adapter, server)
    data = run(session.read(Path("notes/a.txt")))
    assert isinstance(data, io.BytesIO) and data.getvalue() == b"file-bytes"
    run(session.read(Path("/workspace/notes/b.txt")))
    assert [path_of(seen).rsplit("/download/", 1)[1] for seen in server.seen] == ["notes/a.txt", "notes/b.txt"]
    server.on("sandboxes.files.download", lambda request: error(404, "not_found"))
    with pytest.raises(fake.WorkspaceReadNotFoundError):
        run(session.read(Path("missing.txt")))
    with pytest.raises(IsADirectoryError):
        run(session.read(Path(".")))


def test_write_makes_parent_then_uploads(adapter):
    server = MockServer()
    session = make(adapter, server)
    run(session.write(Path("a/b/c.txt"), io.BytesIO(b"hello")))
    assert names(server) == ["sandboxes.files.makeDir", "sandboxes.files.upload"]
    assert path_of(server.seen[0]).endswith("/folders/a/b") and path_of(server.seen[1]).endswith("/upload/a/b/c.txt")
    assert server.last.body == b"hello"
    server = MockServer()
    session = make(adapter, server)
    answers = iter([error(404, "not_found"), error(409, "conflict", detail={"reason": "exists"}),
                    error(409, "conflict", detail={"reason": "exists"})])
    server.on("sandboxes.files.makeDir", lambda request: next(answers))
    run(session.write(Path("/workspace/a/b/c.txt"), io.StringIO("text")))
    assert [path_of(seen).rsplit("/folders/", 1)[-1] for seen in server.seen[:-1]] == ["a/b", "a", "a/b"]
    assert server.last.name == "sandboxes.files.upload" and server.last.body == b"text"
    server = MockServer()
    session = make(adapter, server)
    run(session.write(Path("top.txt"), io.BytesIO(b"x")))
    assert names(server) == ["sandboxes.files.upload"]
    server.on("sandboxes.files.makeDir", lambda request: error(409, "conflict", detail={"state": "hibernated"}))
    with pytest.raises(SandboxHibernatedError):
        run(session.write(Path("d/e.txt"), io.BytesIO(b"x")))
    assert names(server)[-1] == "sandboxes.files.makeDir"


def test_user_argument_refused_without_request(adapter):
    server = MockServer()
    session = make(adapter, server)
    with pytest.raises(NotImplementedError, match="one user"):
        run(session.read(Path("a.txt"), user="root"))
    with pytest.raises(NotImplementedError, match="'root'"):
        run(session.write(Path("a.txt"), io.BytesIO(b"x"), user=fake.User(name="root")))
    with pytest.raises(NotImplementedError, match="one user"):
        run(session.exec("id", user="nobody"))
    assert server.seen == []


def test_running_true_for_active_false_for_hibernated(adapter):
    server = MockServer()
    session = make(adapter, server)
    record = {"schemaVersion": "omega-workspace-sandboxes/v1", "sandbox": {"id": SBX, "name": "n"}}
    for state, expected in (("active", True), ("hibernated", False), ("recovery_required", False)):
        body = {**record, "sandbox": {**record["sandbox"], "state": state}}
        server.on("sandboxes.getInfo", lambda request, body=body: httpx.Response(200, json=body))
        assert run(session.running()) is expected
    server.on("sandboxes.getInfo", lambda request: error(404, "not_found"))
    assert run(session.running()) is False
    assert names(server) == ["sandboxes.getInfo"] * 4
    idle = make(adapter, MockServer(), ready=False)
    assert run(idle.running()) is False and idle.sandbox.state == "active"


def test_persist_workspace_tars_downloads_and_removes(adapter):
    server = MockServer()
    session = make(adapter, server, exec_timeout_s=300)
    session.register_persist_workspace_skip_path("cache")
    data = run(session.persist_workspace())
    assert data.getvalue() == b"file-bytes"
    assert names(server) == ["sandboxes.commands.run", "sandboxes.files.download", "sandboxes.files.remove"]
    body = server.seen[0].json()
    words = shlex.split(body["command"])
    archive = words[words.index("-cf") + 1]
    assert words[0] == "tar" and words[-1] == "." and words[words.index("-C") + 1] == "/workspace"
    assert "--exclude=./cache" in words and "--exclude=./.fi-ws-*.tar" in words
    assert archive.startswith("/workspace/.fi-ws-") and archive.endswith(".tar") and body["timeoutSeconds"] == 300
    name = archive[len("/workspace/"):]
    assert path_of(server.seen[1]).endswith("/download/" + name) and path_of(server.seen[2]).endswith("/files/" + name)
    server = MockServer()
    ending(server, ("stderr", {"data": "tar: disk full"}), exitCode=2)
    session = make(adapter, server)
    with pytest.raises(fake.WorkspaceArchiveReadError) as caught:
        run(session.persist_workspace())
    assert caught.value.context["exit_code"] == 2 and caught.value.context["temporary_archive"].startswith("/workspace/.fi-ws-")
    assert names(server) == ["sandboxes.commands.run"]


def test_hydrate_workspace_uploads_untars_and_removes(adapter):
    server = MockServer()
    session = make(adapter, server, ready=False, manifest=fake.Manifest(root="/workspace/proj"))
    raw = tar_bytes(**{"a.txt": b"A", "src__b.py": b"B"})
    run(session.hydrate_workspace(io.BytesIO(raw)))
    assert names(server) == ["sandboxes.files.upload", "sandboxes.commands.run", "sandboxes.files.remove"]
    assert server.seen[0].body == raw
    name = path_of(server.seen[0]).rsplit("/upload/", 1)[1]
    assert name.startswith(".fi-ws-") and path_of(server.seen[2]).endswith("/files/" + name)
    assert shlex.split(server.seen[1].json()["command"]) == [
        "mkdir", "-p", "--", "/workspace/proj", "&&", "tar", "-C", "/workspace/proj", "-xf", "/workspace/" + name]
    assert session._root_ready is True
    server = MockServer()
    session = make(adapter, server)
    with pytest.raises(fake.WorkspaceArchiveWriteError) as caught:
        run(session.hydrate_workspace(io.BytesIO(tar_bytes(**{"..__escape": b"x"}))))
    assert caught.value.context["reason"] == "unsafe_or_invalid_tar" and server.seen == []
    ending(server, exitCode=2)
    with pytest.raises(fake.WorkspaceArchiveWriteError):
        run(session.hydrate_workspace(io.BytesIO(raw)))
    assert names(server) == ["sandboxes.files.upload", "sandboxes.commands.run", "sandboxes.files.remove"]


def test_hydrate_over_64_mib_refused_before_upload(adapter, monkeypatch):
    module = importlib.import_module(fake.ADAPTER + "._session")
    assert module.UPLOAD_LIMIT_BYTES == 64 * 1024 * 1024
    monkeypatch.setattr(module, "UPLOAD_LIMIT_BYTES", 16)
    server = MockServer()
    session = make(adapter, server)
    with pytest.raises(PayloadTooLargeError) as caught:
        run(session.hydrate_workspace(io.BytesIO(b"x" * 17)))
    assert caught.value.local is True and caught.value.limit_bytes == 16 and "17 bytes" in str(caught.value)
    assert server.seen == []


def test_start_makes_the_workspace_root_once(adapter):
    server = MockServer()
    session = make(adapter, server, ready=False, manifest=fake.Manifest(root="/workspace/my proj"))
    run(session._prepare_backend_workspace())
    assert runs(server) == [{"command": "mkdir -p -- '/workspace/my proj'", "timeoutSeconds": 60}]
    assert session._root_ready is True
    session._set_start_state_preserved(True)
    run(session._prepare_backend_workspace())
    assert len(runs(server)) == 1
    server = MockServer()
    ending(server, ("stderr", {"data": "mkdir: denied"}), exitCode=1)
    session = make(adapter, server, ready=False)
    with pytest.raises(fake.WorkspaceStartError):
        run(session._prepare_backend_workspace())
    assert session._root_ready is False
