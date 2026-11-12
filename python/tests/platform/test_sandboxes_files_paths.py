"""``sbx.files`` paths (contract ``files.md``, Path rules): every files route takes a path relative to
``/workspace``. The handle sends an absolute path under ``/workspace`` in that form, sends the root to the
listing only (as no ``path`` at all), and refuses a path outside ``/workspace``, or with a ``.`` or ``..``
segment, a backslash or a control character, with ``ConfigurationError`` (``invalid_path``) before any
request. The mock answers the files routes as the sandbox service does (``_strict_exec``), so a wrong path
fails here. Fake credentials only."""

from __future__ import annotations

from pathlib import PurePosixPath
from urllib.parse import unquote

import pytest
from fi.sandbox import AsyncSandbox, ConfigurationError, Sandbox, ValidationError

from tests.sandbox_integrations._strict_exec import path_refusal, strict

from ._sandbox_mock import MODES, SBX, MockServer, api, resolve, run

VERBS = ("list", "read", "write", "upload", "download", "download_to", "remove", "move", "make_dir")
OPERATIONS = {"list": "sandboxes.files.list", "read": "sandboxes.files.read", "write": "sandboxes.files.write",
              "upload": "sandboxes.files.upload", "download": "sandboxes.files.download",
              "download_to": "sandboxes.files.download", "remove": "sandboxes.files.remove",
              "move": "sandboxes.files.rename", "make_dir": "sandboxes.files.makeDir"}
RULE = "sandbox paths are relative to /workspace"


def handle(server, mode):
    cls = AsyncSandbox if mode == "async" else Sandbox
    return cls(api(server, mode), {"id": SBX, "state": "active"})


def act(files, verb, path, local):
    """One files call on ``path`` (``move`` moves it to ``b.txt``; ``download_to`` writes ``local``)."""
    calls = {
        "list": lambda: files.list(path),
        "read": lambda: files.read(path),
        "write": lambda: files.write(path, "x"),
        "upload": lambda: files.upload(path, b"x"),
        "download": lambda: files.download(path),
        "download_to": lambda: files.download_to(path, local),
        "remove": lambda: files.remove(path),
        "move": lambda: files.move(path, "b.txt"),
        "make_dir": lambda: files.make_dir(path),
    }
    return run(resolve(calls[verb]()))


def sent(seen):
    """The path one files request carried, as the service reads it: the listing's ``path`` query (None:
    not sent), the move's ``from``, else the decoded ``{path}`` after the route's verb in the URL."""
    if seen.name == "sandboxes.files.list":
        return seen.request.url.params.get("path")
    if seen.name == "sandboxes.files.rename":
        return seen.json()["from"]
    raw = seen.request.url.raw_path.decode("ascii").split("?", 1)[0]
    return unquote(raw.split(f"/{SBX}/", 1)[1].split("/", 1)[1])


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("verb", VERBS)
@pytest.mark.parametrize("path,wire", [
    ("/workspace/sub/a.txt", "sub/a.txt"),
    ("sub/a.txt", "sub/a.txt"),
    ("//workspace/sub//a.txt", "sub/a.txt"),
    ("/workspace/.fi-eval/row.json", ".fi-eval/row.json"),
    (PurePosixPath("/workspace/sub/a.txt"), "sub/a.txt"),
])
def test_every_verb_sends_the_path_relative_to_the_workspace(mode, verb, path, wire, tmp_path):
    server = strict(MockServer())
    act(handle(server, mode).files, verb, path, tmp_path / "out.bin")
    assert [seen.name for seen in server.seen] == [OPERATIONS[verb]]
    assert sent(server.last) == wire


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("root", [".", "./", "/workspace", "/workspace/", "", None])
def test_the_listing_takes_the_root_as_no_path(mode, root):
    server = strict(MockServer())
    files = handle(server, mode).files
    run(resolve(files.list(root)))
    run(resolve(files.list()))
    assert [seen.name for seen in server.seen] == ["sandboxes.files.list"] * 2
    assert all("path" not in seen.request.url.params for seen in server.seen)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("verb", [verb for verb in VERBS if verb != "list"])
