"""fi.evals is the published ai-evaluation 1.1.0 code: every file is byte-identical or listed.

The manifest (``fixtures/upstream-ai-evaluation-1.1.0.json``) holds the sha256 of every file under
``fi/evals`` in the published wheel (the digests of its RECORD). A file that differs must be listed
in ``deviations`` with its reason, and a file this package adds must be listed in ``added``. So
the claim "source-compatible with 1.1.0" is checked file by file, and any later edit to the ported
code shows up here until it is listed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PYTHON = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((Path(__file__).parent / "fixtures" / "upstream-ai-evaluation-1.1.0.json").read_text())


def _tree() -> dict:
    root = PYTHON / "fi" / "evals"
    return {
        str(p.relative_to(PYTHON)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    }


def test_manifest_describes_the_published_wheel() -> None:
    assert MANIFEST["distribution"] == "ai-evaluation"
    assert MANIFEST["version"] == "1.1.0"
    assert MANIFEST["license"] == "Apache-2.0"
    assert len(MANIFEST["files"]) == 221
    assert all(path.startswith("fi/evals/") for path in MANIFEST["files"])


def test_every_upstream_file_is_present_and_identical_unless_listed() -> None:
    tree = _tree()
    missing = sorted(set(MANIFEST["files"]) - set(tree))
    assert missing == [], f"files of ai-evaluation 1.1.0 missing from fi/evals: {missing}"
    changed = sorted(p for p, digest in MANIFEST["files"].items() if tree[p] != digest)
    assert changed == sorted(MANIFEST["deviations"]), (
        "a changed file must be listed in deviations (and a listed one must really differ): "
        f"changed {changed}, listed {sorted(MANIFEST['deviations'])}"
    )


def test_every_added_file_is_listed_with_a_reason() -> None:
    added = sorted(set(_tree()) - set(MANIFEST["files"]))
    assert added == sorted(MANIFEST["added"]), f"unlisted files under fi/evals: {added}"
    assert all(reason.strip() for reason in MANIFEST["added"].values())
    assert all(reason.strip() for reason in MANIFEST["deviations"].values())


def test_the_legacy_cli_tree_is_not_shipped() -> None:
    assert not (PYTHON / "fi" / "cli").exists(), "fi/cli belongs to no distribution; `futureagi-py evals` replaces it"


def test_the_package_ships_fi_evals_and_no_fi_console_script() -> None:
    text = (PYTHON / "pyproject.toml").read_text()
    exclude = text.split("exclude = [", 1)[1].split("]", 1)[0]
    assert '"fi/evals"' not in exclude, "fi/evals must be in the wheel"
    scripts = text.split("[tool.poetry.scripts]", 1)[1].split("\n[", 1)[0]
    lines = [line.split("#", 1)[0] for line in scripts.splitlines()]
    names = [line.split("=", 1)[0].strip().strip("\"'") for line in lines if "=" in line]
    assert names == ["futureagi-py"], f"console scripts: {names}"
    plugins = text.split('[tool.poetry.plugins."futureagi.cli"]', 1)[1].split("\n[", 1)[0]
    assert 'evals = "fi.evals._cli"' in plugins
