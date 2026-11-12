"""The ``sandbox`` file commands (``cp``, ``ls``, ``cat``, ``rm``, ``mv``, ``mkdir``) say in their help how
a sandbox path works: it is relative to the sandbox folder ``/workspace``, an absolute path under it also
works, and any other path is refused before anything is sent. Fake credentials only."""

from __future__ import annotations

import pytest

from ._sandbox_cli_support import run, server_fixture  # noqa: F401

RULE = (
    "Sandbox paths are relative to the sandbox folder /workspace",
    "an absolute path under /workspace also works",
    "any other path is refused before anything is sent",
)


@pytest.mark.parametrize("command", ["cp", "ls", "cat", "rm", "mv", "mkdir"])
def test_each_file_command_help_states_the_path_rule(server, capsys, command):
    assert run(command, "--help") == 0
    out = " ".join(capsys.readouterr().out.split())
    assert all(part in out for part in RULE), out
    assert server.seen == []
