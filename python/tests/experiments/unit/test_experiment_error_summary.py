"""L-SDK2g review fixes. No network, no model (the judge answers through an httpx.MockTransport).

- M2 (b), as ruled after wave 2g: the policy governs a failed trial, as the product's governs an errored try (under
  ``zero`` it is 0 and a fail in every evaluator's numbers; under ``exclude`` it is left out), and an evaluator's
  error score is left out under either policy and counts in ``error_rate``. The review's probe is pinned here with
  the product's numbers, and the docs say so.
- S6: ``--verbose``'s judge line comes from the judge's own POST, and no key or Authorization header is in it.
- S7: an evaluator that only gives numbers has no pass rate, so its error note names the mean alone; the gate's
  number is rounded.
"""

import asyncio
import inspect
import json
import logging
from pathlib import Path

import httpx
import pytest

from fi import experiments
from fi.experiments import results as results_module
from fi.experiments._cli import commands
from fi.experiments._dataset import load_local
from fi.experiments._engine_summary import print_summary
from fi.experiments.evaluators import _judge_http
from fi.experiments.evaluators._base import EvalContext
from fi.experiments.evaluators.judge import Judge
from fi.experiments.results import EvalScore, ExperimentResult, TrialResult, counts_note, shown_number
from tests.experiments.unit.judge_helpers import part_verdict, with_criteria

FAKE = "-".join(("judge", "fake", "value", "0123456789"))


# ---- M2 (a) ---------------------------------------------------------------------------------------------------------

def _rows(n):
    return [{"q": i} for i in range(1, n + 1)]


def _task_errors_on_4(row):
    if row.input == 4:
        raise RuntimeError("the task errored on row 4")
    return row.input


def _ok(output):
    return True


def _raises_on_3(output):
    if output == 3:
        raise ValueError("the evaluator raised on row 3")
    return True


@pytest.mark.parametrize("policy, rate, gate_ok", [("zero", 0.75, False), ("exclude", 1.0, True)])
def test_a_failed_trial_is_what_the_policy_governs(policy, rate, gate_ok, monkeypatch):
    """The review's probe (cache/l-sdk2g-review/probe/probe_policy_scope.py): the task errors on 1 of 4 rows and the
    evaluator passes the other 3. As in the product: 3 of 4 under zero, 3 of 3 under exclude; the failed trial is in
    failed and error_rate either way, which --max-error-rate gates on."""
    monkeypatch.delenv("CI", raising=False)
    res = experiments.run(_rows(4), _task_errors_on_4, [_ok], upload=False, progress=False, trace=False,
                          error_policy=policy)
    s = res.summary()
    ev = s.evaluators["_ok"]
    assert (ev.pass_rate, ev.n, ev.errors, ev.failed_trials, s.failed, s.error_rate) == (rate, 3, 0, 1, 1, 0.25)
    assert res.assert_passing(0.9, raise_on_fail=False).passed is gate_ok
    gate = res.assert_passing(0.5, max_error_rate=0.0, raise_on_fail=False)
    assert not gate.passed and gate.exit_code == 5 and gate.reasons == [
        "error rate 0.250 > 0.0 [failed trials 1; trials with an error score 0; of 4 that ran]"]


@pytest.mark.parametrize("policy", ["zero", "exclude"])
def test_an_evaluator_error_score_is_left_out_under_either_policy(policy):
    """The review's second probe: the evaluator raises on 1 of 3 rows and passes 2. As in the product: 2 of 2."""
    res = experiments.run(_rows(3), lambda row: row.input, [_raises_on_3], upload=False, progress=False, trace=False,
                          error_policy=policy)
    s = res.summary()
    assert s.evaluators["_raises_on_3"].pass_rate == 1.0 and s.evaluators["_raises_on_3"].errors == 1
    assert s.error_rate == pytest.approx(1 / 3) and s.error_scores == 1


