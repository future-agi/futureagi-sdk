"""The exit-code rule the sandbox integrations share (``fi.sandbox_integrations._exit``): 130 cancelled, 124 timed
out, 1 could not start, the command's own code, 128+N for Linux signal N, and None when nothing gives a number. The
numbers are the SDK's one table (``fi.sandbox.types``), which the ``sandbox`` command reads too, so the module keeps
no copy of it. Importing the package loads no framework and no sandbox client."""

from __future__ import annotations

import itertools
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pytest

from fi.sandbox import CommandResult, ExitFrame, types
from fi.sandbox_integrations import _exit

PYTHON = Path(__file__).resolve().parents[2]
FRAMEWORKS = ("deepagents", "agents", "mcp", "opentelemetry")
SANDBOX_CLIENT = ("fi.sandbox", "httpx")


@dataclass(frozen=True)
class Ended:
    """Only the fields of an exit record that the rule reads."""

    exit_code: Optional[int] = None
    signal: Optional[str] = None
    timed_out: bool = False
    cancelled: bool = False
    error: Optional[str] = None


def test_cancelled_wins_over_timed_out():
    for record in (
        Ended(cancelled=True),
        Ended(cancelled=True, timed_out=True),
        Ended(cancelled=True, timed_out=True, signal="SIGTERM"),
    ):
        assert _exit.shell_exit_code(record) == _exit.EXIT_CANCELLED == 130


def test_timed_out_is_124():
    for record in (Ended(timed_out=True), Ended(timed_out=True, signal="SIGKILL"), Ended(timed_out=True, exit_code=0)):
        assert _exit.shell_exit_code(record) == _exit.EXIT_TIMED_OUT == 124


def test_spawn_error_is_1():
    assert _exit.shell_exit_code(Ended(error="spawn /bin/nope ENOENT")) == _exit.EXIT_FAILED == 1


@pytest.mark.parametrize("code", [0, 2, 255])
def test_exit_code_passes_through_including_zero(code):
    assert _exit.shell_exit_code(Ended(exit_code=code)) == code
    result = CommandResult(exit_code=code, stdout="", stderr="", exec_id="exec_1")
    assert _exit.shell_exit_code(result) == code


def test_signal_by_full_name_short_name_and_number():
    for name in ("SIGKILL", "KILL", "kill", "9", " 9 "):
        assert _exit.signal_number(name) == 9
        assert _exit.shell_exit_code(Ended(signal=name)) == _exit.EXIT_SIGNAL_BASE + 9 == 137
    assert _exit.shell_exit_code(Ended(signal="SIGTERM")) == 143
    frame = ExitFrame(id="9", exit_code=None, signal="SIGKILL")
    assert _exit.shell_exit_code(frame) == 137
    assert _exit.shell_exit_code(CommandResult.from_exit(frame, "", "", "exec_1")) == 137


def test_unknown_signal_and_empty_record_give_none():
    for record in (Ended(signal="SIGNOPE"), Ended(), Ended(signal="")):
        assert _exit.shell_exit_code(record) is None
        assert types.exit_status(record) == types.EXIT_REFUSED  # the command line exits 1 here
    assert _exit.signal_number("SIGNOPE") is None


def test_linux_signals_equal_cli_table():
    """One table: the module re-exports ``fi.sandbox.types``, the source the ``sandbox`` command reads, and every
    code it gives equals that command's code for the same record."""
    import fi._cli.sandbox as cli

    assert _exit.LINUX_SIGNALS is types.LINUX_SIGNALS
    assert _exit.signal_number is types.signal_number
    assert (_exit.EXIT_FAILED, _exit.EXIT_TIMED_OUT, _exit.EXIT_SIGNAL_BASE, _exit.EXIT_CANCELLED) == (
        types.EXIT_REFUSED,
        types.EXIT_TIMED_OUT,
        types.EXIT_SIGNAL_BASE,
        types.EXIT_CANCELLED,
    )
    source = Path(_exit.__file__).read_text(encoding="utf-8")
    assert "from fi.sandbox.types import" in source and "SIGKILL" not in source
    assert "from fi.sandbox.types import" in Path(cli.__file__).read_text(encoding="utf-8")
    fields = itertools.product(
        (None, 0, 3), (None, "SIGTERM", "INT", "31", "SIGNOPE"), (False, True), (False, True), (None, "boom")
    )
    for exit_code, signal, timed_out, cancelled, error in fields:
        record = Ended(exit_code=exit_code, signal=signal, timed_out=timed_out, cancelled=cancelled, error=error)
        code = _exit.shell_exit_code(record)
        assert code is None or code == types.exit_status(record), record


def test_ending_note_texts():
    note = _exit.ending_note
    assert note(Ended(timed_out=True, signal="SIGKILL"), timeout_s=30) == "Command timed out after 30 seconds"
    assert note(Ended(timed_out=True)) == "Command timed out"
    assert note(Ended(cancelled=True, timed_out=True), timeout_s=30) == "Command was cancelled"
    assert note(Ended(error="spawn /bin/nope ENOENT")) == "The command could not start: spawn /bin/nope ENOENT"
    assert note(Ended(signal="SIGKILL")) == "Command was ended by signal SIGKILL"
    assert note(Ended(signal="SIGNOPE")) == "Command ended without an exit code (SIGNOPE)"
    assert note(Ended()) == "Command ended without an exit code"
    for code in (0, 2):
        assert note(Ended(exit_code=code)) is None
        assert note(Ended(exit_code=code), timeout_s=30) is None


def _loaded_after(statement: str) -> set:
    code = (
        f"import sys; sys.path.insert(0, {str(PYTHON)!r})\n"
        f"{statement}\n"
        "import json; print(json.dumps(sorted(sys.modules)))"
    )
    out = subprocess.run(
        [sys.executable, "-I", "-B", "-c", code], capture_output=True, text=True, timeout=120, cwd=str(PYTHON)
    )
    assert out.returncode == 0, out.stderr
    return set(json.loads(out.stdout))


def _under(modules: set, roots: tuple) -> list:
    return sorted(m for m in modules if any(m == root or m.startswith(root + ".") for root in roots))


def test_package_import_loads_no_framework_and_no_sandbox_client():
    package = _loaded_after("import fi.sandbox_integrations")
    assert _under(package, FRAMEWORKS + SANDBOX_CLIENT) == []
    # the exit-code helper reads the SDK's one table, so it loads the sandbox package, and still no framework
    helper = _loaded_after("import fi.sandbox_integrations._exit")
    assert _under(helper, FRAMEWORKS) == []
    assert "fi.sandbox.types" in helper
