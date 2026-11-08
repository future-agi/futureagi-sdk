"""``experiments.log_results`` / ``futureagi-py upload FILE``: store results made elsewhere as a run
.

Each result names its row by ``example_id`` (or ``id``) or by 1-based ``number``, and may carry
``trial`` (default 1), ``output``, ``error`` (a string or ``{"type", "message"}``), ``latency_ms``,
``cost_usd``, ``trace_id`` / ``root_span_id`` and ``scores`` (``{name: number | bool |
{"value", "passed", "explanation"}}``). The run's plan is exactly the identities in the file. The
rows go through the same pin, metric binding, journal and streaming upload as ``run()``; recorded
scores bind as external metrics, and ``evaluators=`` score the recorded outputs (templates on the
hosted eval API, local functions in process). Nothing is re-executed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from fi.experiments.errors import UsageError
from fi.experiments.evaluators._base import EvalContext, Evaluator, to_score
from fi.experiments.results import EvalScore


class RecordedTrialError(Exception):
    """A trial that failed where it ran; the engine records it as failed with its own type."""

    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message


@dataclass(frozen=True)
class Recorded:
    key: str  # "id:<example or external id>" | "n:<number>"
    trial: int
    output: Any = None
    error: Optional[tuple[str, str]] = None
    latency_ms: Optional[float] = None
    cost_usd: Optional[float] = None
    trace_id: Optional[str] = None
    root_span_id: Optional[str] = None
    scores: Optional[Mapping[str, Any]] = None


def _read(results: Any) -> list[dict]:
    if isinstance(results, (str, Path)):
        path = Path(results)
        if not path.is_file():
            raise UsageError(f"results file {str(path)!r} does not exist")
        out = []
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                try:
                    out.append(json.loads(line))
                except ValueError as exc:
                    raise UsageError(f"{path}:{n} is not valid JSON: {exc}") from exc
        return out
    if isinstance(results, Sequence) and all(isinstance(r, Mapping) for r in results):
        return [dict(r) for r in results]
    raise UsageError("results= takes a results.jsonl path or a list of dicts")


def parse(records: Sequence[Mapping[str, Any]]) -> list[Recorded]:
    out: list[Recorded] = []
    seen: set[tuple[str, int]] = set()
    for i, rec in enumerate(records, 1):
        ref = rec.get("example_id", rec.get("id"))
        if ref not in (None, ""):
            key = f"id:{ref}"
        elif isinstance(rec.get("number"), int) and not isinstance(rec.get("number"), bool):
            key = f"n:{rec['number']}"
        else:
            raise UsageError(f"result {i} names no row: give it example_id (or id) or a 1-based number")
        trial = int(rec.get("trial", rec.get("trial_number", 1)) or 1)
        if (key, trial) in seen:
            raise UsageError(f"result {i} repeats row {key[3:] if key.startswith('id:') else key[2:]} trial {trial}")
        seen.add((key, trial))
        err = rec.get("error")
        error = None
        if err:
            error = (str(err.get("type") or "error"), str(err.get("message") or "")) if isinstance(err, Mapping) else (
                "error", str(err))
        out.append(Recorded(key, trial, rec.get("output"), error, rec.get("latency_ms"),
                            rec.get("cost_usd", rec.get("cost")), rec.get("trace_id"), rec.get("root_span_id"),
                            rec.get("scores")))
    if not out:
        raise UsageError("there are no results to upload")
    return out


# log_results stores results, so it has no local mode: a missing-keys error names none
NO_KEYS_HINT = "log_results / futureagi-py upload store the results on the server, so they need keys."
SERVER_HINT = "Storing results needs a server that has it (there is no local mode for log_results / futureagi-py upload)."


class RecordedTask:
    """The task of a ``log_results`` run: it returns each identity's recorded output."""

    __name__ = "log_results"
    no_keys_hint = NO_KEYS_HINT
    stores_always = True  # no upload=False: a name refusal never offers it

    def __init__(self, recorded: Sequence[Recorded]) -> None:
        self.recorded = list(recorded)
        self._by: dict[tuple[str, int], Recorded] = {}

    def _bind(self, rows: Sequence[Any]) -> None:
        by_key: dict[str, Any] = {}
        for row in rows:
            by_key[f"n:{row.number}"] = row
            by_key[f"id:{row.id}"] = row
            external = (row.to_dict() or {}).get("id") if hasattr(row, "to_dict") else None
            if external not in (None, ""):
                by_key.setdefault(f"id:{external}", row)
        missing = [r.key for r in self.recorded if r.key not in by_key]
        if missing:
            raise UsageError(f"{len(missing)} result(s) name rows the dataset does not have: "
                             f"{', '.join(m.split(':', 1)[1] for m in missing[:5])}")
        self._by = {(by_key[r.key].id, r.trial): r for r in self.recorded}

    def plan_identities(self, rows: Sequence[Any]) -> list[tuple[Any, int]]:
        self._bind(rows)
        order = {row.id: i for i, row in enumerate(rows)}
        rows_by_id = {row.id: row for row in rows}
        return sorted(((rows_by_id[rid], t) for rid, t in self._by), key=lambda it: (order[it[0].id], it[1]))

    def recorded_for(self, example_id: str, trial: int) -> Optional[Recorded]:
        return self._by.get((example_id, trial))

    def __call__(self, row: Any, ctx: Any) -> Any:
        rec = self._by[(row.id, ctx.trial)]
        if rec.error is not None:
            raise RecordedTrialError(*rec.error)
        return rec.output


