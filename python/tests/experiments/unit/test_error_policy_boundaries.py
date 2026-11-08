"""The error policy: ``error_policy`` governs a FAILED
TRIAL, as the product's run error policy governs an errored try. Under ``zero`` (the default) a failed trial counts as
0 and a fail in every evaluator's mean and pass rate; under ``exclude`` it is left out, with its count shown. An
evaluator's ERROR SCORE is shown with its count and left out of that evaluator's mean and pass rate under either
policy, as the product leaves a score error out, and it still counts toward ``error_rate`` / ``--max-error-rate``. A
gate fails for an evaluator with no scored rows and says why. The closing lines and gate reasons print both counts and
how each was counted. The names stay the product's (``zero`` | ``exclude``; ``fail`` is not offered, no alias for the
wave-2f ``count``). No network, no model."""

import inspect
import json
import re

import pytest

from fi import experiments
from fi.experiments._engine_config import RunConfig
from fi.experiments._engine_summary import print_summary
from fi.experiments.errors import UsageError
from fi.experiments.results import (DEFAULT_ERROR_POLICY, ERROR_POLICIES, EvalScore, ExperimentResult, TrialError,
                                    TrialResult, check_error_policy, counts_note)
from tests.experiments.unit.cli_helpers import cli

PASS, FAIL = EvalScore(True), EvalScore(False)
ERROR = EvalScore(status="error", explanation="ValueError: the judge's answer for a part has no true/false met")
FAILED = "failed"  # a trial whose task raised: no score of its own


def _result(cells, policy=None, name="judge", evaluators=None):
    """One trial per cell: an EvalScore for a completed trial, FAILED for a failed one."""
    items = []
    for i, cell in enumerate(cells):
        if cell is FAILED:
            items.append(TrialResult(example_id=f"r{i}", number=i, trial=1, status="failed",
                                     error=TrialError(type="RuntimeError", message="the task raised")))
        else:
            items.append(TrialResult(example_id=f"r{i}", number=i, trial=1, status="completed", scores={name: cell}))
    kw = {} if policy is None else {"error_policy": policy}
    if evaluators is not None:
        kw["evaluator_names"] = evaluators
    return ExperimentResult(run_id="run", name="n", status="no_upload", items=items, **kw)


# ---- failed trials: what the policy governs --------------------------------------------------------------------------

def test_by_default_a_failed_trial_is_zero_and_a_fail_in_every_evaluator():
    s = _result([PASS, PASS, PASS, FAILED]).summary()
    ev = s.evaluators["judge"]
    assert (ev.pass_rate, ev.mean, ev.failed_trials, ev.errors, ev.scored, ev.n) == (0.75, 0.75, 1, 0, 3, 3)
    assert ev.error_policy == "zero" and s.failed == 1 and s.error_rate == 0.25


def test_exclude_leaves_a_failed_trial_out_with_its_count():
    ev = _result([PASS, PASS, PASS, FAILED], "exclude").summary().evaluators["judge"]
    assert (ev.pass_rate, ev.mean, ev.failed_trials) == (1.0, 1.0, 1)
    same = _result([PASS, PASS, PASS, FAILED]).summary("exclude").evaluators["judge"]  # summary()'s own override
    assert same.pass_rate == 1.0 and same.error_policy == "exclude"


def test_a_failed_trial_counts_in_every_evaluator_of_the_run():
    items = [TrialResult(example_id="a", number=1, trial=1, status="completed",
                         scores={"x": PASS, "y": EvalScore(0.8)}),
             TrialResult(example_id="b", number=2, trial=1, status="failed", error=TrialError(type="timeout"))]
    res = ExperimentResult(run_id="r", name="n", status="no_upload", items=items, evaluator_names=["x", "y"])
    s = res.summary()
    assert s.evaluators["x"].pass_rate == 0.5 and s.evaluators["x"].mean == 0.5
    assert s.evaluators["y"].pass_rate is None and s.evaluators["y"].mean == pytest.approx(0.4)  # numbers only
    assert s.timeouts == 1 and s.failed == 1