def test_the_docs_say_what_the_policy_governs():
    run_doc = inspect.getdoc(experiments.run) or ""
    module_doc = inspect.getdoc(results_module) or ""
    docs = {
        "run": run_doc,
        "arun": inspect.getdoc(experiments.arun) or "",
        "results": module_doc,
        "EvaluatorSummary": inspect.getdoc(results_module.EvaluatorSummary) or "",
        "summary": inspect.getdoc(ExperimentResult.summary) or "",
        "assert_passing": inspect.getdoc(ExperimentResult.assert_passing) or "",
        "--error-policy": next(kw["help"] for _, opts in commands.MORE for flags, kw in opts
                               if "--error-policy" in flags),
    }
    for where, text in docs.items():
        flat = " ".join(text.split())
        for stale in ("the SDK applies them to other errors", "a failed trial has no score under either policy",
                      "failed trials are in neither", "an error score is 0 and a miss", "(0, a miss",
                      "is in no evaluator's pass rate or mean under either policy"):
            assert stale.lower() not in flat.lower(), (where, stale)
    for where in ("run", "results", "EvaluatorSummary", "summary", "assert_passing", "--error-policy"):
        flat = " ".join(docs[where].split()).lower()
        assert "failed trial" in flat and "error score" in flat, where  # each says how both are counted
    flat = " ".join(module_doc.split())
    assert "the pass rate is 3 of 4 under ``zero`` and 3 of 3 under ``exclude``" in flat
    assert "it is 2 of 2 under either policy" in flat
    assert "An uploaded run does not carry the policy" in flat
    readme = (Path(results_module.__file__).parent / "README.md").read_text(encoding="utf-8")
    assert "## 6. How failed trials and error scores are counted (`error_policy`)" in readme


def test_the_published_schema_carries_the_new_evaluator_summary_text():
    from fi.experiments._cli.json_schema import build_schema
    from importlib import resources

    shipped = json.loads((resources.files("fi.experiments") / "schemas" / "cli-json.schema.json").read_text())
    assert shipped == build_schema()
    flat = json.dumps(shipped)
    assert "has no score of its own" in flat and "failed_trials" in flat and "error_scores" in flat


# ---- S6 -------------------------------------------------------------------------------------------------------------

@pytest.fixture
def judge_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", FAKE)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    async def no_wait(seconds):
        return None

    monkeypatch.setattr(_judge_http, "_sleep", no_wait)


def test_verbose_logs_each_judge_post_with_no_key_or_header(judge_key, caplog):
    """Through the judge itself (not _debug.http called directly): a 429 then a 200 for the part, after the criteria
    read; every POST is one DEBUG line naming host and path, the retry is named, and no line, message or argument
    holds the key, "Bearer" or "Authorization"."""
    seen = {"part": 0}
    headers_sent = []

    def part(request):
        headers_sent.append(request.headers.get("authorization"))
        seen["part"] += 1
        if seen["part"] == 1:
            return httpx.Response(429, json={"error": {"message": "busy"}}, headers={"retry-after": "0"})
        return httpx.Response(200, json=part_verdict(True))

    def handler(request):
        headers_sent.append(request.headers.get("authorization"))
        return with_criteria(part)(request)

    judge = Judge("Is the output polite?", model="m", transport=httpx.MockTransport(handler))
    row = load_local([{"q": "x", "expected": "y"}]).rows[0]
    with caplog.at_level(logging.DEBUG, logger="fi.experiments"):
        score = asyncio.run(judge.aevaluate(EvalContext(row=row, output="o")))["judge"]
    assert score.status == "assessed" and score.passed is True
    assert headers_sent and all(h == f"Bearer {FAKE}" for h in headers_sent if h)  # the key was sent, so it was there
    lines = [r.getMessage() for r in caplog.records if r.name == "fi.experiments"]
    posts = [ln for ln in lines if ln.startswith("judge POST ")]
    assert posts == ["judge POST https://api.openai.com/v1/chat/completions -> HTTP 200",
                     "judge POST https://api.openai.com/v1/chat/completions -> HTTP 429",
                     "judge POST https://api.openai.com/v1/chat/completions -> HTTP 200 (retry 1)"], lines
    raw = json.dumps([[r.msg, [str(a) for a in (r.args or ())]] for r in caplog.records])
    for secret in (FAKE, "Bearer", "Authorization", "authorization"):
        assert secret not in raw and not any(secret in ln for ln in lines), secret


def test_without_debug_the_judge_logs_nothing(judge_key, caplog):
    judge = Judge("Is the output polite?", model="m",
                  transport=httpx.MockTransport(with_criteria(lambda r: httpx.Response(200, json=part_verdict(True)))))
    row = load_local([{"q": "x"}]).rows[0]
    with caplog.at_level(logging.INFO, logger="fi.experiments"):
        asyncio.run(judge.aevaluate(EvalContext(row=row, output="o")))
    assert not [r for r in caplog.records if r.getMessage().startswith("judge POST")]