class RecordedScores(Evaluator):
    """Scores that came with the results; uploaded as external metrics like any local score."""

    kind = "local"

    def __init__(self, task: RecordedTask, names: Sequence[str]) -> None:
        self.task = task
        self.names = tuple(names)

    def evaluate(self, ec: EvalContext) -> dict[str, EvalScore]:
        rec = self.task.recorded_for(ec.row.id, ec.ctx.trial)
        scores = dict((rec.scores if rec else None) or {})
        out: dict[str, EvalScore] = {}
        for name in self.names:
            value = scores.get(name)
            if isinstance(value, Mapping):
                out[name] = EvalScore(value.get("value"), explanation=value.get("explanation"),
                                      passed=value.get("passed"), label=value.get("label"))
            else:
                out[name] = to_score(value)
        return out


def log_results(
    dataset: Any,
    results: Any,
    evaluators: Sequence[Any] = (),
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    experiment: Any = None,
    version: Any = None,
    judge_model: Optional[str] = None,
    params: Optional[Mapping[str, Any]] = None,
    client: Any = None,
    progress: bool = True,
    resume: Any = None,
    **cli: Any,
) -> Any:
    """Store results made elsewhere as a run on ``dataset`` (see the module docstring).
    ``resume=RUN`` sends what a stalled or interrupted upload of the same results did not."""
    from fi.experiments._engine import Engine, RunConfig
    from fi.experiments._sync import run_coroutine_sync
    from fi.experiments.errors import NotSupportedByServerError

    recorded = parse(_read(results))
    task = RecordedTask(recorded)
    score_names = sorted({n for r in recorded for n in (r.scores or {})})
    evs = list(evaluators) + ([RecordedScores(task, score_names)] if score_names else [])
    cfg = RunConfig(dataset=dataset, task=task, evaluators=evs, name=name or "log_results", description=description,
                    metadata=metadata, experiment=experiment, version=version, judge_model=judge_model,
                    params=params, client=client, progress=progress, upload=True, trace=False,
                    timeout_s=None, concurrency=4, resume=resume, **cli)
    try:
        return run_coroutine_sync(lambda: Engine(cfg).execute())
    except NotSupportedByServerError as exc:  # its default hint (upload=False) is a dead end here
        raise NotSupportedByServerError(exc.srv, exc.what, hint=SERVER_HINT) from exc
