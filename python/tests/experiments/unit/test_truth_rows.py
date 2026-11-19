"""Truth-row migrations preserve failing verdicts and never merge aliases."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location("row_gate", ROOT / "scripts/experiments/release_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


@pytest.mark.parametrize("status,code", [("GREEN", 0), ("RED", 1), ("BLOCKED", 1),
                                        ("NOT_RUN", 1), ("NOT_RECORDED", 1)])
def test_explicit_mapping_preserves_each_verdict(tmp_path, status, code):
    options = tmp_path / "options.yaml"
    truth = tmp_path / "truth.json"
    mapping = tmp_path / "rows.json"
    options.write_text("options:\n  py:run: [run.dataset]\n")
    truth.write_text(json.dumps({"rows": {"old.dataset": status}}))
    mapping.write_text(json.dumps({"old.dataset": "run.dataset"}))
    args = ["--options", str(options), "--truth", str(truth), "--row-map", str(mapping)]
    assert gate.main(args) == code
    truth.write_text(json.dumps({"rows": {"run.dataset": status}}))
    assert gate.main(args) == code


@pytest.mark.parametrize("rows,mapping", [
    ({"old": "RED", "new": "GREEN"}, {"old": "new"}),
    ({"old": "GREEN", "new": "GREEN"}, {"old": "new"}),
    ({"one": "RED", "two": "GREEN"}, {"one": "new", "two": "new"}),
])
def test_collisions_fail_even_if_statuses_agree(tmp_path, rows, mapping):
    options, truth, aliases = (tmp_path / n for n in ("o.yaml", "t.json", "m.json"))
    options.write_text("options:\n  py:run: [new]\n")
    truth.write_text(json.dumps({"rows": rows}))
    aliases.write_text(json.dumps(mapping))
    assert gate.main(["--options", str(options), "--truth", str(truth),
                      "--row-map", str(aliases)]) == 2


def test_unmapped_required_row_stays_not_recorded(tmp_path):
    options, truth, aliases = (tmp_path / n for n in ("o.yaml", "t.json", "m.json"))
    options.write_text("options:\n  py:run: [required]\n")
    truth.write_text(json.dumps({"rows": {"unrelated": "GREEN"}}))
    aliases.write_text(json.dumps({"old": "required"}))
    assert gate.main(["--options", str(options), "--truth", str(truth),
                      "--row-map", str(aliases)]) == 1
