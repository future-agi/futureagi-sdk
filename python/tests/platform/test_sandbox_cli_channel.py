"""``sandbox rsh``, ``ssh``, ``rsync`` and ``scp`` against the fake channel server: byte-exact
standard streams, the remote exit code, every close code as an exit message, the refusals of the
mint, the tty restored on every exit of ``ssh``, and the system tools named when missing."""

from __future__ import annotations

import io
import os
import subprocess
import sys
import threading
import time

import pytest
from fi._cli import main as cli_main
from fi._cli import registry

from ._channel_fake import BEARER, SBX, FakeChannel
from ._channel_support import channel_fixture  # noqa: F401
from ._sandbox_cli_support import _EP, ENV


@pytest.fixture(name="cli")
def cli_fixture(channel, monkeypatch):
    for name in ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OMEGA_BASE_URL", channel.base_url)
    monkeypatch.setenv("FUTUREAGI_OMEGA_API_KEY", BEARER)
    monkeypatch.setattr(registry, "entry_points", lambda: [_EP()])
    return channel


def run(*argv):
    return cli_main.main(["sandbox", *argv])


def feed(monkeypatch, data: bytes):
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(data)))


# -- rsh ----------------------------------------------------------------------------------------


def test_rsh_pipes_stdin_stdout_and_stderr_byte_exact(cli, monkeypatch, capsysbinary):
    payload = bytes(range(256)) * 40 + b"\x00\x00"
    feed(monkeypatch, payload)
    code = run("rsh", SBX, "--", "sh", "-c", "cat; printf 'to-err\\000bytes' >&2")
    captured = capsysbinary.readouterr()
    assert code == 0
    assert captured.out == payload and captured.err == b"to-err\x00bytes"


def test_rsh_exits_with_the_remote_code_and_works_without_dashes(cli, monkeypatch, capsysbinary):
    feed(monkeypatch, b"")
    assert run("rsh", SBX, "sh", "-c", "echo hi; exit 7") == 7
    assert capsysbinary.readouterr().out == b"hi\n"


def test_rsh_keeps_the_commands_options_after_the_id(cli, monkeypatch, capsysbinary):
    feed(monkeypatch, b"")
    assert run("rsh", SBX, "printf", "%s", "--server", "-vlogDtpre.iLsfxCIvu", ".", "dest/") == 0
    assert capsysbinary.readouterr().out == b"--server-vlogDtpre.iLsfxCIvu.dest/"


def test_rsh_drops_the_empty_host_word_rsync_passes(cli, monkeypatch, capsysbinary):
    feed(monkeypatch, b"")
    assert run("rsh", SBX, "", "printf", "ok") == 0
    assert capsysbinary.readouterr().out == b"ok"


def test_rsh_signal_and_time_limit_exit_codes(cli, monkeypatch, capsysbinary):
    feed(monkeypatch, b"")
    assert run("rsh", SBX, "--", "sh", "-c", "kill -9 $$") == 137
    feed(monkeypatch, b"")
    assert run("rsh", "--timeout", "1", SBX, "--", "sleep", "30") == 124


def test_rsh_ssh_style_skips_ssh_options_and_runs_the_line_in_a_shell(cli, monkeypatch, capsysbinary):
    feed(monkeypatch, b"")
    code = run("rsh", "--ssh-style", SBX, "--", "-x", "-oForwardAgent=no", "-p", "22", "--", SBX,
               "echo", "'a b'", ";", "echo", "err", ">&2")
    captured = capsysbinary.readouterr()
    assert code == 0 and captured.out == b"a b\n" and captured.err == b"err\n"


def test_rsh_runs_in_the_cwd_given(cli, monkeypatch, capsysbinary):
    feed(monkeypatch, b"")
    assert run("rsh", "--cwd", "sub", SBX, "--", "pwd") == 0
    assert capsysbinary.readouterr().out.strip() == str(cli.root / "sub").encode()


@pytest.mark.parametrize("code,reason,says", [
    (4401, "access_revoked", "access"),
    (4404, "sandbox_gone", "deleted"),
    (4409, "emergency_stop", "stopped"),
    (4410, "sandbox_hibernated", "hibernated"),
    (4411, "sandbox_frozen", "frozen"),
    (1001, "server_stopping", "shutting down"),
])
def test_every_close_code_is_an_exit_message(cli, monkeypatch, capsysbinary, code, reason, says):
    feed(monkeypatch, b"")
    threading.Timer(0.6, cli.close_sockets, args=(code, reason)).start()
    assert run("rsh", SBX, "--", "sleep", "30") == 1
    err = capsysbinary.readouterr().err.decode()
    assert err.startswith(f"{reason}: ") and says in err.lower()
    assert cli.wait_idle()