# ---- S7 -------------------------------------------------------------------------------------------------------------

def _numbers(scores, policy="zero"):
    items = [TrialResult(example_id=f"r{i}", number=i, trial=1, status="completed", scores={"score": s})
             for i, s in enumerate(scores)]
    return ExperimentResult(run_id="r", name="n", status="no_upload", items=items, error_policy=policy)


ERR = EvalScore(status="error", explanation="ValueError: boom")


def test_a_numbers_only_evaluator_s_gate_reason_names_the_mean_and_rounds():
    """The review's probe: 'score: 0.5333333333333333 < 0.6 (1 error score counted as 0, a miss: ...)' said "a miss"
    for an evaluator with no pass rate, and printed every digit."""
    res = _numbers([EvalScore(0.9), EvalScore(0.7), EvalScore(0.0), ERR])  # the error score is left out of the mean
    ev = res.summary().evaluators["score"]
    assert ev.pass_rate is None and ev.mean == pytest.approx(1.6 / 3)
    assert res.assert_passing(0.6, raise_on_fail=False).reasons == [
        "score: 0.533 < 0.6 [failed trials 0; error scores 1: left out of the mean, counted in the error rate]"]
    lines: list = []
    print_summary(lines.append, res)
    row = next(ln for ln in lines if ln.strip().startswith("score"))
    assert row.endswith("[failed trials 0; error scores 1: left out of the mean, counted in the error rate]"), row
    exc = _numbers([EvalScore(0.9), EvalScore(0.1), ERR], "exclude")
    assert exc.assert_passing(0.6, raise_on_fail=False).reasons == [
        "score: 0.5 < 0.6 [failed trials 0; error scores 1: left out of the mean, counted in the error rate]"]


def test_an_evaluator_with_a_pass_rate_names_both_in_its_note():
    def ev(cells, policy="zero"):
        items = [TrialResult(example_id=f"r{i}", number=i, trial=1, status="failed") if c is None else
                 TrialResult(example_id=f"r{i}", number=i, trial=1, status="completed", scores={"j": c})
                 for i, c in enumerate(cells)]
        res = ExperimentResult(run_id="r", name="n", status="no_upload", items=items, error_policy=policy,
                               evaluator_names=["j"])
        return res.summary().evaluators["j"]

    ok, err = EvalScore(True), ERR
    assert counts_note(ev([ok, None])) == ("[failed trials 1: counted as 0, a fail, in the pass rate and the mean "
                                           "(error policy zero, the default); error scores 0]")
    assert counts_note(ev([ok, None, None, err])) == (
        "[failed trials 2: each counted as 0, a fail, in the pass rate and the mean (error policy zero, the default); "
        "error scores 1: left out of the pass rate and the mean, counted in the error rate]")
    assert counts_note(ev([ok, None], "exclude")) == ("[failed trials 1: left out of the pass rate and the mean (error "
                                                      "policy exclude); error scores 0]")
    assert counts_note(ev([ok])) == "[failed trials 0; error scores 0]"


@pytest.mark.parametrize("value, threshold, shown", [
    (0.5333333333333333, 0.6, "0.533"),
    (2 / 3, 0.7, "0.667"),
    (0.5, 0.6, "0.5"),
    (0.75, 0.8, "0.75"),
    (0.0, 0.5, "0"),
    (0.59996, 0.6, "0.59996"),  # 3 or 4 decimals would read 0.6 < 0.6: more are shown
    (0.6999999, 0.7, "0.6999999"),
])
def test_shown_number_never_reads_as_the_threshold(value, threshold, shown):
    assert shown_number(value, threshold) == shown
    assert float(shown_number(value, threshold)) < threshold


def test_the_cli_gate_line_is_rounded(tmp_path, monkeypatch):
    from tests.experiments.unit.cli_helpers import cli

    monkeypatch.chdir(tmp_path)
    (tmp_path / "run_eval.py").write_text(
        "from fi import experiments\n"
        "def graded(row, output):\n    return row.input != 2\n"
        "experiments.run([{'q': 1}, {'q': 2}, {'q': 3}], lambda row: row.input, [graded], upload=False, "
        "trace=False)\n")
    code, out, err = cli("run", "run_eval.py", "--fail-under", "0.7", "--no-env-file")
    assert code == 1 and "graded: 0.667 < 0.7" in err and "0.6666" not in err, err[-600:]