@pytest.mark.parametrize("root", [".", "/workspace", "/workspace/", ""])
def test_the_root_is_refused_where_the_route_needs_a_file(mode, verb, root, tmp_path):
    server = strict(MockServer())
    with pytest.raises(ConfigurationError) as info:
        act(handle(server, mode).files, verb, root, tmp_path / "out.bin")
    assert info.value.code == "invalid_path" and info.value.operation == OPERATIONS[verb]
    assert "/workspace itself" in str(info.value) and RULE in str(info.value)
    assert server.seen == [] and list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("verb", VERBS)
@pytest.mark.parametrize("path", [
    "/tmp/a.txt", "/", "/workspacex/a.txt", "/etc/passwd", "/workspace/../etc/passwd", "a/../b.txt",
    "..", "./a.txt", "a/./b.txt", "a\\b.txt", "a\x00b.txt", "a\nb.txt", "a\x7fb.txt",
])
def test_outside_and_dotted_paths_are_refused_before_any_request(mode, verb, path, tmp_path):
    server = strict(MockServer())
    with pytest.raises(ConfigurationError) as info:
        act(handle(server, mode).files, verb, path, tmp_path / "out.bin")
    assert info.value.code == "invalid_path" and info.value.operation == OPERATIONS[verb]
    assert repr(path) in str(info.value) and RULE in str(info.value)
    assert server.seen == [] and list(tmp_path.iterdir()) == []  # download_to made no file either


@pytest.mark.parametrize("mode", MODES)
def test_move_sends_both_sides_relative_and_refuses_either_side(mode):
    server = strict(MockServer())
    files = handle(server, mode).files
    run(resolve(files.move("/workspace/a.txt", "/workspace/sub/b.txt")))
    assert server.last.json() == {"from": "a.txt", "to": "sub/b.txt"}
    for src, dst, named in (("/workspace/a.txt", "/tmp/b.txt", "dst '/tmp/b.txt'"),
                            ("../a.txt", "b.txt", "src '../a.txt'")):
        with pytest.raises(ConfigurationError) as info:
            run(resolve(files.move(src, dst)))
        assert info.value.code == "invalid_path" and named in str(info.value)
    assert len(server.seen) == 1


@pytest.mark.parametrize("mode", MODES)
def test_the_refusal_names_the_path_and_the_workspace_rule(mode):
    server = strict(MockServer())
    files = handle(server, mode).files
    with pytest.raises(ConfigurationError) as info:
        run(resolve(files.read("/tmp/notes.txt")))
    assert str(info.value).startswith("sandboxes.files.read: path '/tmp/notes.txt' is outside /workspace; " + RULE)
    with pytest.raises(ConfigurationError) as info:
        run(resolve(files.write(7, "x")))
    assert info.value.code == "invalid_path" and "path must be text, not int" in str(info.value)
    assert server.seen == []


@pytest.mark.parametrize("mode", MODES)
def test_the_strict_mock_refuses_absolute_and_dotted_files_paths_as_the_service_does(mode):
    server = strict(MockServer())
    files = api(server, mode).files
    refused = (
        lambda: files.read(SBX, "/workspace/a.txt"),  # sent as workspace/a.txt: its leading slash is lost
        lambda: files.make_dir(SBX, "/workspace/sub"),
        lambda: files.list(SBX, path="/workspace"),
        lambda: files.list(SBX, path="."),
        lambda: files.rename(SBX, body={"from": "/workspace/a.txt", "to": "b.txt"}),
        lambda: files.rename(SBX, body={"from": "a.txt", "to": "sub/../b.txt"}),
    )
    for call in refused:
        with pytest.raises(ValidationError) as info:
            run(resolve(call()))
        assert info.value.status == 400 and info.value.code == "validation"
    assert len(server.seen) == len(refused)  # each one reached the mock and was refused there
    for call in (lambda: files.read(SBX, "a.txt"), lambda: files.list(SBX), lambda: files.list(SBX, path=""),
                 lambda: files.rename(SBX, body={"from": "a.txt", "to": "sub/b.txt"})):
        run(resolve(call()))
    assert path_refusal("/workspace/a", "path") == "path must be a workspace-relative path."
    assert path_refusal("a/./b", '"to"').startswith('"to" must not contain "." or ".." path segments.')
    assert path_refusal("", "path", root=True) is None and path_refusal("", "path") is not None
