"""scripts/experiments/release_gate.py: an option ships only when every one of its rows is GREEN."""

import importlib.util
import json
from pathlib import Path

import pytest

pytest.importorskip("yaml")
SCRIPT = Path(__file__).resolve().parents[4] / "scripts" / "experiments" / "release_gate.py"
spec = importlib.util.spec_from_file_location("release_gate", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def _files(tmp_path, rows, options="options:\n  py:run: [SDK-01, SDK-20]\n  cli:run --dataset: [CLI-05]\n"):
    (tmp_path / "o.yaml").write_text("schema_version: 1\n" + options)
    (tmp_path / "t.json").write_text(json.dumps({"rows": rows}))
    return ["--truth", str(tmp_path / "t.json"), "--options", str(tmp_path / "o.yaml")]


def test_all_green_passes(tmp_path, capsys):
    args = _files(tmp_path, {"SDK-01": "GREEN", "SDK-20": "GREEN", "CLI-05": "GREEN"})
    assert gate.main(args) == 0
    assert "2 of 2 options" in capsys.readouterr().out


def test_red_blocked_and_unrecorded_rows_fail_and_are_named(tmp_path, capsys):
    args = _files(tmp_path, {"SDK-01": "GREEN", "SDK-20": "RED"})
    assert gate.main(args + ["--json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["blocked"] == {"py:run": {"SDK-20": "RED"}, "cli:run --dataset": {"CLI-05": "NOT_RECORDED"}}


def test_an_option_without_rows_is_an_orphan(tmp_path):
    args = _files(tmp_path, {"SDK-01": "GREEN"}, options="options:\n  py:run: []\n")
    assert gate.main(args) == 1


def test_unreadable_truth_is_exit_2(tmp_path):
    assert gate.main(["--truth", str(tmp_path / "missing.json")]) == 2


def test_the_real_options_file_loads_and_today_nothing_is_ready(tmp_path):
    """The shipped _options.yaml against an empty truth table: every option is blocked."""
    options = gate.load_options(gate.DEFAULT_OPTIONS)
    report = gate.evaluate(options, {})
    assert report["ready"] == 0 and len(report["blocked"]) == len(options) > 100


# ---- holds ----------------------------------------------------------------------------------------

def test_a_held_option_is_not_ready_whatever_its_rows_say(tmp_path, capsys):
    args = _files(tmp_path, {"SDK-01": "GREEN", "SDK-20": "GREEN", "CLI-05": "GREEN"},
                  options="options:\n  py:run: [SDK-01, SDK-20]\n  cli:run --dataset: [CLI-05]\n"
                          "holds:\n  py:run: the rate gate is not ruled\n")
    assert gate.main(args + ["--json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["ready"] == 1 and report["held"] == {"py:run": "the rate gate is not ruled"}
    assert report["blocked"] == {"py:run": {"(hold)": "HOLD: the rate gate is not ruled"}}
    assert gate.main(args) == 1
    assert "NOT READY  py:run: (hold) HOLD: the rate gate is not ruled" in capsys.readouterr().out


def test_a_hold_on_an_option_the_file_does_not_list_is_exit_2(tmp_path, capsys):
    args = _files(tmp_path, {"SDK-01": "GREEN"}, options="options:\n  py:run: [SDK-01]\nholds:\n  py:nope: why\n")
    assert gate.main(args) == 2
    assert "holds name options the file does not list: py:nope" in capsys.readouterr().err


def test_the_real_options_file_has_no_hold_since_the_judge_rate_gate_passed_at_two_consecutive_pins():
    """Keep the accepted two-snapshot rate-gate criterion without private collection identifiers."""
    assert gate.load_holds(gate.DEFAULT_OPTIONS) == {}
    text = " ".join(gate.DEFAULT_OPTIONS.read_text(encoding="utf-8").replace("\n#", " ").split())
    assert "two consecutive SDK snapshots under one gate definition" in text
    assert "Every gate run passed at both snapshots" in text and "B1-B24" in text
