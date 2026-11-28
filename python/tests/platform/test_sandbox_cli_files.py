"""The ``sandbox`` file, snapshot and network-policy commands (contract v1 section 5, v2 item 6):
cp both ways (a download is renamed only when complete), ls, cat (text, binary, cut short), rm,
mv, mkdir, snapshot create / list / restore, and network-policy get / set with its ETag. Fake
credentials only."""

from __future__ import annotations

import io
import json
import sys

import pytest

from ._sandbox_cli_support import (  # noqa: F401 (registers the server fixture)
    LOCAL,
    OTHER,
    answer,
    file_answer,
    names,
    record,
    refuse,
    run,
    server_fixture,
)
from ._sandbox_mock import ETAG, SBX, SNAP

# --- files -----------------------------------------------------------------------------------


def test_cp_uploads_a_local_file_keeping_its_name_under_a_folder(server, capsys, tmp_path):
    local = tmp_path / "data.csv"
    local.write_bytes(b"a,b\n1,2\n")
    server.on("sandboxes.files.upload", answer(200, json={
        "schemaVersion": "v1", "file": {"path": "in/data.csv", "bytes": 8, "modifiedAt": "2026-11-11T00:00:00Z"}}))
    assert run("cp", str(local), f"{SBX}:in/") == 0
    assert capsys.readouterr().out == f"Copied {local} to {SBX}:in/data.csv (8 bytes).\n"
    assert server.last.name == "sandboxes.files.upload" and server.last.body == b"a,b\n1,2\n"
    assert server.last.request.method == "PUT" and "data.csv" in str(server.last.request.url)
    assert run("cp", str(local), f"{SBX}:renamed.csv", "--json") == 0
    assert json.loads(capsys.readouterr().out)["bytes"] == 8


def test_cp_downloads_into_a_file_or_a_folder(server, capsys, tmp_path):
    assert run("cp", f"{SBX}:out/result.bin", str(tmp_path)) == 0
    target = tmp_path / "result.bin"
    assert target.read_bytes() == b"file-bytes"
    assert capsys.readouterr().out == f"Copied {SBX}:out/result.bin to {target} (10 bytes).\n"
    named = tmp_path / "named.bin"
    assert run("cp", f"{SBX}:out/result.bin", str(named), "--json") == 0
    assert json.loads(capsys.readouterr().out) == {"from": f"{SBX}:out/result.bin", "to": str(named), "bytes": 10}
    assert names(server) == ["sandboxes.files.download"] * 2


def test_cp_download_refused_leaves_no_partial_file(server, capsys, tmp_path):
    server.on("sandboxes.files.download", refuse(404, "not_found"))
    assert run("cp", f"{SBX}:missing.txt", str(tmp_path / "missing.txt")) == 1
    assert capsys.readouterr().err.startswith("not_found: ")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("argv", [
    ("a.txt", "b.txt"), (f"{SBX}:a", f"{OTHER}:b"), ("/no/such/file.txt", f"{SBX}:x"), (f"{SBX}:", "out.txt"),
])
def test_cp_usage_errors_exit_2_before_sending(server, capsys, tmp_path, monkeypatch, argv):
    monkeypatch.chdir(tmp_path)
    assert run("cp", *argv) == 2
    assert server.seen == []


def test_remote_spelling_is_sandbox_id_colon_path():
    from fi._cli import sandbox as cli

    assert cli._remote(f"{SBX}:a/b.txt") == (SBX, "a/b.txt")
    for local in ("C:/x.txt", "C:\\x.txt", "./a:b", "dir/a:b", "plain.txt"):
        assert cli._remote(local) is None, local