def test_a_run_whose_every_trial_failed_still_lists_its_evaluators():
    s = _result([FAILED, FAILED], evaluators=["judge"]).summary()
    ev = s.evaluators["judge"]
    assert (ev.n, ev.scored, ev.failed_trials, ev.pass_rate, ev.mean) == (0, 0, 2, 0.0, 0.0)
    ex = _result([FAILED, FAILED], "exclude", evaluators=["judge"]).summary().evaluators["judge"]
    assert ex.pass_rate is None and ex.mean is None and ex.failed_trials == 2


def test_skipped_trials_are_in_neither_count():
    items = [TrialResult(example_id="a", number=1, trial=1, status="completed", scores={"judge": PASS}),
             TrialResult(example_id="b", number=2, trial=1, status="skipped", error=TrialError(type="cost_cap"))]
    s = ExperimentResult(run_id="r", name="n", status="stopped_cost", items=items).summary()
    assert s.evaluators["judge"].pass_rate == 1.0 and s.evaluators["judge"].failed_trials == 0 and s.error_rate == 0


# ---- error scores: always left out, always counted in the error rate --------------------------------------------------

@pytest.mark.parametrize("policy", ["zero", "exclude"])
def test_an_error_score_is_shown_and_left_out_under_either_policy(policy):
    s = _result([PASS, PASS, FAIL, ERROR], policy).summary()
    ev = s.evaluators["judge"]
    assert ev.pass_rate == pytest.approx(2 / 3) and ev.mean == pytest.approx(2 / 3)
    assert (ev.errors, ev.scored, ev.n) == (1, 3, 4)
    assert s.error_scores == 1 and s.error_score_trials == 1 and s.error_rate == 0.25 and s.failed == 0


def test_a_numbers_only_evaluator_leaves_its_error_out_of_the_mean_and_counts_failed_trials_as_zero():
    ev = _result([EvalScore(0.8), EvalScore(0.6), ERROR]).summary().evaluators["judge"]
    assert ev.pass_rate is None and ev.mean == pytest.approx(0.7)
    ev = _result([EvalScore(0.8), EvalScore(0.6), FAILED]).summary().evaluators["judge"]
    assert ev.pass_rate is None and ev.mean == pytest.approx(1.4 / 3)


def test_no_failures_no_difference():
    for policy in ("zero", "exclude"):
        ev = _result([PASS, FAIL, PASS, PASS], policy).summary().evaluators["judge"]
        assert ev.pass_rate == 0.75 and ev.errors == 0 and ev.failed_trials == 0


# ---- the gate --------------------------------------------------------------------------------------------------------

def test_fail_under_counts_a_failed_trial_as_a_fail_by_default():
    res = _result([PASS, PASS, PASS, FAILED])
    gate = res.assert_passing(0.9, raise_on_fail=False)
    assert not gate.passed and gate.exit_code == 1
    assert gate.reasons == ["judge: 0.75 < 0.9 [failed trials 1: counted as 0, a fail, in the pass rate and the mean "
                            "(error policy zero, the default); error scores 0]"]
    assert _result([PASS, PASS, PASS, FAILED], "exclude").assert_passing(0.9, raise_on_fail=False).passed
    assert res.assert_passing(0.9, raise_on_fail=False, error_policy="exclude").passed


def test_an_error_score_does_not_lower_the_pass_rate_but_fails_max_error_rate():
    res = _result([PASS, PASS, PASS, ERROR])
    assert res.assert_passing(0.9, raise_on_fail=False).passed
    gate = res.assert_passing(0.9, max_error_rate=0.0, raise_on_fail=False)
    assert not gate.passed and gate.exit_code == 5
    assert gate.reasons == ["error rate 0.250 > 0.0 [failed trials 0; trials with an error score 1; of 4 that ran]"]


