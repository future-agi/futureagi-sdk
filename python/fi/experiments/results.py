"""Result types: frozen pydantic v2 models.

this release ``summary()``: per evaluator mean, pass rate and errors; latency p50/p95/p99; cost; tokens;
skipped; timeouts; failures grouped by exception class. Bootstrap intervals arrive in a later release.

**Failed trials, error scores and the pass rate**:

The runner's ``timeout_s`` bounds the task's attempts in each trial, including retries, not evaluators.
Evaluators keep their own limits; their timeouts produce error scores without extending or reusing that budget.

- ``error_policy`` governs a *failed trial* (the task raised or timed out). Under ``error_policy="zero"`` (the
  default) a failed trial counts as 0 and as a fail in every evaluator's mean and pass rate. Under
  ``error_policy="exclude"`` (``run(error_policy=...)``, CLI ``--error-policy exclude``) it is left out of them, and
  its count is shown. This is what the product's run error policy does with an errored try.
- An evaluator's *error score* (status ``error``: the evaluator raised or hit its own timeout, a judge answer
  held no verdict, a provider refused the call) is shown with its count and left out of that evaluator's mean
  and pass rate under either policy, as the product leaves a score error out. It still counts toward
  ``Summary.error_rate``, which ``--max-error-rate``
  (``max_error_rate``) gates on, so a broken evaluator is never silent.
- A gate (``assert_passing``, CLI ``--fail-under``) fails for an evaluator with no scored rows (every score an error,
  or no trial completed), and its reason says why.
- The closing lines and every gate reason print both counts, failed trials and error scores, and how each was
  counted.

So with the task erroring on 1 of 4 rows and the evaluator passing the other 3, the pass rate is 3 of 4 under
``zero`` and 3 of 3 under ``exclude``; with the evaluator raising on 1 of 3 rows and passing 2, it is 2 of 2 under
either policy, with 1 error score shown and an error rate of 1 in 3. The names are the product's (``zero`` |
``exclude``; its third, ``fail``, is not offered). An uploaded run does not carry the policy: the server's run has no
error-policy field today, so the product's page counts with its own default.
"""

from __future__ import annotations

import math
import os
from collections import Counter
from pathlib import Path
from typing import Any, Literal, Mapping, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from fi.experiments.errors import EXIT_CI_ERRORS, EXIT_GATE, EXIT_OK, UsageError

_FROZEN = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)
ErrorPolicy = Literal["zero", "exclude"]
ERROR_POLICIES = ("zero", "exclude")  # the product's names; its "fail" is not offered
DEFAULT_ERROR_POLICY = "zero"  # a failed trial is 0 and a fail in every evaluator's numbers (the product's default)


def check_error_policy(policy: Any) -> str:
    if policy not in ERROR_POLICIES:
        raise UsageError(f"error_policy must be 'zero' (a failed trial is 0 and a fail; the default) or 'exclude' "
                         f"(failed trials left out, their count shown), got {policy!r}")
    return policy


class EvalScore(BaseModel):
    """One score. ``value`` is a number (bools become 1.0 / 0.0); ``passed`` is set when the
    evaluator defines pass and fail."""

    model_config = _FROZEN
    value: Optional[float] = None
    label: Optional[str] = None
    explanation: Optional[str] = None
    status: Literal["assessed", "error", "skipped"] = "assessed"
    passed: Optional[bool] = None

    def __init__(self, value: Any = None, label: Optional[str] = None, explanation: Optional[str] = None,
                 status: str = "assessed", passed: Optional[bool] = None, **kw: Any) -> None:
        if isinstance(value, bool):
            passed = value if passed is None else passed
            value = 1.0 if value else 0.0
        super().__init__(value=value, label=label, explanation=explanation, status=status, passed=passed, **kw)


class TrialError(BaseModel):
    model_config = _FROZEN
    type: str  # exception class name, or "timeout" / "cost_cap" / "fail_fast" / "interrupted"
    message: str = ""
    traceback: Optional[str] = None


class TrialResult(BaseModel):
    model_config = _FROZEN
    example_id: str
    number: int
    trial: int
    status: Literal["completed", "failed", "skipped"]
    output: Any = None
    error: Optional[TrialError] = None
    latency_ms: Optional[float] = None
    cost_usd: Optional[float] = None
    tokens: Optional[dict[str, int]] = None
    trace_id: Optional[str] = None
    root_span_id: Optional[str] = None
    attempts: int = 1
    scores: dict[str, EvalScore] = Field(default_factory=dict)
    receipt_key: Optional[str] = None