def test_hibernated_close_names_the_next_step(cli, monkeypatch, capsysbinary):
    feed(monkeypatch, b"")
    threading.Timer(0.5, cli.close_sockets, args=(4410, "sandbox_hibernated")).start()
    run("rsh", SBX, "--", "sleep", "30")
    assert f"sandbox rsh {SBX}" in capsysbinary.readouterr().err.decode()


def test_the_switched_off_channel_is_said_plainly(tmp_path, monkeypatch, capsysbinary):
    with FakeChannel(tmp_path, enabled=False) as server:
        for name in ENV:
            monkeypatch.delenv(name, raising=False)
        monkeypatch.setenv("OMEGA_BASE_URL", server.base_url)
        monkeypatch.setenv("FUTUREAGI_OMEGA_API_KEY", BEARER)
        monkeypatch.setattr(registry, "entry_points", lambda: [_EP()])
        feed(monkeypatch, b"")
        assert run("rsh", SBX, "--", "true") == 1
    err = capsysbinary.readouterr().err.decode()
    assert err.startswith("not_found: ") and "switched off by the operator" in err


def test_remote_host_sandboxes_get_a_clear_message(tmp_path, monkeypatch, capsysbinary):
    with FakeChannel(tmp_path, remote_unsupported=True) as server:
        for name in ENV:
            monkeypatch.delenv(name, raising=False)
        monkeypatch.setenv("OMEGA_BASE_URL", server.base_url)
        monkeypatch.setenv("FUTUREAGI_OMEGA_API_KEY", BEARER)
        monkeypatch.setattr(registry, "entry_points", lambda: [_EP()])
        feed(monkeypatch, b"")
        assert run("rsh", SBX, "--", "true") == 1
    err = capsysbinary.readouterr().err.decode()
    assert "sandbox host" in err and "exec" in err


@pytest.mark.parametrize("buffering", [-1, 0], ids=["buffered", "unbuffered"])
def test_remote_output_waits_for_a_full_non_blocking_pipe(buffering):
    # rsync and scp read rsh's standard output through a pipe they set non-blocking: a full pipe
    # makes the next write wait for the reader instead of failing part way through a transfer.
    # Unbuffered (python -u) output is a raw file, whose write returns None when it would block.
    from fi._cli import sandbox_channel

    read_end, write_end = os.pipe()
    os.set_blocking(write_end, False)
    data = bytes(range(256)) * 4096  # 1 MiB, far more than the pipe holds
    got = bytearray()

    def slow_reader():
        time.sleep(0.2)  # let the pipe fill first
        while chunk := os.read(read_end, 65536):
            got.extend(chunk)

    reader = threading.Thread(target=slow_reader)
    reader.start()
    with open(write_end, "wb", buffering=buffering) as target:
        writer = threading.Thread(target=sandbox_channel._emit, args=(target, data), daemon=True)
        writer.start()
        writer.join(10)
        assert not writer.is_alive(), "the write did not finish"
    reader.join(10)
    os.close(read_end)
    assert bytes(got) == data


def test_a_command_is_required(cli, capsys):
    assert run("rsh", SBX) == 2
    assert "invalid_arguments: give the command" in capsys.readouterr().err


def test_no_base_url_is_a_usage_problem(monkeypatch, capsys):
    for name in ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(registry, "entry_points", lambda: [_EP()])
    assert run("rsh", SBX, "--", "true") == 2
    assert "missing_base_url" in capsys.readouterr().err


def test_help_lists_the_new_commands(cli, capsys):
    assert cli_main.main(["sandbox", "--help"]) == 0
    out = capsys.readouterr().out
    for word in ("rsh", "ssh", "rsync", "scp"):
        assert word in out


# -- rsync and scp wrappers ---------------------------------------------------------------------


@pytest.mark.parametrize("tool", ["rsync", "scp"])
def test_a_missing_local_tool_is_named(cli, monkeypatch, capsys, tool):
    import shutil

    real = shutil.which
    monkeypatch.setattr(shutil, "which", lambda name, *a, **k: None if name == tool else real(name, *a, **k))
    assert run(tool, SBX, "-r", "x", ":y") == 2
    err = capsys.readouterr().err
    assert f"{tool}_missing" in err and tool in err and "install" in err.lower()


