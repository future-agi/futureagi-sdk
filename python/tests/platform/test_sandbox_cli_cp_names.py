"""``cp SANDBOX_ID:PATH LOCAL_DIR`` names the local file from the last part of PATH, with both ``/``
and ``\\`` as separators on every system, and refuses (exit 2, before any request or write) a name
that is empty, ``.`` or ``..``, names a drive, or resolves outside LOCAL_DIR. These checks keep
writes inside the destination when a script copies names from a sandbox listing (Linux allows
backslashes in names). A sandbox path with a backslash is refused too (``invalid_path``, exit 2, before any
request or write): the files routes take only ``/workspace``-relative paths, with ``/`` between
folders. Fake credentials only."""

from __future__ import annotations

import os

import pytest
from fi._cli import sandbox as group

from ._sandbox_cli_support import (  # noqa: F401 (registers the server fixture)
    names,
    run,
    server_fixture,
)
from ._sandbox_mock import SBX


@pytest.mark.parametrize("remote,name", [
    ("out/result.bin", "result.bin"),
    ("/workspace/out/result.bin", "result.bin"),
    ("x:y/evil.txt", "evil.txt"),
])
def test_the_last_part_lands_inside_the_folder(server, capsys, tmp_path, remote, name):
    folder = tmp_path / "into"
    folder.mkdir()
    assert run("cp", f"{SBX}:{remote}", str(folder)) == 0
    assert sorted(p.name for p in folder.iterdir()) == [name]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["into"]
    assert (folder / name).read_bytes() == b"file-bytes"
    assert names(server) == ["sandboxes.files.download"]


@pytest.mark.parametrize("remote", [
    "dir\\evil.txt", "..\\..\\evil.txt", "a\\b/c\\d.txt", "\\abs\\evil.txt", "x:y\\evil.txt",
])
def test_a_backslash_in_the_sandbox_path_is_refused_before_any_request(server, capsys, tmp_path, remote):
    folder = tmp_path / "into"
    folder.mkdir()
    assert run("cp", f"{SBX}:{remote}", str(folder)) == 2
    captured = capsys.readouterr()
    assert captured.err.startswith("invalid_path: ") and "relative to /workspace" in captured.err
    assert server.seen == [] and list(folder.iterdir()) == []


@pytest.mark.parametrize("remote", [
    "a/..", "a\\..", "..", "a\\.", "dir\\", "C:", "D:evil.txt", "x/D:evil.txt", "dir\\d:x",
])
def test_an_unsafe_name_is_refused_before_any_request_or_write(server, capsys, tmp_path, remote):
    assert run("cp", f"{SBX}:{remote}", str(tmp_path)) == 2
    captured = capsys.readouterr()
    assert captured.err.startswith("unsafe_file_name: ") and "LOCAL_FILE" in captured.err
    assert server.seen == [] and list(tmp_path.iterdir()) == []


def test_a_link_in_the_folder_that_points_outside_is_refused(server, capsys, tmp_path):
    folder, outside = tmp_path / "into", tmp_path / "outside.txt"
    folder.mkdir()
    outside.write_bytes(b"untouched")
    try:
        os.symlink(outside, folder / "result.bin")
    except (OSError, NotImplementedError):
        pytest.skip("this system cannot make a symbolic link here")
    assert run("cp", f"{SBX}:out/result.bin", str(folder)) == 2
    assert capsys.readouterr().err.startswith("unsafe_file_name: ")
    assert server.seen == [] and outside.read_bytes() == b"untouched"


def test_a_named_local_file_is_written_as_given(server, capsys, tmp_path):
    target = tmp_path / "chosen.bin"
    assert run("cp", f"{SBX}:x/D:evil.txt", str(target)) == 0  # an unsafe name, but the file is named
    assert target.read_bytes() == b"file-bytes" and [p.name for p in tmp_path.iterdir()] == ["chosen.bin"]


@pytest.mark.parametrize("remote,ok", [
    ("plain.txt", True), ("a\\b.txt", True), ("..", False), ("Z:", False), ("\\", False),
])
def test_the_name_rule_itself(tmp_path, remote, ok):
    if ok:
        target = group._inside(str(tmp_path), SBX, remote)
        assert os.path.dirname(target) == str(tmp_path)
        return
    with pytest.raises(group._Usage) as caught:
        group._inside(str(tmp_path), SBX, remote)
    assert caught.value.code == "unsafe_file_name"