class EvaluatorSummary(BaseModel):
    """``n``: the scores this evaluator returned (error scores included); ``scored``: those in its numbers. A failed
    trial has no score of its own: under ``error_policy`` ``zero`` (the default) each of the run's ``failed_trials``
    is 0 and a fail in ``mean`` and ``pass_rate``, and under ``exclude`` it is left out. ``errors``, the evaluator's
    error scores, are always shown and left out of ``mean`` and ``pass_rate`` under either policy (they count in
    ``Summary.error_rate``)."""

    model_config = _FROZEN
    name: str
    n: int
    mean: Optional[float]
    pass_rate: Optional[float]
    errors: int
    error_policy: ErrorPolicy = DEFAULT_ERROR_POLICY
    scored: int = 0
    failed_trials: int = 0


class Summary(BaseModel):
    model_config = _FROZEN
    trials: int
    completed: int
    failed: int
    skipped: int
    timeouts: int
    error_rate: float
    evaluators: dict[str, EvaluatorSummary]
    latency_ms: dict[str, Optional[float]]
    cost_usd: Optional[float]
    tokens: dict[str, int]
    errors_by_type: dict[str, int]
    error_policy: ErrorPolicy = DEFAULT_ERROR_POLICY
    error_scores: int = 0  # every evaluator's error scores
    error_score_trials: int = 0  # completed trials with at least one error score (in error_rate)


class GateResult(BaseModel):
    model_config = _FROZEN
    passed: bool
    reasons: list[str]
    exit_code: int


def counts_note(ev: "EvaluatorSummary") -> str:
    """Both counts for an evaluator, and how each was counted, for the closing lines and the gate's reasons (dataset service
    decisions after wave 2g): its failed trials (by the policy) and its error scores (always left out). An evaluator
    that only gives numbers has no pass rate, so the note names the mean alone."""
    where = "the pass rate and the mean" if ev.pass_rate is not None or not ev.scored else "the mean"
    f, e = ev.failed_trials, ev.errors
    if not f:
        failed = "failed trials 0"
    elif ev.error_policy == "zero":
        fail = ", a fail," if where != "the mean" else ""
        each = "each " if f != 1 else ""
        failed = f"failed trials {f}: {each}counted as 0{fail} in {where} (error policy zero, the default)"
    else:
        failed = f"failed trials {f}: left out of {where} (error policy exclude)"
    errors = "error scores 0" if not e else f"error scores {e}: left out of {where}, counted in the error rate"
    return f"[{failed}; {errors}]"


def _no_scored_rows(ev: "EvaluatorSummary") -> str:
    if ev.errors and ev.errors == ev.n:
        return f"every score it returned was an error ({ev.errors})"
    if ev.failed_trials and not ev.n:
        return "no trial completed"
    return "it returned no score"


def shown_number(value: float, threshold: float) -> str:
    """A gate number for its reason: 3 decimals, or as many as it takes to stay below ``threshold`` (0.5999 < 0.6 is
    never shown as 0.6 < 0.6)."""
    for digits in (3, 4, 6):
        text = f"{round(value, digits):g}"
        if float(text) < threshold:
            return text
    return repr(value)


def _percentile(values: list[float], q: float) -> Optional[float]:
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return s[int(k)]
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


# What ``url`` opens today: the server's app_url names the run, but the page lists it only once
# the app shows SDK runs there (FE-2).
RUN_PAGE_IS = "the dataset's Experiments tab; it lists SDK runs once FE-2 ships"


