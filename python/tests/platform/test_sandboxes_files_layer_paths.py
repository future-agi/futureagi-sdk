"""``client.sandboxes.files`` paths: the files layer under ``sbx.files`` takes every path as ``sbx.files``
does. A path is relative to ``/workspace``; an absolute path under ``/workspace`` is sent relative
(``/workspace/a.txt`` as ``a.txt``), the root (``/workspace`` itself, ``.`` or an empty path) is sent to the
listing only (as no ``path``), and a path outside ``/workspace``, a ``.`` or ``..`` segment anywhere
(``/workspace/.`` too), a backslash, a control character or a path over 4096 characters is refused with
``ConfigurationError`` (``invalid_path``) before any request. So a file written through one layer is the
file the other reads. A refusal shows the path as given, cut to 200 characters. The mock answers the files
routes as the sandbox service does (``_strict_exec``). Fake credentials only."""

from __future__ import annotations

from urllib.parse import unquote

import pytest
from fi import errors as fe
from fi._core.request import build_path
from fi.generated.platform.policy import OPERATIONS
from fi.sandbox import AsyncSandbox, ConfigurationError, Sandbox

from tests.sandbox_integrations._strict_exec import strict

from ._sandbox_mock import MODES, SBX, MockServer, api, resolve, run

RULE = "sandbox paths are relative to /workspace"


def short(path):
    """A test id that stays short for a long path."""
    return path if len(path) <= 40 else f"{path[:12]}...{len(path)}-chars"
NAMES = {
    "list": "sandboxes.files.list",
    "read": "sandboxes.files.read",
    "write": "sandboxes.files.write",
    "remove": "sandboxes.files.remove",
    "upload": "sandboxes.files.upload",
    "download": "sandboxes.files.download",
    "make_dir": "sandboxes.files.makeDir",
}
CALLS = {
    "list": lambda files, path: files.list(SBX, path=path),
    "read": lambda files, path: files.read(SBX, path),
    "write": lambda files, path: files.write(SBX, path, body={"content": "x", "encoding": "utf8"}),
    "remove": lambda files, path: files.remove(SBX, path),
    "upload": lambda files, path: files.upload(SBX, path, body=b"x"),
    "download": lambda files, path: files.download(SBX, path),
    "make_dir": lambda files, path: files.make_dir(SBX, path),
}


def call(server, mode, verb, path):
    """One ``client.sandboxes.files`` call on ``path``."""
    return run(resolve(CALLS[verb](api(server, mode).files, path)))


def handle(server, mode):
    cls = AsyncSandbox if mode == "async" else Sandbox
    return cls(api(server, mode), {"id": SBX, "state": "active"})


def sent(seen):
    """The path one files request carried: the listing's ``path`` query (None: not sent), else the
    decoded ``{path}`` after the route's verb in the URL."""
    if seen.name == "sandboxes.files.list":
        return seen.request.url.params.get("path")
    raw = seen.request.url.raw_path.decode("ascii").split("?", 1)[0]
    return unquote(raw.split(f"/{SBX}/", 1)[1].split("/", 1)[1])


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("verb", list(CALLS))
@pytest.mark.parametrize("path,wire", [
    ("/workspace/sub/a.txt", "sub/a.txt"),
    ("sub/a.txt", "sub/a.txt"),
    ("//workspace/sub//a.txt/", "sub/a.txt"),
    ("/workspace/.fi-eval/row.json", ".fi-eval/row.json"),
])
def test_the_files_layer_sends_a_workspace_path_relative(mode, verb, path, wire):
    server = strict(MockServer())
    call(server, mode, verb, path)
    assert [seen.name for seen in server.seen] == [NAMES[verb]]
    assert sent(server.last) == wire


@pytest.mark.parametrize("mode", MODES)
def test_what_the_files_layer_writes_is_the_file_the_handle_reads(mode):
    server = strict(MockServer())
    call(server, mode, "write", "/workspace/notes/a.txt")
    sbx = handle(server, mode)
    run(resolve(sbx.files.read("/workspace/notes/a.txt")))
    call(server, mode, "make_dir", "/workspace/notes/old")
    call(server, mode, "remove", "/workspace/notes/old")
    assert [(seen.name, sent(seen)) for seen in server.seen] == [
        ("sandboxes.files.write", "notes/a.txt"),
        ("sandboxes.files.read", "notes/a.txt"),
        ("sandboxes.files.makeDir", "notes/old"),
        ("sandboxes.files.remove", "notes/old"),
    ]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("root", [None, ".", "./", "/workspace", "/workspace/", ""])