def test_a_gate_fails_for_an_evaluator_with_no_scored_rows_and_says_why():
    for policy in ("zero", "exclude"):
        gate = _result([ERROR, ERROR, ERROR], policy).assert_passing(0.5, raise_on_fail=False)
        assert not gate.passed and gate.exit_code == 1
        assert gate.reasons[0].startswith("judge: no scored rows, so it cannot pass 0.5: every score it returned was "
                                          "an error (3) [failed trials 0; error scores 3: left out of the pass rate "
                                          "and the mean, counted in the error rate]"), gate.reasons
    # threshold 0 cannot let a broken evaluator through either
    assert not _result([ERROR, ERROR]).assert_passing(0.0, raise_on_fail=False).passed
    # every trial failed: under zero the numbers are 0, and still no scored row
    gate = _result([FAILED, FAILED], evaluators=["judge"]).assert_passing(0.0, raise_on_fail=False)
    assert not gate.passed and "judge: no scored rows, so it cannot pass 0.0: no trial completed [failed trials 2: " \
        "each counted as 0, a fail, in the pass rate and the mean (error policy zero, the default); error scores 0]" \
        in gate.reasons
    gate = _result([FAILED, FAILED], "exclude", evaluators=["judge"]).assert_passing(0.5, raise_on_fail=False)
    assert not gate.passed and "failed trials 2: left out of the pass rate and the mean (error policy exclude)" in \
        gate.reasons[0]


def test_every_reason_prints_both_counts():
    gate = _result([PASS, FAIL, ERROR, FAILED]).assert_passing(0.9, raise_on_fail=False)
    assert gate.reasons == ["judge: 0.333 < 0.9 [failed trials 1: counted as 0, a fail, in the pass rate and the mean "
                            "(error policy zero, the default); error scores 1: left out of the pass rate and the "
                            "mean, counted in the error rate]"]


def test_counts_note_for_a_numbers_only_evaluator_names_the_mean_alone():
    ev = _result([EvalScore(0.5), ERROR, FAILED, FAILED]).summary().evaluators["judge"]
    assert counts_note(ev) == ("[failed trials 2: each counted as 0 in the mean (error policy zero, the default); "
                               "error scores 1: left out of the mean, counted in the error rate]")


# ---- names -----------------------------------------------------------------------------------------------------------

def test_an_unknown_policy_is_a_usage_error_that_names_the_two_policies():
    # "count" was the wave-2f name (no alias: the SDK is unreleased); "fail" is the product's, not offered by the SDK
    for bad in ("drop", "count", "fail", "Zero", None):
        with pytest.raises(UsageError, match=r"error_policy must be 'zero' .* or 'exclude' ") as got:
            _result([PASS]).summary(bad) if bad is not None else check_error_policy(bad)
        assert repr(bad) in str(got.value)
    for bad in ("count", "fail"):
        with pytest.raises(UsageError, match="error_policy must be 'zero'"):
            experiments.run([{"q": 1}], lambda row: 1, [], upload=False, progress=False, error_policy=bad)


def test_the_names_are_the_products():
    assert ERROR_POLICIES == ("zero", "exclude") and DEFAULT_ERROR_POLICY == "zero"
    assert _result([PASS]).error_policy == "zero" and _result([PASS]).summary().error_policy == "zero"
    assert inspect.signature(experiments.run).parameters["error_policy"].default == "zero"
    assert inspect.signature(experiments.arun).parameters["error_policy"].default == "zero"
    assert RunConfig.__dataclass_fields__["error_policy"].default == "zero"


# ---- the closing lines -----------------------------------------------------------------------------------------------

def test_the_closing_lines_always_print_both_counts_and_how_each_was_counted():
    for policy, note in (
            ("zero", "[failed trials 1: counted as 0, a fail, in the pass rate and the mean (error policy zero, the "
                     "default); error scores 1: left out of the pass rate and the mean, counted in the error rate]"),
            ("exclude", "[failed trials 1: left out of the pass rate and the mean (error policy exclude); error "
                        "scores 1: left out of the pass rate and the mean, counted in the error rate]")):
        lines: list = []
        print_summary(lines.append, _result([PASS, ERROR, FAILED], policy))
        row = next(ln for ln in lines if ln.strip().startswith("judge"))
        assert row.endswith(note), row
    lines = []
    print_summary(lines.append, _result([PASS, FAIL]))
    assert next(ln for ln in lines if ln.strip().startswith("judge")).endswith("[failed trials 0; error scores 0]")


# ---- through run() and the CLI ---------------------------------------------------------------------------------------

def _task(row):
    if row.input == 9:
        raise RuntimeError("the task errored on this row")
    return row.input


def _flaky(output):
    if output == 2:
        raise ValueError("cannot score this one")
    return output == 1