def test_ls_text_and_json(server, capsys):
    entries = [{"name": "a.py", "size": 12, "mode": "0644", "directory": False},
               {"name": "lib", "size": 0, "mode": "0755", "directory": True}]
    server.on("sandboxes.files.list", answer(200, json={"schemaVersion": "v1", "path": "src",
                                                                "entries": entries}))
    assert run("ls", SBX, "src") == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].split() == ["12", "a.py"] and lines[1].split() == ["-", "lib/"]
    assert server.last.request.url.params["path"] == "src"
    assert run("ls", SBX, "--json") == 0
    assert json.loads(capsys.readouterr().out) == entries
    assert "path" not in server.last.request.url.params  # the top folder: no path (the route refuses ".")



def test_cat_prints_a_text_file_and_json_prints_the_record(server, capsys):
    server.on("sandboxes.files.read", file_answer("hello\n"))
    assert run("cat", SBX, "notes.txt") == 0
    assert capsys.readouterr().out == "hello\n"
    assert run("cat", SBX, "notes.txt", "--max-bytes", "5", "--json") == 0
    assert json.loads(capsys.readouterr().out)["content"] == "hello\n"
    assert server.last.request.url.params["maxBytes"] == "5"


def test_cat_writes_binary_bytes_as_they_are(server, capsysbinary):
    import base64

    data = b"\x00\xffbinary"
    server.on("sandboxes.files.read", file_answer(base64.b64encode(data).decode(), encoding="base64"))
    assert run("cat", SBX, "blob.bin") == 0
    assert capsysbinary.readouterr().out == data


def test_cat_says_when_the_file_was_cut_short(server, capsys):
    server.on("sandboxes.files.read", file_answer("partial", truncated=True))
    assert run("cat", SBX, "big.log") == 0
    captured = capsys.readouterr()
    assert captured.out == "partial" and f"cp {SBX}:big.log" in captured.err


def test_rm_mv_mkdir(server, capsys):
    assert run("rm", SBX, "old.txt") == 0
    assert capsys.readouterr().out == f"Deleted {SBX}:old.txt.\n"
    assert "recursive" not in server.last.request.url.params
    assert run("rm", "-r", SBX, "build", "--json") == 0
    assert server.last.request.url.params["recursive"].lower() == "true"
    assert "path" in json.loads(capsys.readouterr().out)
    assert run("mv", SBX, "a.txt", "b.txt") == 0
    assert capsys.readouterr().out == f"Moved a.txt to b.txt in {SBX}.\n"
    assert server.last.json() == {"from": "a.txt", "to": "b.txt"}
    assert run("mkdir", SBX, "data/raw") == 0
    assert capsys.readouterr().out == f"Created the folder {SBX}:data/raw.\n"
    assert run("mkdir", SBX, "data/raw", "--json") == 0
    assert "path" in json.loads(capsys.readouterr().out)
    assert names(server) == ["sandboxes.files.remove", "sandboxes.files.remove", "sandboxes.files.rename",
                             "sandboxes.files.makeDir", "sandboxes.files.makeDir"]


# --- snapshots -------------------------------------------------------------------------------


SNAPSHOT = {"id": SNAP, "sandboxId": SBX, "createdAt": "2026-11-11T00:00:00Z", "kind": "files",
            "statement": "s", "contentAddress": "sha256:0"}


def test_snapshot_create_list_and_restore(server, capsys):
    server.on("sandboxes.snapshots.create", answer(201, json={"schemaVersion": "v1", "snapshot": SNAPSHOT}))
    server.on("sandboxes.snapshots.list", answer(200, json={"schemaVersion": "v1", "snapshots": [SNAPSHOT]}))
    server.on("sandboxes.snapshots.restore", answer(201, json=record(ident=OTHER)))
    assert run("snapshot", "create", SBX) == 0
    assert capsys.readouterr().out == SNAP + "\n"
    assert run("snapshot", "list", SBX) == 0
    assert SNAP in capsys.readouterr().out
    assert run("snapshot", "list", SBX, "--json") == 0
    assert json.loads(capsys.readouterr().out) == [SNAPSHOT]
    assert run("snapshot", "restore", SBX, SNAP) == 0
    assert capsys.readouterr().out == OTHER + "\n"
    assert str(server.last.request.url) == f"{LOCAL}/workspace/sandboxes/{SBX}/snapshots/{SNAP}/restore"
    assert run("snapshot", "restore", SBX, SNAP, "--json") == 0
    assert json.loads(capsys.readouterr().out)["id"] == OTHER
    assert names(server) == ["sandboxes.snapshots.create", "sandboxes.snapshots.list", "sandboxes.snapshots.list",
                             "sandboxes.snapshots.restore", "sandboxes.snapshots.restore"]


