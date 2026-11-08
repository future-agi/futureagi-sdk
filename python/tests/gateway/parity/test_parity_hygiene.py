"""No golden carries a local path (regression check, finding 1).

The guard against the shared conformance cases (the TypeScript twin passes the
same file), the recorder's refusal to write a leaking file, and a scan of every
committed golden, Python and TypeScript.
"""

from __future__ import annotations

import json
import re

import pytest

from . import record as record_module
from ._fixtures import FIXTURES, GOLDEN, REPO, load
from ._hygiene import LocalPathError, leaks, leaks_in, recorder_roots, write_checked
from ._observe import dump
from ._runner import Case

CASES = load("hygiene-cases.json")["cases"]
# Built here, so the repository never holds a local path literal.
FILE_URL = "file:" + "//"
VOLUMES = "/" + "Volumes"


def _expand(text: str) -> str:
    return re.sub(
        r"\{(\w+)\}", lambda m: FILE_URL if m[1] == "file" else "/" + m[1], text
    )


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_conformance(case: dict) -> None:
    assert leaks(_expand(case["text"]), [_expand(r) for r in case.get("roots", [])]) == [
        _expand(t) for t in case["expect"]
    ]


def test_no_committed_golden_carries_a_local_path() -> None:
    files = sorted(GOLDEN.rglob("*.json"))
    assert len(files) > 50
    found = [
        leak
        for path in files
        for leak in leaks_in(
            json.loads(path.read_text()), (), str(path.relative_to(FIXTURES))
        )
    ]
    assert found == []


def test_write_checked_refuses_a_leak_and_writes_nothing(tmp_path) -> None:
    target = tmp_path / "area.json"
    frame = f"at Bare ({FILE_URL}{VOLUMES}/example/cases/integrations.mjs:84:71)"
    data = {"cases": {"c": {"console": [["error", frame]]}}}
    with pytest.raises(LocalPathError, match=r"cases/c/console/0/1"):
        write_checked(target, data, [])
    assert not target.exists()
    roots = recorder_roots(tmp_path)
    for leaking in ({"out": str(tmp_path / "x")}, {str(REPO / "x.py"): 1}):
        with pytest.raises(LocalPathError):
            write_checked(target, leaking, roots)
    clean = {"cases": {"c": {"console": [["error", "at Bare (<frame>)"]]}}}
    assert write_checked(target, clean, roots) == dump(clean)
    assert target.read_text() == dump(clean)


def test_the_recorder_refuses_a_case_that_records_its_checkout(
    tmp_path, monkeypatch
) -> None:
    pytest.importorskip("httpx")
    leaky = Case(id="hygiene.leak", area="hygiene", fn=lambda ctx: str(REPO / "x.py"))
    monkeypatch.setattr(record_module, "all_cases", lambda: [leaky])
    with pytest.raises(LocalPathError, match="hygiene.json"):
        record_module.record("json", tmp_path / "out")
    assert not (tmp_path / "out" / "hygiene.json").exists()

    fine = Case(id="hygiene.fine", area="hygiene", fn=lambda ctx: "<path>/x.py")
    monkeypatch.setattr(record_module, "all_cases", lambda: [fine])
    index = record_module.record("json", tmp_path / "out")
    assert index["case_ids"] == ["hygiene.fine[sync]"]
    recorded = json.loads((tmp_path / "out" / "hygiene.json").read_text())
    assert recorded["cases"]["hygiene.fine[sync]"]["result"] == "<path>/x.py"