def test_run_keeps_its_policy_and_its_evaluators_on_the_result(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    rows = [{"q": 1}, {"q": 1}, {"q": 0}, {"q": 2}, {"q": 9}]  # pass, pass, fail, error score, failed trial
    res = experiments.run(rows, _task, [_flaky], upload=False, progress=False, trace=False)
    ev = res.summary().evaluators["_flaky"]
    assert res.error_policy == "zero" and res.evaluator_names == ["_flaky"]
    assert (ev.errors, ev.failed_trials, ev.pass_rate) == (1, 1, 0.5)  # 2 of (3 scored + 1 failed trial)
    assert res.summary().error_rate == pytest.approx(2 / 5)
    res = experiments.run(rows, _task, [_flaky], upload=False, progress=False, trace=False, error_policy="exclude")
    assert res.error_policy == "exclude" and res.summary().evaluators["_flaky"].pass_rate == pytest.approx(2 / 3)


def _run_file(tmp_path, extra=""):
    (tmp_path / "run_eval.py").write_text(
        "from fi import experiments\n"
        "def task(row):\n"
        "    if row.input == 9:\n        raise RuntimeError('the task errored on this row')\n"
        "    return row.input\n"
        "def flaky(output):\n"
        "    if output == 2:\n        raise ValueError('cannot score this one')\n"
        "    return output == 1\n"
        f"experiments.run([{{'q': 1}}, {{'q': 1}}, {{'q': 1}}, {{'q': 2}}, {{'q': 9}}], task, [flaky], "
        f"upload=False, trace=False{extra})\n")  # no tracing: these runs need no spans (and run on Python 3.14, TA-1)


def test_cli_fail_under_counts_a_failed_trial_by_default_and_error_policy_exclude_leaves_it_out(tmp_path, monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    _run_file(tmp_path)  # 3 pass, 1 error score (left out), 1 failed trial: 3 of 4 under zero, 3 of 3 under exclude
    code, out, err = cli("run", "run_eval.py", "--fail-under", "0.8", "--quiet")
    assert code == 1 and ("flaky: 0.75 < 0.8 [failed trials 1: counted as 0, a fail, in the pass rate and the mean "
                          "(error policy zero, the default); error scores 1: left out of the pass rate and the mean, "
                          "counted in the error rate]") in err, err
    code, out, err = cli("run", "run_eval.py", "--fail-under", "0.8", "--error-policy", "exclude", "--json")
    doc = json.loads(out)
    assert code == 0 and doc["exit_code"] == 0
    ev = doc["runs"][0]["summary"]["evaluators"]["flaky"]
    assert ev["errors"] == 1 and ev["failed_trials"] == 1 and ev["error_policy"] == "exclude" and ev["pass_rate"] == 1
    assert doc["runs"][0]["summary"]["error_policy"] == "exclude" and doc["runs"][0]["summary"]["error_scores"] == 1
    code, out, err = cli("run", "run_eval.py", "--fail-under", "0.8", "--error-policy", "exclude",
                         "--max-error-rate", "0.3", "--quiet")
    assert code == 5 and "error rate 0.400 > 0.3 [failed trials 1; trials with an error score 1; of 5 that ran]" in err


def test_cli_flag_overrides_the_run_files_policy_and_a_bad_value_is_a_usage_error(tmp_path, monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    _run_file(tmp_path, ", error_policy='exclude'")
    assert cli("run", "run_eval.py", "--fail-under", "0.8", "--quiet")[0] == 0  # the run file's own policy
    assert cli("run", "run_eval.py", "--fail-under", "0.8", "--quiet", "--error-policy", "zero")[0] == 1
    for bad in ("count", "fail"):  # the wave-2f name (no alias) and the product's unoffered "fail"
        code, out, err = cli("run", "run_eval.py", "--error-policy", bad)
        line = next((ln for ln in err.splitlines() if "error:" in ln), "")  # argparse quotes the names on some Pythons
        assert code == 2 and "--error-policy" in line and repr(bad) in line, err
        assert re.search(r"choose from '?zero'?, '?exclude'?\)", line), line
        assert "Done" not in out + err  # refused before any run
