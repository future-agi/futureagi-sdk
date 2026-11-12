"""The ``sandbox`` file commands send every sandbox path relative to ``/workspace``, as the files routes take
it (an absolute path under ``/workspace`` is sent relative; a leading slash would get a 400): ``cat``, which
reads through the generated layer for the record's ``truncated`` and ``encoding``, as well as ``ls``, ``rm``,
``mv``, ``mkdir`` and ``cp``, which go through the handle. So ``/workspace/a.txt`` written by one command is
the file another reads. A path outside ``/workspace`` is refused (``invalid_path``, exit 2) before any
request. The mock answers the files routes as the sandbox service does (``_strict_exec``), so a wrong path
fails here. Fake credentials only."""

from __future__ import annotations

from urllib.parse import unquote

import pytest

from tests.sandbox_integrations._strict_exec import strict

from ._sandbox_cli_support import (  # noqa: F401 (registers the server fixture)
    answer,
    file_answer,
    names,
    run,
    server_fixture,
)
from ._sandbox_mock import SBX


def url_path(seen):
    """``files/<path>``, ``upload/<path>`` or ``folders/<path>`` of a files request, decoded."""
    raw = seen.request.url.raw_path.decode("ascii").split("?", 1)[0]
    return unquote(raw.split(f"/{SBX}/", 1)[1])


@pytest.mark.parametrize("path,sent", [
    ("/workspace/notes.txt", "files/notes.txt"),
    ("notes.txt", "files/notes.txt"),
    ("/workspace/logs/run.log", "files/logs/run.log"),
])
def test_cat_sends_the_path_relative_to_the_workspace(server, capsys, path, sent):
    strict(server).on("sandboxes.files.read", file_answer("hello\n"))
    assert run("cat", SBX, path) == 0
    assert capsys.readouterr().out == "hello\n"
    assert names(server) == ["sandboxes.files.read"] and url_path(server.last) == sent


@pytest.mark.parametrize("path", ["/tmp/x", "/etc/passwd", "/workspace/../etc/passwd", "a\\b.txt", "/workspace"])
def test_cat_refuses_a_path_outside_the_workspace_before_any_request(server, capsys, path):
    strict(server)
    assert run("cat", SBX, path) == 2
    err = capsys.readouterr().err
    assert err.startswith(f"invalid_path: sandboxes.files.read: path {path!r} ")
    assert "sandbox paths are relative to /workspace" in err
    assert server.seen == []


def test_what_cp_writes_under_workspace_is_what_cat_reads(server, capsys, tmp_path):
    local = tmp_path / "a.txt"
    local.write_text("hello\n", encoding="utf-8")
    strict(server).on("sandboxes.files.read", file_answer("hello\n"))
    assert run("cp", str(local), f"{SBX}:/workspace/out/a.txt") == 0
    assert run("cat", SBX, "/workspace/out/a.txt") == 0
    assert capsys.readouterr().out.endswith("hello\n")
    assert [url_path(seen) for seen in server.seen] == ["upload/out/a.txt", "files/out/a.txt"]


def test_ls_rm_mv_mkdir_send_workspace_paths_relative(server, capsys):
    strict(server).on("sandboxes.files.list", answer(200, json={"schemaVersion": "v1", "path": ".", "entries": []}))
    assert run("ls", SBX, "/workspace") == 0
    assert "path" not in server.last.request.url.params  # the top folder: no path
    assert run("ls", SBX, "/workspace/src") == 0
    assert server.last.request.url.params["path"] == "src"
    assert run("rm", SBX, "/workspace/old.txt") == 0
    assert url_path(server.last) == "files/old.txt"
    assert run("mv", SBX, "/workspace/a.txt", "/workspace/b/a.txt") == 0
    assert server.last.json() == {"from": "a.txt", "to": "b/a.txt"}
    assert run("mkdir", SBX, "/workspace/data/raw") == 0
    assert url_path(server.last) == "folders/data/raw"
    assert names(server) == ["sandboxes.files.list", "sandboxes.files.list", "sandboxes.files.remove",
                             "sandboxes.files.rename", "sandboxes.files.makeDir"]
