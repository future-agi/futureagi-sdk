"""Packaging of the sandbox integrations: the extras pyproject declares (each installs its framework at the
supported range and Python marker, and its import root names that extra), ``sandbox mcp`` living inside the one
``sandbox`` command group (no plugin entry of its own), and the rename tool keeping ``mcp`` reserved. Reads
files only: no framework is imported and nothing is installed."""

from __future__ import annotations

import ast
import importlib.util
import re
import sys
from pathlib import Path

import pytest
from packaging.specifiers import SpecifierSet

from fi._cli.extra_roots import EXTRA_ROOTS, extra_for_module

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - 3.10
    tomllib = pytest.importorskip("tomli")

PYTHON = Path(__file__).resolve().parents[2]  # python/
REPO = PYTHON.parent
POETRY = tomllib.loads((PYTHON / "pyproject.toml").read_text())["tool"]["poetry"]
DEV = POETRY["group"]["dev"]["dependencies"]

HELD = ("openai-agents 0.24 requires openai>=3; litellm (the evals extra) requires openai<3; one lock "
        "cannot hold both, so this extra is not declared yet")


@pytest.mark.parametrize("extra,distribution,version,python", [
    ("sandbox-deepagents", "deepagents", ">=0.7.35,<0.8", ">=3.11,<4.0"),
    ("sandbox-mcp", "mcp", ">=1.30,<3,!=2.0.*,!=2.1.*", ">=3.10,<3.14"),
    pytest.param("sandbox-openai-agents", "openai-agents", ">=0.24.0,<0.25", ">=3.10,<3.14",
                 marks=pytest.mark.skip(reason=HELD)),
])
def test_extras_declared_with_ranges_and_markers(extra, distribution, version, python):
    assert POETRY["extras"].get(extra) == [distribution]
    spec = POETRY["dependencies"][distribution]
    assert spec == {"version": version, "optional": True, "python": python}
    # The framework itself, never an instrumentor: these extras are not the traceAI ones.
    assert "fi-instrumentation-otel" not in POETRY["extras"][extra]
    root = distribution.replace("-", "_")
    assert EXTRA_ROOTS.get(root) == extra
    assert extra_for_module(f"{root}.submodule") == extra
    # The dev pin, when there is one, lies inside the published range (one lock holds both).
    pin = DEV.get(distribution)
    if pin is not None:
        pinned = pin["version"] if isinstance(pin, dict) else pin
        assert pinned in SpecifierSet(version), f"dev pin {distribution}=={pinned} is outside {version}"


def test_missing_mcp_message_names_the_pythons_the_marker_covers():
    # The message for a missing mcp names the Pythons the extra installs it on; read from the source,
    # so no framework is imported.
    source = (PYTHON / "fi" / "sandbox_integrations" / "mcp_server" / "_server.py").read_text()
    found = [ast.literal_eval(node.value) for node in ast.walk(ast.parse(source))
             if isinstance(node, ast.Assign)
             and any(getattr(target, "id", None) == "SUPPORTED_PYTHONS" for target in node.targets)]
    assert len(found) == 1
    (low, high), marker = found[0], SpecifierSet(POETRY["dependencies"]["mcp"]["python"])
    assert f"{low[0]}.{low[1]}" in marker and f"{high[0]}.{high[1]}" in marker
    assert f"{low[0]}.{low[1] - 1}" not in marker and f"{high[0]}.{high[1] + 1}" not in marker


def _sub_commands(tree: ast.AST) -> set[str]:
    """The names given to ``add(commands, NAME, ...)`` in the sandbox group's ``register``."""
    names = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "add"
                and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant)):
            names.add(node.args[1].value)
    return names


def test_plugin_line_for_sandbox_mcp():
    plugins = POETRY["plugins"]["futureagi.cli"]
    # ``mcp`` is a sub-command of the sandbox group's own module, not a second plugin entry that
    # appends to it (that would depend on the load order of entry points).
    assert plugins["sandbox"] == "fi._cli.sandbox"
    assert "sandbox_mcp" not in plugins
    assert not any(module.startswith("fi.sandbox_integrations") for module in plugins.values())
    source = (PYTHON / "fi" / "_cli" / "sandbox.py").read_text()
    assert "mcp" in _sub_commands(ast.parse(source))
    # Every install line the group prints names an extra that exists.
    extras = set(re.findall(r'futureagi\[([A-Za-z0-9-]+)\]', source))
    assert "sandbox-mcp" in extras
    assert extras <= POETRY["extras"].keys()
    assert extra_for_module("mcp") == "sandbox-mcp"


def _install_lines_naming_missing_extras(paths):
    """``path:line extra`` for every ``futureagi[...]`` and every ``MissingExtraError(extra=...)`` (the hint
    a user sees at import time) in ``paths`` that names an extra pyproject lacks."""
    pattern = re.compile(r'futureagi\[([A-Za-z0-9, -]+)\]')
    declared = POETRY["extras"].keys()
    missing = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        named = []
        for number, line in enumerate(text.splitlines(), start=1):
            for match in pattern.finditer(line):
                named.extend((number, name.strip()) for name in match.group(1).split(","))
        if path.suffix == ".py":
            for node in ast.walk(ast.parse(text)):
                if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) \
                        == "MissingExtraError":
                    named.extend((node.lineno, keyword.value.value) for keyword in node.keywords
                                 if keyword.arg == "extra" and isinstance(keyword.value, ast.Constant))
        missing.extend(f"{path.relative_to(REPO)}:{number} {extra}"
                       for number, extra in sorted(named) if extra and extra not in declared)
    return missing


def test_every_sandbox_integration_install_line_names_a_declared_extra():
    # A user who copies an install line from a module, a README, an error hint or a test must get the
    # framework; pip only warns about an unknown extra and installs nothing for it.
    package = PYTHON / "fi" / "sandbox_integrations"
    paths = [path for path in sorted(package.rglob("*"))
             if path.is_file() and "__pycache__" not in path.parts]
    paths += sorted((PYTHON / "tests" / "sandbox_integrations").glob("*.py"))
    paths.append(PYTHON / "fi" / "_cli" / "sandbox.py")
    assert any(path.name == "README.md" for path in paths)
    missing = _install_lines_naming_missing_extras(paths)
    assert missing == [], "install lines name extras pyproject.toml does not declare:\n" + "\n".join(missing)


def test_mcp_reserved_in_rename_tool(tmp_path):
    spec = importlib.util.spec_from_file_location("rename_cli_packaging", REPO / "scripts/packaging/rename-cli.py")
    rename_cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rename_cli)
    assert "sandbox" in rename_cli.COMMANDS
    assert "mcp" in rename_cli.RESERVED_NAMES and "mcp" not in rename_cli.COMMANDS
    # Every sub-command of the sandbox group, nested ones included, survives a later rename.
    group = _sub_commands(ast.parse((PYTHON / "fi" / "_cli" / "sandbox.py").read_text()))
    assert "mcp" in group
    assert group <= rename_cli.RESERVED_NAMES, sorted(group - rename_cli.RESERVED_NAMES)
    # Refused before any file is read, so an empty folder is enough.
    with pytest.raises(ValueError, match="NEW_NAME"):
        rename_cli.rename(tmp_path, "mcp")
    assert not any(tmp_path.iterdir())
