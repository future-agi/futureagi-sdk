"""The MCP file tools say how their ``path`` works where a model and a person read it: each file tool's
description and the README's tools section say that a path is relative to the sandbox folder
``/workspace``, that an absolute path under it also works and that any other path is refused; the README
names the two refusal codes. ``mcp`` is faked (``_fake_mcp``)."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from . import _fake_mcp

FILE_TOOLS = ("sandbox_read_file", "sandbox_write_file", "sandbox_list_files")
RULE = (
    "relative to the sandbox folder /workspace",
    "an absolute path under /workspace also works",
    "any other path is refused",
)


@pytest.fixture(name="server_module")
def server_module_fixture(monkeypatch):
    """The server module imported afresh over the fake ``mcp``."""
    restore = _fake_mcp.isolate_server()
    _fake_mcp.install(monkeypatch)
    yield importlib.import_module(_fake_mcp.SERVER)
    restore()


def test_each_file_tool_description_states_the_path_rule(server_module):
    for name in FILE_TOOLS:
        text = server_module.DESCRIPTIONS[name]
        assert all(part in text for part in RULE), name
        assert "sandbox_exec" in text, name  # where a file elsewhere is read


def test_the_readme_states_the_path_rule_and_both_refusal_codes():
    package = importlib.import_module(_fake_mcp.PACKAGE)
    text = " ".join((Path(package.__file__).parent / "README.md").read_text(encoding="utf-8").split())
    rule = text.split("The file tools take `path`", 1)[1].split("`sandbox_exec` runs the command", 1)[0]
    assert rule.startswith(" relative to the sandbox folder `/workspace`")
    assert "an absolute path under `/workspace` also works" in rule
    assert "any other path is refused before any request" in rule
    assert "`outside_workspace`" in rule and "`invalid_path`" in rule
