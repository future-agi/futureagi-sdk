"""The port manifest covers every agentcc 1.0 test id.

port_manifest.json maps each of the 789 test ids at agent-command-center-sdk the recorded source to
a collected test here, to the agentcc 2.0 compatibility package (``shim:``), or to a
drop with its reason and reviewer record. scripts/gateway/check_port_manifest.py holds
the rules; ``--require-signed`` (every drop signed) is the release gate.
"""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
_spec = importlib.util.spec_from_file_location(
    "check_port_manifest", ROOT / "scripts" / "gateway" / "check_port_manifest.py"
)
assert _spec and _spec.loader
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)

MANIFEST = check.load()


@pytest.fixture(scope="module")
def collected() -> set[str]:
    return check.collected_ids()


def test_every_1_0_test_id_is_mapped_to_a_collected_test_or_the_shim(
    collected: set[str],
) -> None:
    assert check.problems(MANIFEST, collected, require_signed=False) == []
    assert len(MANIFEST["entries"]) == 789


def test_the_counts_add_up() -> None:
    counts = check.summary(MANIFEST)
    assert sum(counts.values()) == 789
    assert set(counts) <= check.KINDS


def test_a_missing_id_fails() -> None:
    broken = copy.deepcopy(MANIFEST)
    broken["entries"].pop()
    found = check.problems(broken, None, require_signed=False)
    assert any("788 entries" in p for p in found)
    assert any("ids_sha256" in p for p in found)


def test_a_target_that_is_not_collected_fails(collected: set[str]) -> None:
    broken = copy.deepcopy(MANIFEST)
    entry = next(e for e in broken["entries"] if e["kind"] == "same")
    entry["to"] += "_gone"
    entry["kind"] = "edited"
    entry["edits"] = ["x"]
    found = check.problems(broken, collected, require_signed=False)
    assert found == [f"{entry['old']}: target {entry['to']} is not a collected test"]


def test_a_shim_entry_needs_a_shim_only_reason_and_a_drop_needs_a_signature() -> None:
    broken = copy.deepcopy(MANIFEST)
    shim = next(e for e in broken["entries"] if e["kind"] == "shim")
    shim["reason"] = "moved"
    drop = next(e for e in broken["entries"] if e["kind"] == "same")
    drop.update(kind="dropped", to=None, reason="asserts the 1.0 bug D-09 fixes")
    found = check.problems(broken, None, require_signed=False)
    assert found == [
        f"{shim['old']}: a shim entry is 'shim:<old id>' with a shim-only reason"
    ]
    signed = check.problems(broken, None, require_signed=True)
    assert f"{drop['old']}: drop not signed" in signed
    drop["reviewer"] = {"by": "a maintainer", "record": "review-fixture", "verdict": "ok"}
    assert f"{drop['old']}: drop not signed" not in check.problems(
        broken, None, require_signed=True
    )


def test_the_release_gate_passes_today() -> None:
    """No drop exists, so nothing waits for a signature."""
    assert check.summary(MANIFEST).get("dropped", 0) == 0
    assert check.problems(MANIFEST, None, require_signed=True) == []
