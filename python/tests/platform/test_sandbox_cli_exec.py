"""The ``sandbox exec`` command (contract v1 section 5, v2 item 6): output streamed as it arrives,
the exit codes (the command's own code, 124 timeout, 128+N signal, 130 cancelled, 1 when it could
not start or completion is unknown), Ctrl-C cancelling a running command, json frames, and the
``--`` that separates the command from this tool's options. Fake credentials only."""

from __future__ import annotations

import json

import httpx
import pytest

from ._sandbox_cli_support import (  # noqa: F401 (registers the server fixture)
    LOCAL,
    exec_body,
    names,
    refuse,
    run,
    server_fixture,
)
from ._sandbox_mock import EXEC, EXIT0, SBX, Chunks, stream_response


def test_exec_streams_stdout_and_stderr_and_exits_with_the_commands_code(server, capsys):
    server.on("sandboxes.commands.run", exec_body(
        ("stdout", {"data": "héllo\n"}), ("stderr", {"data": "warn\n"}), ("exit", {**EXIT0, "exitCode": 3}),
        chunks=lambda data: [bytes([b]) for b in data]))
    assert run("exec", SBX, "--", "python3", "app.py") == 3
    captured = capsys.readouterr()
    assert captured.out == "héllo\n" and captured.err == "warn\n"
    assert server.last.json() == {"command": "python3 app.py"}
    assert names(server) == ["sandboxes.commands.run"]


def test_exec_sends_cwd_env_timeout_and_quotes_separate_words(server, capsys):
    assert run("exec", "--cwd", "src", "--env", "A=1", "--env", "B=x=y", "--timeout", "9", SBX,
               "--", "ls", "-la", "my dir") == 0
    assert server.last.json() == {"command": "ls -la 'my dir'", "cwd": "src", "env": {"A": "1", "B": "x=y"},
                                  "timeoutSeconds": 9}
    assert run("exec", SBX, "--", "echo $HOME | wc -c && true") == 0
    assert server.last.json() == {"command": "echo $HOME | wc -c && true"}


@pytest.mark.parametrize("wire,code,says", [
    ({"exitCode": 0}, 0, None),
    ({"exitCode": 42}, 42, None),
    ({"exitCode": None, "signal": "SIGKILL", "timedOut": True, "durationMs": 9000}, 124, "time limit"),
    ({"exitCode": None, "signal": "SIGTERM", "cancelled": True}, 130, "cancelled"),
    ({"exitCode": None, "signal": "SIGTERM"}, 143, "SIGTERM"),
    ({"exitCode": None, "signal": "SIGKILL"}, 137, "SIGKILL"),
    ({"exitCode": None, "signal": "KILL"}, 137, "KILL"),
    ({"exitCode": None, "signal": "9"}, 137, None),
    ({"exitCode": None, "signal": "SIGSEGV"}, 139, None),
    ({"exitCode": None, "error": "spawn /bin/nope ENOENT"}, 1, "could not start"),
    ({"exitCode": None, "signal": "SIGNOPE"}, 1, "SIGNOPE"),
])
def test_exec_exit_codes(server, capsys, wire, code, says):
    server.on("sandboxes.commands.run", exec_body(("stdout", {"data": "so far"}), ("exit", {**EXIT0, **wire})))
    assert run("exec", SBX, "--", "x") == code
    captured = capsys.readouterr()
    assert captured.out == "so far"
    if says:
        assert says in captured.err
    assert names(server) == ["sandboxes.commands.run"]


def test_exec_notes_truncated_output(server, capsys):
    server.on("sandboxes.commands.run", exec_body(("exit", {**EXIT0, "truncated": True})))
    assert run("exec", SBX, "--", "x") == 0
    assert "dropped some of the output" in capsys.readouterr().err