def test_the_files_layer_sends_the_root_to_the_listing_as_no_path(mode, root):
    server = strict(MockServer())
    call(server, mode, "list", root)
    assert [seen.name for seen in server.seen] == ["sandboxes.files.list"]
    assert "path" not in server.last.request.url.params


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("verb", [verb for verb in CALLS if verb != "list"])
@pytest.mark.parametrize("root", [".", "/workspace", "/workspace/", ""])
def test_the_files_layer_refuses_the_root_where_the_route_needs_a_file(mode, verb, root):
    server = strict(MockServer())
    with pytest.raises(ConfigurationError) as info:
        call(server, mode, verb, root)
    assert info.value.code == "invalid_path" and info.value.operation == NAMES[verb]
    assert "/workspace itself" in str(info.value) and RULE in str(info.value)
    assert server.seen == []


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("verb", list(CALLS))
@pytest.mark.parametrize("path", [
    "/tmp/a.txt", "/", "/workspacex/a.txt", "/workspace/../etc/passwd", "a/../b.txt", "src/../a.txt",
    "/workspace/.", "/workspace/./a.txt", "./a.txt", "..", "a\\b.txt", "a\x00b.txt", "a\nb.txt",
    "x" * 4097, "/workspace/" + "x" * 4097,
], ids=short)
def test_the_files_layer_refuses_outside_dotted_and_long_paths_before_any_request(mode, verb, path):
    server = strict(MockServer())
    with pytest.raises(ConfigurationError) as info:
        call(server, mode, verb, path)
    assert info.value.code == "invalid_path" and info.value.operation == NAMES[verb]
    assert RULE in str(info.value)
    assert server.seen == []


@pytest.mark.parametrize("mode", MODES)
def test_only_a_path_outside_the_workspace_is_marked_outside(mode):
    """The mark a tool layer reads to tell ``outside_workspace`` from any other refused path."""
    server = strict(MockServer())
    for path, outside in (("/tmp/a.txt", True), ("/workspacex/a", True), ("/", True),
                          ("/tmp/a\\b", True), ("/etc/x\ny", True), ("/workspace/a\\b", False),
                          ("/workspace/../a", False), ("a\\b", False), ("/workspace", False)):
        with pytest.raises(ConfigurationError) as info:
            call(server, mode, "read", path)
        assert (info.value.detail == {"reason": "outside_workspace"}) is outside, path
    assert server.seen == []


def test_a_files_path_with_a_leading_or_doubled_slash_is_refused_by_the_url_builder():
    """The URL builder refuses an empty segment instead of dropping it, rejecting
    ``/workspace/a.txt`` rather than converting it to ``workspace/a.txt``."""
    read = OPERATIONS["sandboxes.files.read"]
    assert build_path(read, {"id": SBX, "path": "dir/a.txt"}).endswith(f"/{SBX}/files/dir/a.txt")
    for path in ("/workspace/a.txt", "/a.txt", "a//b.txt", "a/"):
        with pytest.raises(fe.ConfigurationError) as info:
            build_path(read, {"id": SBX, "path": path})
        assert info.value.code == "invalid_path_param", path


@pytest.mark.parametrize("mode", MODES)
def test_the_handle_refuses_a_dot_segment_after_the_workspace_even_for_the_listing(mode):
    server = strict(MockServer())
    sbx = handle(server, mode)
    for path in ("/workspace/.", "/workspace/./", "/workspace/./src"):
        with pytest.raises(ConfigurationError) as info:
            run(resolve(sbx.files.list(path)))
        assert info.value.code == "invalid_path" and 'has a "." or ".." segment' in str(info.value)
    assert server.seen == []


@pytest.mark.parametrize("mode", MODES)
def test_the_handle_refuses_a_path_over_4096_characters_before_any_request(mode):
    server = strict(MockServer())
    sbx = handle(server, mode)
    for path in ("a" * 4097, "/workspace/" + "a" * 4097, "d/" * 2048 + "a"):
        with pytest.raises(ConfigurationError) as info:
            run(resolve(sbx.files.read(path)))
        assert info.value.code == "invalid_path" and "characters long" in str(info.value)
        assert "takes at most 4096" in str(info.value)
    assert server.seen == []
    run(resolve(sbx.files.read("/workspace/" + "a" * 4096)))  # 4096 after the prefix: sent
    assert sent(server.last) == "a" * 4096


@pytest.mark.parametrize("mode", MODES)
def test_a_refusal_shows_at_most_200_characters_of_the_path(mode):
    server = strict(MockServer())
    sbx = handle(server, mode)
    long_outside = "/tmp/" + "x" * 100_000
    for path in (long_outside, "a\\" + "y" * 5000, "z" * 5000):
        with pytest.raises(ConfigurationError) as info:
            run(resolve(sbx.files.read(path)))
        text = str(info.value)
        assert repr(path[:200] + "...") in text and path[:201] not in text
        assert len(text) < 600
    with pytest.raises(ConfigurationError) as info:
        run(resolve(sbx.files.read("/tmp/" + "x" * 195)))  # 200 characters: shown whole
    assert repr("/tmp/" + "x" * 195) in str(info.value) and "..." not in str(info.value)
    assert server.seen == []