# --- network policy --------------------------------------------------------------------------


def test_network_policy_get_shows_the_etag(server, capsys):
    assert run("network-policy", "get", SBX) == 0
    assert f"ETag: {ETAG}" in capsys.readouterr().out
    assert run("network-policy", "get", SBX, "--json") == 0
    body = json.loads(capsys.readouterr().out)
    assert body["etag"] == ETAG and "desiredRevision" in body["policy"]


@pytest.fixture
def policy_file(tmp_path):
    path = tmp_path / "policy.json"
    path.write_text(json.dumps({"mode": "allow-list", "allow": [{"host": "pypi.org"}]}), encoding="utf-8")
    return path


def test_network_policy_set_with_if_match_sends_it(server, capsys, policy_file):
    assert run("network-policy", "set", SBX, "--file", str(policy_file), "--if-match", '"3"') == 0
    assert names(server) == ["sandboxes.networkPolicy.update"]
    assert server.last.request.headers["if-match"] == '"3"'
    assert server.last.json() == {"mode": "allow-list", "allow": [{"host": "pypi.org"}]}
    assert f"ETag: {ETAG}" in capsys.readouterr().out


def test_network_policy_set_without_if_match_reads_first(server, capsys, policy_file, monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO(policy_file.read_text(encoding="utf-8")))
    assert run("network-policy", "set", SBX, "--file", "-", "--json") == 0
    assert names(server) == ["sandboxes.networkPolicy.get", "sandboxes.networkPolicy.update"]
    assert server.last.request.headers["if-match"] == ETAG
    assert json.loads(capsys.readouterr().out)["etag"] == ETAG


def test_a_stale_etag_is_a_refusal_that_is_not_retried(server, capsys, policy_file):
    server.on("sandboxes.networkPolicy.update", refuse(412, "network_policy_revision_mismatch"))
    assert run("network-policy", "set", SBX, "--file", str(policy_file), "--if-match", '"1"') == 1
    err = capsys.readouterr().err
    assert err.startswith("network_policy_revision_mismatch: ") and "network-policy get" in err
    assert names(server) == ["sandboxes.networkPolicy.update"]


@pytest.mark.parametrize("content,code", [(None, "local_file_not_found"), ("{not json", "invalid_policy_file"),
                                          ("[1, 2]", "invalid_policy_file")])
def test_a_bad_policy_file_is_a_usage_error(server, capsys, tmp_path, content, code):
    path = tmp_path / "policy.json"
    if content is not None:
        path.write_text(content, encoding="utf-8")
    assert run("network-policy", "set", SBX, "--file", str(path)) == 2
    assert capsys.readouterr().err.startswith(f"{code}: ")
    assert server.seen == []


def test_cp_into_a_hibernated_sandbox_says_how_to_resume_it(server, capsys, tmp_path):
    local = tmp_path / "a.txt"
    local.write_text("x", encoding="utf-8")
    server.on("sandboxes.files.upload", refuse(409, "sandbox_hibernated", detail={"state": "hibernated"}))
    assert run("cp", str(local), f"{SBX}:a.txt") == 1
    err = capsys.readouterr().err
    assert err.startswith("sandbox_hibernated: ") and f"resume {SBX}" in err and ".." not in err


def test_a_missing_path_points_at_the_path_not_the_sandbox(server, capsys):
    server.on("sandboxes.files.list", refuse(404, "not_found"))
    assert run("ls", SBX, "nope") == 1
    err = capsys.readouterr().err
    assert err.startswith("not_found: ") and "Check the path" in err and "No sandbox" not in err