class ExperimentResult(BaseModel):
    """One run's result. ``url`` is the ``app_url`` the server returns for the run, built from the deployment's
    configured frontend URL (SRV-4). **Today it is the dataset's Experiments tab, which does not list SDK runs
    yet:** its ``run=`` parameter selects this run once the app lists SDK runs there (FE-2). It is None when no app
    URL is known (the run was not uploaded, or the server has no frontend URL configured), and ``url_note`` then
    says why; the SDK never makes a link up."""

    model_config = _FROZEN
    run_id: str
    name: str
    url: Optional[str] = None
    url_note: Optional[str] = None  # why url is None (FN-05); None when url is set
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    experiment_id: Optional[str] = None
    status: Literal["completed", "partial", "stopped_cost", "failed_fast", "no_upload"]
    items: list[TrialResult]
    metadata: dict[str, Any] = Field(default_factory=dict)
    journal_dir: Optional[str] = None
    error_policy: ErrorPolicy = DEFAULT_ERROR_POLICY  # run(error_policy=...): how a failed trial counts
    evaluator_names: list[str] = Field(default_factory=list)  # the run's evaluators, so a run with no score lists them

    # ---- reading ----
    def scores(self, name: str) -> list[Optional[float]]:
        return [it.scores[name].value if name in it.scores else None for it in self.items]

    def failed(self) -> list[TrialResult]:
        return [it for it in self.items if it.status != "completed"]

    def summary(self, error_policy: Optional[str] = None) -> Summary:
        """The run's numbers. ``error_policy`` (default: the run's, ``zero``) says how a failed trial counts:
        ``zero``, 0 and a fail in every evaluator's mean and pass rate; ``exclude``, left out of them. An evaluator's
        error scores are left out of its mean and pass rate under either policy, and count in ``error_rate`` (the
        share of trials that ran and failed or got an error score), as ``failed`` counts the failed trials."""
        policy = check_error_policy(error_policy or self.error_policy)
        items = self.items
        completed = [i for i in items if i.status == "completed"]
        failed = [i for i in items if i.status == "failed"]
        skipped = [i for i in items if i.status == "skipped"]
        timeouts = sum(1 for i in items if i.error and i.error.type == "timeout")
        names: list[str] = list(dict.fromkeys(self.evaluator_names))  # the run's evaluators, even with no score
        for it in items:
            for k in it.scores:
                if k not in names:
                    names.append(k)
        zeros = len(failed) if policy == "zero" else 0  # a failed trial: 0 and a fail in every evaluator's numbers
        evals: dict[str, EvaluatorSummary] = {}
        for name in names:
            got = [it.scores[name] for it in items if name in it.scores]
            assessed = [s for s in got if s.status == "assessed" and (s.value is not None or s.passed is not None)]
            vals = [s.value for s in assessed if s.value is not None]
            judged = [s.passed for s in assessed if s.passed is not None]
            # an evaluator that only ever gives numbers keeps no pass rate; one with no assessed score at all is
            # read as pass/fail, so failed trials counted as fails give it a pass rate of 0
            pass_of = len(judged) + zeros if (judged or not vals) else 0
            evals[name] = EvaluatorSummary(
                name=name,
                n=len(got),
                mean=(sum(vals) / (len(vals) + zeros)) if (vals or zeros) else None,
                pass_rate=(sum(1 for p in judged if p) / pass_of) if pass_of else None,
                errors=sum(1 for s in got if s.status == "error"),
                error_policy=policy,  # type: ignore[arg-type]
                scored=len(assessed),
                failed_trials=len(failed),
            )
        error_score_trials = sum(1 for i in completed if any(s.status == "error" for s in i.scores.values()))
        lat = [i.latency_ms for i in items if i.latency_ms is not None and i.status != "skipped"]
        costs = [i.cost_usd for i in items if i.cost_usd is not None]
        tokens = {"input": 0, "output": 0, "total": 0}
        for i in items:
            for k in tokens:
                tokens[k] += int((i.tokens or {}).get(k, 0))
        errors_by_type = Counter(i.error.type for i in failed + skipped if i.error)
        ran = len(completed) + len(failed)
        return Summary(
            trials=len(items),
            completed=len(completed),
            failed=len(failed),
            skipped=len(skipped),
            timeouts=timeouts,
            error_rate=((len(failed) + error_score_trials) / ran) if ran else 0.0,
            evaluators=evals,
            latency_ms={
                "p50": _percentile(lat, 0.50),
                "p95": _percentile(lat, 0.95),
                "p99": _percentile(lat, 0.99),
            },
            cost_usd=sum(costs) if costs else None,
            tokens=tokens,
            errors_by_type=dict(errors_by_type),
            error_policy=policy,  # type: ignore[arg-type]
            error_scores=sum(ev.errors for ev in evals.values()),
            error_score_trials=error_score_trials,
        )

    # ---- gates ----
    def assert_passing(
        self,
        fail_under: Union[float, Mapping[str, float], None] = None,
        *,
        max_error_rate: Optional[float] = None,
        raise_on_fail: bool = True,
        error_policy: Optional[str] = None,
    ) -> GateResult:
        """Pass rate (or mean, for evaluators without pass/fail) at or above ``fail_under``. A failed trial counts as
        the run's ``error_policy`` says (default ``zero``: 0 and a fail in every evaluator's numbers), or as
        ``error_policy`` here says; an evaluator's error scores are left out of its numbers and count in the error
        rate, which ``max_error_rate`` gates on. An evaluator with no scored rows fails the gate, saying why. Each
        reason prints both counts and how each was counted."""
        s = self.summary(error_policy)
        reasons: list[str] = []
        code = EXIT_OK
        if fail_under is not None:
            wanted = (
                {n: float(fail_under) for n in s.evaluators}
                if not isinstance(fail_under, Mapping)
                else {k: float(v) for k, v in fail_under.items()}
            )
            if not wanted:
                reasons.append("fail_under is set but the run has no evaluator scores")
                code = EXIT_GATE
            for name, threshold in wanted.items():
                ev = s.evaluators.get(name)
                if ev is None:
                    raise UsageError(f"fail_under names {name!r}, which is not an evaluator of this run")
                got = ev.pass_rate if ev.pass_rate is not None else ev.mean
                if not ev.scored:  # a broken evaluator never passes silently
                    reasons.append(f"{name}: no scored rows, so it cannot pass {threshold}: {_no_scored_rows(ev)} "
                                   + counts_note(ev))
                    code = EXIT_GATE
                elif got is None or got < threshold:
                    reasons.append(f"{name}: {shown_number(got, threshold) if got is not None else 'no scores'} < "
                                   f"{threshold} " + counts_note(ev))
                    code = EXIT_GATE
        if code == EXIT_OK and max_error_rate is not None and s.error_rate > max_error_rate:
            reasons.append(f"error rate {s.error_rate:.3f} > {max_error_rate} [failed trials {s.failed}; trials with "
                           f"an error score {s.error_score_trials}; of {s.completed + s.failed} that ran]")
            code = EXIT_CI_ERRORS
        result = GateResult(passed=code == EXIT_OK, reasons=reasons, exit_code=code)
        if raise_on_fail and not result.passed:
            raise AssertionError("; ".join(reasons))
        return result

    @property
    def exit_code(self) -> int:
        """What the CLI returns with no gate flags: 5 under CI=true when any trial errored."""
        if os.environ.get("CI", "").lower() == "true" and self.summary().failed > 0:
            return EXIT_CI_ERRORS
        return EXIT_OK

    # ---- the run's page ----
    def open(self) -> str:
        """Open ``url`` in a browser and return it. Today that page is the run's dataset's Experiments tab, which
        lists SDK runs (and selects this one) only once FE-2 ships. With no ``url`` this raises ``NoRunPageError``
        saying why (``url_note``), and when no browser can be started it raises with the link to open by hand: it
        never reports success it did not have."""
        from fi.experiments.errors import NoRunPageError

        if not self.url:
            raise NoRunPageError(f"run {self.run_id} has no page to open: "
                                 f"{self.url_note or 'no app URL is known for it'}")
        import webbrowser

        try:
            opened = webbrowser.open(self.url)
        except Exception as exc:  # a broken BROWSER setting: say so, with the link
            raise NoRunPageError(f"could not start a browser ({type(exc).__name__}: {exc}); open {self.url}") from exc
        if not opened:
            raise NoRunPageError(f"no browser is available here; open {self.url}")
        return self.url

    # ---- export ----
    def to_jsonl(self, path: Union[str, Path]) -> None:
        import json

        with Path(path).open("w", encoding="utf-8") as fh:
            for it in self.items:
                fh.write(json.dumps(it.model_dump(mode="json"), sort_keys=True) + "\n")

    def to_pandas(self) -> Any:  # pragma: no cover - thin (a pandas.DataFrame; pandas is not imported here)
        import pandas as pd

        return pd.DataFrame([it.model_dump(mode="json") for it in self.items])
