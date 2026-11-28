"""Journal: modes, gitignore, resume, lock, receipts golden, redaction."""

import json
import os
import stat
import sys
from pathlib import Path

import pytest

from fi import experiments
from fi.experiments import _journal
from fi.experiments._plan import canonical_bytes, receipt_key
from fi.experiments._redact import Redactor
from fi.experiments.errors import JournalError, RunLockedError

GOLDEN = Path(__file__).parent / "golden" / "receipts.json"
ROWS = [{"id": f"T{i}", "q": f"q{i}"} for i in range(1, 6)]


def test_receipts_golden():
    cases = json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"]
    for case in cases:
        data = canonical_bytes(case["item"])
        assert data.decode("utf-8") == case["canonical"]
        assert receipt_key(case["run_id"], case["example_id"], case["trial"], data) == case["receipt_key"]


def test_canonical_bytes_refuse_nan_and_sort():
    assert canonical_bytes({"b": 1, "a": [1.5, None]}) == b'{"a":[1.5,null],"b":1}'
    assert canonical_bytes({"x": float("nan")}) == b'{"x":null}'
    assert canonical_bytes({"ü": "é"}) == '{"ü":"é"}'.encode("utf-8")


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX modes")
def test_journal_modes_and_gitignore(tmp_path, monkeypatch):
    monkeypatch.delenv("FI_RUN_DIR")
    result = experiments.run(ROWS[:1], lambda r: 1, upload=False, progress=False)
    run_dir = Path(result.journal_dir)
    assert run_dir.parent == tmp_path / ".futureagi" / "runs"
    assert (tmp_path / ".futureagi" / ".gitignore").read_text() == "runs/\n"
    assert stat.S_IMODE(os.stat(run_dir).st_mode) == 0o700
    for name in ("plan.json", "journal.jsonl"):
        assert stat.S_IMODE(os.stat(run_dir / name).st_mode) == 0o600
    plan = json.loads((run_dir / "plan.json").read_text())
    assert plan["schema_version"] == 1 and plan["sdk_version"]
    assert not (run_dir / "lock").exists()


def test_resume_runs_only_missing_identities():
    calls = []

    def task(row):
        calls.append(row.id)
        return row["q"].upper()

    first = experiments.run(ROWS, task, upload=False, progress=False)
    journal = Path(first.journal_dir) / "journal.jsonl"
    lines = journal.read_text().splitlines()
    journal.write_text("\n".join(lines[:3]) + "\n" + lines[3][:20])  # a kill: 3 items + a torn line
    kept = {json.loads(l)["example_id"]: json.loads(l)["receipt_key"] for l in lines[:3]}
    calls.clear()
    again = experiments.run(ROWS, task, resume=first.run_id, upload=False, progress=False)
    assert again.run_id == first.run_id
    assert sorted(calls) == sorted(set(r["id"] for r in ROWS) - set(kept))
    assert len(again.items) == 5
    for item in again.items:
        if item.example_id in kept:
            assert item.receipt_key == kept[item.example_id]


def test_resume_refuses_a_different_plan():
    first = experiments.run(ROWS, lambda r: 1, upload=False, progress=False)
    with pytest.raises(JournalError):
        experiments.run(ROWS[:2], lambda r: 1, resume=first.run_id, upload=False, progress=False)


def test_lock_live_and_stale(tmp_path):
    j = _journal.Journal("run-x", tmp_path / "runs")
    j.create({"items": []})
    other = _journal.Journal("run-x", tmp_path / "runs")
    (j.lock_path).write_text(str(os.getppid()))  # a live process that is not us
    with pytest.raises(RunLockedError):
        other.acquire()
    (j.lock_path).write_text("999999")  # a dead process: stale, taken over
    other.acquire()
    assert j.lock_path.read_text() == str(os.getpid())
    j.close()


def test_redaction_in_journal_and_plan(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-unit-test-0123456789")
    result = experiments.run(
        ROWS[:1],
        lambda r: "leaked sk-unit-test-0123456789 here",
        params={"api_key": "abc", "model": "m"},
        metadata={"token": "t0p-secret-value"},
        upload=False,
        progress=False,
    )
    text = (Path(result.journal_dir) / "journal.jsonl").read_text()
    plan = (Path(result.journal_dir) / "plan.json").read_text()
    assert "sk-unit-test-0123456789" not in text and "[redacted]" in text
    assert '"api_key": "[redacted]"' in plan and '"model": "m"' in plan
    assert "t0p-secret-value" not in plan


def test_redactor_by_key_and_value():
    r = Redactor(["supersecret-1"])
    assert r.value({"Authorization": "x", "nested": {"password": "p"}, "msg": "a supersecret-1 b"}) == {
        "Authorization": "[redacted]",
        "nested": {"password": "[redacted]"},
        "msg": "a [redacted] b",
    }
