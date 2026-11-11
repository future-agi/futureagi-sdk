"""The one exit-code table (``fi.sandbox.types``): the command's own code, 124 when it timed out,
128+N when signal N ended it (Linux numbering), 130 when it was cancelled, 1 when it could not
start or the signal has no known number, 2 for usage; read from an ``ExitFrame`` and from a
``CommandResult`` alike. The module imports the standard library only, and the ``sandbox``
command keeps no copy of the table."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest
from fi.sandbox import CommandResult, ExitFrame, types

TYPES = Path(types.__file__)

CASES = [
    ({"exit_code": 0}, 0),
    ({"exit_code": 42}, 42),
    ({"exit_code": None, "signal": "SIGKILL", "timed_out": True}, 124),
    ({"exit_code": None, "signal": "SIGTERM", "cancelled": True}, 130),
    ({"exit_code": None, "signal": "SIGTERM", "cancelled": True, "timed_out": True}, 130),
    ({"exit_code": None, "signal": "SIGTERM"}, 143),
    ({"exit_code": None, "signal": "SIGKILL"}, 137),
    ({"exit_code": None, "signal": "KILL"}, 137),
    ({"exit_code": None, "signal": "9"}, 137),
    ({"exit_code": None, "signal": "SIGSEGV"}, 139),
    ({"exit_code": None, "signal": "SIGUSR1"}, 138),  # 10 on Linux (30 on macOS)
    ({"exit_code": None, "signal": "SIGCHLD"}, 145),  # 17 on Linux (20 on macOS)
    ({"exit_code": None, "error": "spawn /bin/nope ENOENT"}, 1),
    ({"exit_code": None, "signal": "SIGNOPE"}, 1),
    ({"exit_code": None}, 1),
]


@pytest.mark.parametrize("fields,code", CASES)
def test_an_exit_frame_and_a_result_map_to_the_same_code(fields, code):
    frame = ExitFrame(id="9", **fields)
    assert types.exit_status(frame) == code
    assert types.exit_status(CommandResult.from_exit(frame, "out", "err", "exec_1")) == code


def test_the_table_names_its_codes():
    assert (types.EXIT_OK, types.EXIT_REFUSED, types.EXIT_USAGE) == (0, 1, 2)
    assert (types.EXIT_TIMED_OUT, types.EXIT_SIGNAL_BASE, types.EXIT_CANCELLED) == (124, 128, 130)
    assert types.LINUX_SIGNALS["SIGTERM"] == 15 and types.LINUX_SIGNALS["SIGSYS"] == 31
    assert [types.signal_number(name) for name in ("SIGINT", "int", " 2 ", "", None, "SIGNOPE")] == [
        2, 2, 2, None, None, None]


def test_the_table_module_imports_the_standard_library_only():
    tree = ast.parse(TYPES.read_text(encoding="utf-8"))
    guarded = {id(node) for block in tree.body if isinstance(block, ast.If)
               and ast.unparse(block.test) == "TYPE_CHECKING" for node in ast.walk(block)}
    found = []
    for node in ast.walk(tree):
        if id(node) in guarded:
            continue
        if isinstance(node, ast.Import):
            found += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            found.append("." * node.level + (node.module or ""))
    roots = {name.split(".")[0] for name in found}
    assert roots <= set(sys.stdlib_module_names) | {"__future__"}, found


def test_the_command_line_keeps_no_copy_of_the_table():
    import fi._cli.sandbox as cli

    names = {"LINUX_SIGNALS", "EXIT_OK", "EXIT_REFUSED", "EXIT_USAGE", "EXIT_TIMED_OUT", "EXIT_CANCELLED",
             "EXIT_SIGNAL_BASE", "_signal_number"}
    assert not names & set(vars(cli))
    source = Path(cli.__file__).read_text(encoding="utf-8")
    assert "from fi.sandbox.types import" in source and "SIGKILL" not in source
