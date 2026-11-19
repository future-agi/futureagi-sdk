"""E-NEW: fi.gateway against the agentcc 1.0.0 golden, with the Python port's overlay.

The port's entries for the comparison py-agentcc-1.0.0->e-new-py ('D-xx-py' and
'PY-*') live in the golden's tests/fixtures/gateway/intended-differences.json once a
reviewer signed them ('proven'), beside the D-xx work list ('planned'), and in
python/tests/gateway/intended-differences-py.json while 'landed'.
scripts/gateway/compare_enew.py merges the two. The comparison itself runs only in the
golden's pinned environment (Python 3.12 with tests/fixtures/gateway/e-old/
constraints-py.txt); anywhere else it is skipped with the differences named. The
structure checks run everywhere.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
_spec = importlib.util.spec_from_file_location(
    "compare_enew", ROOT / "scripts" / "gateway" / "compare_enew.py"
)
assert _spec and _spec.loader
compare_enew = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(compare_enew)

# Every entry of the port, signed or still landed; SHARED is the rest of the shared file.
OVERLAY = compare_enew.port_entries()
UNSIGNED = compare_enew.overlay_entries()
SHARED = [
    e
    for e in compare_enew.shared_entries()
    if not compare_enew.PORT_ID.fullmatch(e["id"])
]
PINNED = "pip install -c tests/fixtures/gateway/e-old/constraints-py.txt on Python 3.12"
# Text no recorded value contains: a regex that matches it pins nothing (the rule of
# python/tests/gateway/parity/test_parity_intended.py).
PROBES = ("<<parity probe: no recorded value is this text>>", "\x00\n")
# The Python deltas the port lands. D-19 has no entry: the two
# golden cases that logged no longer log (PY-1.2, D-21); test_gw_d19_logger.py proves it.
PORT_DELTAS = ["D-02", "D-03", "D-06", "D-07", "D-09", "D-10", "D-14", "D-15"]
PORT_DELTAS += ["D-16", "D-17", "D-20", "D-21"]


def _assert_review_state(entry: dict) -> None:
    entry_id = entry["id"]
    assert entry["status"] in compare_enew.COVERING, entry_id
    reviewer = entry["reviewer"]
    if entry["status"] == "landed":
        assert reviewer is None, entry_id
        return
    from parity._review import assert_review_record

    assert_review_record(entry)


def test_overlay_entries_are_well_formed() -> None:
    ids = [e["id"] for e in OVERLAY]
    assert len(ids) == len(set(ids))
    assert not {e["id"] for e in UNSIGNED} & {
        e["id"] for e in compare_enew.shared_entries()
    }, "overlay ids must be new"
    for e in OVERLAY:
        assert re.fullmatch(r"D-\d\d[a-z]?-py|PY-[0-9.]+-[a-z0-9-]+", e["id"]), e["id"]
        assert e["lang"] == "py" and e["applies_to"] == [compare_enew.LABEL], e["id"]
        assert e["summary"] and e["evidence"] and e["test_id"], e["id"]
        _assert_review_state(e)
        assert e["match"], e["id"]
        for rule in e["match"]:
            assert set(rule) <= {"path", "kind", "old", "new", "top_level"}, e["id"]
            assert rule.get("kind", "any") in {"any", "changed", "added", "removed"}
            for side in ("old", "new"):
                if side in rule:
                    re.compile(rule[side])


def _pinned(rule: dict) -> bool:
    exact = not re.search(r"[*?]", rule.get("path", "*"))
    pins = [
        not any(re.search(rule[side], probe) for probe in PROBES)
        for side in ("old", "new")
        if side in rule
    ]
    return exact or any(pins)


def test_every_overlay_rule_is_pinned() -> None:
    loose = [(e["id"], r) for e in OVERLAY for r in e["match"] if not _pinned(r)]
    assert loose == []


def test_transport_fix_rules_pin_both_sides() -> None:
    entries = [e for e in OVERLAY if e["id"].startswith("PY-4.0-")]
    assert {e["id"] for e in entries} == {
        "PY-4.0-sessions", "PY-4.0-stream-status",
        "PY-4.0-cache-stream", "PY-4.0-sse-boundaries",
    }
    assert sum(len(e["match"]) for e in entries) == 54
    for entry in entries:
        _assert_review_state(entry)
    # The SSE fix keeps the module's public names, so the signed module-split
    # entry's surface rule still holds and no landed entry restates it.
    sse_surface = "surface.modules[sync]/result/_streaming._sse"
    assert not [r for e in entries for r in e["match"] if r["path"] == sse_surface]
    for entry in entries:
        for rule in entry["match"]:
            assert not re.search(r"[*?]", rule["path"])
            assert rule["kind"] in {"added", "changed", "removed"}
            for side in ("old", "new"):
                assert rule[side].startswith("^") and rule[side].endswith("$")
                assert not any(re.search(rule[side], probe) for probe in PROBES)


def _transport_entries() -> list[dict]:
    return copy.deepcopy([e for e in OVERLAY if e["id"].startswith("PY-4.0-")])


def _reviewer_fixture() -> dict:
    return {
        "by": "independent reviewer fixture",
        "record": "python-transport-fixes-2026-10-28",
        "verdict": "accepted",
        "date": "2026-10-28",
        "evidence": "python/tests/gateway/unit/test_catalog_compatibility.py",
    }


@pytest.mark.parametrize("promoted_count", [0, 1, 4])
def test_transport_entries_move_from_landed_to_proven(
    tmp_path: Path, monkeypatch, promoted_count: int
) -> None:
    entries = _transport_entries()
    original_rules = {e["id"]: copy.deepcopy(e["match"]) for e in entries}
    for entry in entries:
        entry.update(status="landed", reviewer=None)
    promoted, landed = entries[:promoted_count], entries[promoted_count:]
    for entry in promoted:
        entry.update(status="proven", reviewer=_reviewer_fixture())
    shared = [
        e for e in compare_enew.shared_entries() if e["id"] not in original_rules
    ] + promoted
    shared_file, overlay_file = tmp_path / "shared.json", tmp_path / "overlay.json"
    shared_file.write_text(json.dumps({"differences": shared}))
    overlay_file.write_text(json.dumps({"differences": landed}))
    monkeypatch.setattr(compare_enew, "SHARED_FILE", shared_file)
    monkeypatch.setitem(globals(), "OVERLAY", compare_enew.port_entries(overlay_file))
    monkeypatch.setitem(globals(), "UNSIGNED", compare_enew.overlay_entries(overlay_file))

    test_overlay_entries_are_well_formed()
    test_transport_fix_rules_pin_both_sides()
    assert {e["id"]: e["match"] for e in _transport_entries()} == original_rules
    strict = compare_enew.merged(landed, landed_covers=False)
    assert {e["id"] for e in strict if e["id"] in original_rules and e["status"] == "proven"} == {
        e["id"] for e in promoted
    }


_BAD_REVIEWERS = [None, "reviewed", [], {}]
_BAD_REVIEWERS += [
    {k: v for k, v in _reviewer_fixture().items() if k != missing}
    for missing in ("by", "record", "verdict", "date", "evidence")
]
_BAD_REVIEWERS += [
    {**_reviewer_fixture(), field: value}
    for field, value in [
        ("by", " "), ("commit", "not-a-commit"), ("commit", 1234567),
        ("verdict", ""), ("date", "2026-02-30"), ("date", "20261028"),
        ("evidence", " "), ("evidence", []),
    ]
]


@pytest.mark.parametrize("reviewer", _BAD_REVIEWERS)
def test_proven_transport_entry_rejects_malformed_review(monkeypatch, reviewer) -> None:
    entries = copy.deepcopy(OVERLAY)
    entry = next(e for e in entries if e["id"].startswith("PY-4.0-"))
    entry.update(status="proven", reviewer=reviewer)
    monkeypatch.setitem(globals(), "OVERLAY", entries)
    with pytest.raises(AssertionError):
        test_overlay_entries_are_well_formed()
    with pytest.raises(AssertionError):
        test_transport_fix_rules_pin_both_sides()


def test_landed_transport_entry_cannot_claim_review() -> None:
    entry = _transport_entries()[0]
    entry.update(status="landed", reviewer=_reviewer_fixture())
    with pytest.raises(AssertionError):
        _assert_review_state(entry)


def test_the_pinning_check_bites() -> None:
    assert not _pinned({"path": "stream.*"})
    assert not _pinned({"path": "*", "new": ".*"})
    assert _pinned({"path": "env.base_url.x[sync]/requests/0/path"})
    assert _pinned({"path": "*/headers/user-agent", "new": "^futureagi-python/"})


def test_each_test_id_names_a_test_in_the_tree() -> None:
    for e in OVERLAY:
        path, _, name = e["test_id"].partition("::")
        source = (ROOT / path).read_text()
        assert re.search(rf"^(async )?def {re.escape(name)}\(", source, re.M), e["id"]


def test_every_port_delta_has_landed() -> None:
    ids = {e["id"] for e in OVERLAY}
    assert [d for d in PORT_DELTAS if f"{d}-py" not in ids] == []
    planned = {e["id"] for e in SHARED if e["status"] == "planned"}
    assert set(PORT_DELTAS) <= planned | {"D-19"}


# Entries that change what an agentcc 1.x caller sends carry the line the migration
# guide quotes: D-06b (the one metadata rule), the query options that now reach the
# wire, and audio uploads (a str file name is refused).
MIGRATION = ("D-06b-py", "PY-1.4-default-query", "PY-1.2-audio-multipart")


def test_behaviour_changes_carry_a_migration_line() -> None:
    by_id = {e["id"]: e for e in OVERLAY}
    for entry_id in MIGRATION:
        entry = by_id[entry_id]
        line = entry.get("migration")
        assert isinstance(line, str) and len(line) > 40, entry_id
        assert "Migration:" in entry["summary"], entry_id
    assert set(by_id) - set(MIGRATION) == {
        e["id"] for e in OVERLAY if "migration" not in e
    }


def test_d_06b_pins_the_l6_over_l4_merge() -> None:
    (entry,) = [e for e in OVERLAY if e["id"] == "D-06b-py"]
    (rule,) = entry["match"]
    assert rule["path"].startswith("header_merge.l6_over_l4[")
    assert re.search(rule["old"], '{"b":2}') and not re.search(rule["new"], '{"b":2}')
    assert re.search(rule["new"], '{"a":1,"b":2}')


def _skip_reason() -> str | None:
    from parity.compare import load_recording, pinned_environment_differences
    from parity.record import library_environment

    golden = load_recording(compare_enew.GOLDEN)["index"]["environment"]
    differences = pinned_environment_differences(golden, library_environment())
    if differences:
        return f"not the golden's environment ({'; '.join(differences)}): run with {PINNED}"
    return None


def test_e_new_has_no_unlisted_difference_with_the_overlay(tmp_path: Path) -> None:
    reason = _skip_reason()
    if reason:
        pytest.skip(reason)
    # Record in a fresh interpreter: in this one, earlier tests have resolved lazy
    # names, which fi.gateway caches in its namespace, so surface.modules would see
    # them (a recording depends on what the process imported before it).
    import os
    import subprocess
    import sys

    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONPATH"] = str(ROOT / "python")
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "parity.record",
            "--root",
            "fi.gateway",
            "--out",
            str(tmp_path),
        ],
        cwd=compare_enew.GATEWAY_TESTS,
        env=env,
        capture_output=True,
        text=True,
    )
    # the recorder's own output, so a failure in it says what failed
    assert done.returncode == 0, (
        f"parity.record exited {done.returncode}\n"
        f"stderr:\n{done.stderr[-4000:]}\nstdout:\n{done.stdout[-2000:]}"
    )
    report = compare_enew.compare_new(tmp_path)
    (tmp_path / "report.json").write_text(json.dumps(report, default=str))
    assert report["unlisted"] == [], json.dumps(report["unlisted"][:10], default=str)
    assert report["unused_overlay_rules"] == []
    assert report["unobserved_overlay"] == []
    # The shared file's strict rule (only signed entries cover) is the release gate:
    # it passes exactly when no overlay entry still waits for its reviewer record.
    assert report["strict_ok"] == (report["awaiting_reviewer"] == [])
    assert (report["strict_unlisted"] == 0) == report["strict_ok"]
    assert report["ok"]
