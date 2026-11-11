"""Every next step the ``sandbox`` commands print is a command to type: the program name (the root
parser's prog), ``sandbox`` and its words, as in ``<prog> sandbox resume ID``; never argparse's
usage line ("[-h] [--version] COMMAND ..."), in a refusal, a note, the exec usage hint or the help
examples. Fake credentials only."""

from __future__ import annotations

import pytest
from fi._cli import main as cli_main

from ._sandbox_cli_support import (  # noqa: F401 (registers the server fixture)
    answer,
    file_answer,
    refuse,
    run,
    server_fixture,
)
from ._sandbox_mock import SBX, SNAP

HIBERNATED = {"detail": {"state": "hibernated"}}


@pytest.fixture(name="prog")
def prog_fixture(server):
    """The root parser's prog (the console script's name, renamed or not) and this group."""
    return cli_main.build_parser(warn=lambda message: None).prog + " sandbox"


def plain(text):
    """No usage text and no doubled full stop."""
    return "[-h]" not in text and "COMMAND ..." not in text and ".." not in text


@pytest.mark.parametrize("operation,argv", [
    ("sandboxes.files.upload", ("cp", "LOCAL", f"{SBX}:a.txt")),
    ("sandboxes.commands.run", ("exec", SBX, "--", "ls")),
    ("sandboxes.files.read", ("cat", SBX, "a.txt")),
    ("sandboxes.files.list", ("ls", SBX)),
    ("sandboxes.snapshots.create", ("snapshot", "create", SBX)),
])
def test_a_hibernated_sandbox_names_the_resume_command(server, capsys, tmp_path, prog, operation, argv):
    local = tmp_path / "a.txt"
    local.write_text("x", encoding="utf-8")
    server.on(operation, refuse(409, "sandbox_hibernated", **HIBERNATED))
    assert run(*(str(local) if word == "LOCAL" else word for word in argv)) == 1
    err = capsys.readouterr().err
    assert err.startswith("sandbox_hibernated: ") and plain(err), err
    assert err.rstrip("\n").endswith(f". It is hibernated; start it first with: {prog} resume {SBX}"), err


@pytest.mark.parametrize("operation,status,code,argv,step", [
    ("sandboxes.networkPolicy.update", 412, "network_policy_revision_mismatch",
     ("network-policy", "set", SBX, "--file", "POLICY", "--if-match", '"1"'),
     "see it with: {prog} network-policy get {sbx}, then try again"),
    ("sandboxes.files.list", 404, "not_found", ("ls", SBX, "nope"),
     "Check the path, and the sandbox id with: {prog} list"),
    ("sandboxes.getInfo", 404, "not_found", ("get", SBX),
     "check the id with: {prog} list, and FI_WORKSPACE_ID"),
    ("sandboxes.snapshots.restore", 404, "not_found", ("snapshot", "restore", SBX, SNAP),
     "Check the snapshot id with: {prog} snapshot list {sbx}"),
])
def test_every_refusal_hint_is_a_command_to_type(server, capsys, tmp_path, prog, operation, status, code,
                                                  argv, step):
    policy = tmp_path / "policy.json"
    policy.write_text('{"mode": "deny-all"}', encoding="utf-8")
    server.on(operation, refuse(status, code))
    assert run(*(str(policy) if word == "POLICY" else word for word in argv)) == 1
    err = capsys.readouterr().err
    assert err.startswith(f"{code}: ") and plain(err), err
    assert step.format(prog=prog, sbx=SBX) in err, err


def test_every_note_names_a_command_to_type(server, capsys, prog):
    server.on("sandboxes.list", answer(200, json={"schemaVersion": "omega-workspace-sandboxes/v1", "caps": {},
                                                  "sandboxes": []}))
    assert run("list") == 0
    err = capsys.readouterr().err
    assert f"Create one with: {prog} create --name NAME" in err and plain(err), err
    server.on("sandboxes.snapshots.list", answer(200, json={"schemaVersion": "v1", "snapshots": []}))
    assert run("snapshot", "list", SBX) == 0
    err = capsys.readouterr().err
    assert f"Save one with: {prog} snapshot create {SBX}" in err and plain(err), err
    server.on("sandboxes.files.read", file_answer("partial", truncated=True))
    assert run("cat", SBX, "f") == 0
    err = capsys.readouterr().err
    assert f"Copy all of it with: {prog} cp {SBX}:f LOCAL_FILE" in err and plain(err), err


def test_the_exec_usage_hint_names_the_command(server, capsys, prog):
    assert run("exec", SBX, "ls", "-la") == 2
    err = capsys.readouterr().err
    assert err.startswith(f"usage: {prog} exec [options] SANDBOX_ID -- COMMAND...\n"), err
    assert f"for example: {prog} exec {SBX} -- ls -la" in err and "[-h]" not in err
    assert server.seen == []


def test_help_and_its_examples_name_the_command(server, capsys, prog):
    assert run("--help") == 0
    out = capsys.readouterr().out
    assert out.startswith(f"usage: {prog} [-h]") and f"  {prog} create --name scratch" in out
    assert "COMMAND ... sandbox" not in out and "[--version]" not in out
    assert run("exec", "--help") == 0
    out = capsys.readouterr().out
    assert out.startswith(f"usage: {prog} exec [options] SANDBOX_ID -- COMMAND...")
    assert run("snapshot", "restore", "--help") == 0
    assert capsys.readouterr().out.startswith(f"usage: {prog} snapshot restore ")