@pytest.mark.parametrize("body,code", [
    (exec_body(("stdout", {"data": "a"}), ("error", {"message": "runtime died"})), "command_failed"),
    (exec_body(("stdout", {"data": "partial"}), chunks=lambda data: [data, b"event: exit\ndata: {"]),
     "command_incomplete"),
    (exec_body(("stdout", {"data": "partial"}), fail=httpx.ReadError("reset")), "connection_lost"),
])
def test_exec_without_a_clean_exit_says_completion_is_unknown_and_exits_1(server, capsys, body, code):
    server.on("sandboxes.commands.run", body)
    assert run("exec", SBX, "--", "long") == 1
    err = capsys.readouterr().err
    assert err.splitlines()[-1].startswith(f"{code}: ") and "unknown" in err
    assert names(server) == ["sandboxes.commands.run"]


def test_exec_refused_by_the_server_exits_1_and_is_not_retried(server, capsys):
    server.on("sandboxes.commands.run", refuse(409, "sandbox_hibernated", detail={"state": "hibernated"}))
    assert run("exec", SBX, "--", "ls") == 1
    err = capsys.readouterr().err
    assert err.startswith("sandbox_hibernated: ") and "resume" in err
    assert names(server) == ["sandboxes.commands.run"]


def test_exec_json_prints_each_frame_as_one_line(server, capsys):
    server.on("sandboxes.commands.run", exec_body(("stdout", {"data": "hi\n"}), ("exit", {**EXIT0, "exitCode": 5})))
    assert run("exec", SBX, "--json", "--", "x") == 5
    frames = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [frame["event"] for frame in frames] == ["started", "stdout", "exit"]
    assert frames[1]["data"] == {"data": "hi\n"} and frames[2]["data"]["exitCode"] == 5


def test_ctrl_c_during_exec_cancels_the_command_and_exits_130(server, capsys):
    server.on("sandboxes.commands.run", exec_body(("stdout", {"data": "working\n"}), fail=KeyboardInterrupt()))
    assert run("exec", SBX, "--", "sleep 600") == 130
    captured = capsys.readouterr()
    assert captured.out == "working\n" and "Cancelled." in captured.err
    assert names(server) == ["sandboxes.commands.run", "sandboxes.commands.cancel"]
    assert server.last.request.method == "POST"
    assert str(server.last.request.url) == f"{LOCAL}/workspace/sandboxes/{SBX}/exec/{EXEC}/cancel"


def test_ctrl_c_before_the_command_started_exits_130_without_a_cancel_call(server, capsys):
    server.on("sandboxes.commands.run", lambda request: stream_response(Chunks([], fail=KeyboardInterrupt())))
    assert run("exec", SBX, "--", "sleep 600") == 130
    assert "before the command started" in capsys.readouterr().err
    assert names(server) == ["sandboxes.commands.run"]


def test_ctrl_c_exits_130_when_the_cancel_request_fails(server, capsys):
    server.on("sandboxes.commands.run", exec_body(fail=KeyboardInterrupt()))
    server.on("sandboxes.commands.cancel", refuse(404, "not_found"))
    assert run("exec", SBX, "--", "sleep 600") == 130
    assert "cancel request failed (not_found" in capsys.readouterr().err


def test_exec_without_dashes_says_where_the_command_goes_and_sends_nothing(server, capsys):
    assert run("exec", SBX, "ls", "-la") == 2
    err = capsys.readouterr().err
    assert "exec_usage: put the command after --" in err and f"exec {SBX} -- ls -la" in err
    assert "unrecognized arguments" not in err and server.seen == []


@pytest.mark.parametrize("argv", [
    ("sandbox", "exec", "--cwd", "src", SBX, "--timeout=5", "--json", "ls"),
    ("sandbox", "exec", SBX, "--env", "A=1", "ls"),
    ("sandbox", "exec", SBX, "--", "ls", "-la"),
    ("sandbox", "exec", SBX, "ls", "--help"),
    ("sandbox", "ls", SBX, "-r"),
    ("agents", "exec", SBX, "ls", "-la"),
])
def test_the_dashes_check_leaves_everything_else_to_argparse(argv):
    from fi._cli import sandbox as cli

    assert cli._exec_needs_dashes(list(argv)) is None