def test_rsync_runs_the_system_tool_with_this_cli_as_the_shell(cli, monkeypatch):
    seen = {}

    def fake_run(argv, *a, **k):
        seen["argv"] = list(argv)
        return subprocess.CompletedProcess(argv, 23)

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert run("rsync", SBX, "-av", "src/", ":dest/") == 23
    argv = seen["argv"]
    assert os.path.basename(argv[0]) == "rsync"
    shell = argv[argv.index("-e") + 1]
    assert shell.endswith(f"sandbox rsh {SBX}")
    assert "--protect-args" in argv and argv[-3:] == ["-av", "src/", ":dest/"]


def test_scp_runs_the_system_tool_with_a_wrapper_that_maps_to_rsh(cli, monkeypatch):
    seen = {}

    def fake_run(argv, *a, **k):
        wrapper = argv[argv.index("-S") + 1]
        seen["argv"] = list(argv)
        seen["wrapper"] = open(wrapper).read()
        seen["executable"] = os.access(wrapper, os.X_OK)
        seen["path"] = wrapper
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert run("scp", SBX, "-r", "local.txt", ":remote.txt") == 0
    argv = seen["argv"]
    assert os.path.basename(argv[0]) == "scp" and "-O" in argv
    assert argv[-2:] == ["local.txt", f"{SBX}:remote.txt"]
    assert seen["executable"] and f"sandbox rsh --ssh-style {SBX}" in seen["wrapper"]
    assert not os.path.exists(seen["path"])  # removed afterwards


# -- ssh ----------------------------------------------------------------------------------------


def cli_process(cli, *args, slave):
    env = {**os.environ, "OMEGA_BASE_URL": cli.base_url, "FUTUREAGI_OMEGA_API_KEY": BEARER,
           "PYTHONPATH": os.pathsep.join(p for p in sys.path if p)}
    return subprocess.Popen([sys.executable, "-m", "fi._cli", "sandbox", *args],
                            stdin=slave, stdout=slave, stderr=slave, env=env, close_fds=True)


def read_until(fd, needle: bytes, seconds=15.0) -> bytes:
    import select

    seen, end = b"", time.monotonic() + seconds
    while needle not in seen and time.monotonic() < end:
        ready, _, _ = select.select([fd], [], [], 0.1)
        if ready:
            try:
                seen += os.read(fd, 4096)
            except OSError:
                break
    return seen


@pytest.mark.skipif(sys.platform == "win32", reason="needs a pty")
@pytest.mark.parametrize("how", ["exit", "ctrl-c-byte", "sigint", "eof"])
def test_ssh_runs_a_shell_in_raw_mode_and_restores_the_tty_on_every_exit(cli, how):
    import pty
    import signal
    import termios

    master, slave = pty.openpty()
    before = termios.tcgetattr(slave)
    proc = cli_process(cli, "ssh", SBX, slave=slave)
    try:
        # Raw mode is in force while the session runs: no echo or line buffering by the tty.
        deadline, during = time.monotonic() + 15, before
        while time.monotonic() < deadline and during == before:
            during = termios.tcgetattr(slave)
            time.sleep(0.02)
        assert not during[3] & termios.ECHO and not during[3] & termios.ICANON
        os.write(master, b"echo hello-from-$((40+2))\n")
        assert b"hello-from-42" in read_until(master, b"hello-from-42")
        if how == "exit":
            os.write(master, b"exit 5\n")
            assert proc.wait(15) == 5
        elif how == "eof":
            os.write(master, b"\x04")
            assert proc.wait(15) == 0
        elif how == "ctrl-c-byte":
            os.write(master, b"\x03")
            assert proc.wait(15) == 130
        else:
            proc.send_signal(signal.SIGINT)
            assert proc.wait(15) == 130
        assert termios.tcgetattr(slave) == before
        assert cli.wait_idle()
    finally:
        if proc.poll() is None:
            proc.kill()
        os.close(master)
        os.close(slave)


def test_ssh_uses_the_shell_the_sandbox_reports(cli, monkeypatch, capsysbinary):
    if not os.path.exists("/bin/bash"):
        pytest.skip("needs /bin/bash")
    cli.info = {"shell": "/bin/bash"}
    feed(monkeypatch, b"echo shell-is-$0\nexit 0\n")
    assert run("ssh", SBX) == 0
    assert b"shell-is-/bin/bash" in capsysbinary.readouterr().out


def test_ssh_defaults_to_a_posix_shell(cli, monkeypatch, capsysbinary):
    feed(monkeypatch, b"echo shell-is-$0\nexit 0\n")
    assert run("ssh", SBX) == 0
    assert b"shell-is-/bin/sh" in capsysbinary.readouterr().out
