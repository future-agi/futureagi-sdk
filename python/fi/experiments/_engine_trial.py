"""One trial: its task attempts, evaluator scores, fail-fast bookkeeping, and journaled record
(journaled first, then queued for upload).

``timeout_s`` bounds the task's attempts in each trial, including transient and user retries
and their delays. Evaluators run outside that bound, with their own limits (judge or provider
request timeouts). An evaluator timeout produces an error score; an evaluator without its own
bound may wait indefinitely. Evaluators do not extend or reuse the task's ``timeout_s``.

When the runner handles a task timeout, it sets ``ctx.cancelled``, abandons the attempt and
records a timeout. The concurrency slot is released without waiting for a synchronous task's
thread to return. Threads ignoring this cooperative stop signal can exceed ``concurrency``;
there is no forced kill. Work a task starts in the default executor can also occupy workers
until it returns. Async cancellation can be delayed; an async task that suppresses cancellation
can currently have its late result recorded instead of a timeout, without ``ctx.cancelled``
being set. This is being fixed.

Split out of ``_engine.py`` (the 400-line module rule). ``TrialMixin`` is mixed into ``Engine``.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import time
import traceback
from typing import Any, Optional, Sequence

from fi.experiments import _debug, _engine_pool, _params, _provider_errors
from fi.experiments._context import TaskContext, maybe_span_event
from fi.experiments._cost import Usage, priced_usd, usage_from_spans
from fi.experiments._dataset import Row
from fi.experiments._engine_config import FromColumn, _text
from fi.experiments._engine_pool import _Shared
from fi.experiments._journal import JournalRecord
from fi.experiments._plan import canonical_bytes, receipt_key, to_jsonable
from fi.experiments._sync import run_in_daemon_thread
from fi.experiments.adapters import TaskRunner
from fi.experiments.adapters.callable import FactoryRunner
from fi.experiments.evaluators._base import EvalContext, Evaluator, error_score
from fi.experiments.results import EvalScore, TrialError, TrialResult


class TrialMixin:
    """``Engine``'s per-trial methods."""

    async def _run_trial(self, row, trial, runner, evaluators, budget, journal, tracing, run_id, shared):
        ctx = TaskContext(run_id, row.id, trial, self.params)
        holder = {"attempts": 0}
        started = time.monotonic()
        output: Any = None
        error: Optional[TrialError] = None
        token = _params.bind(self.params)
        try:
            with tracing.trial(row.id, trial) as tt:
                ctx.span = tt.span
                try:
                    deadline = None if self.cfg.timeout_s is None else time.monotonic() + self.cfg.timeout_s
                    coro = self._attempts(row, ctx, runner, holder, deadline)
                    if self.cfg.timeout_s is None:
                        output, error = await coro
                    else:
                        output, error = await asyncio.wait_for(coro, timeout=self.cfg.timeout_s)
                    _check_deadline(deadline)
                except asyncio.TimeoutError:
                    ctx.cancelled.set()
                    output = None
                    error = TrialError(type="timeout", message=f"the trial passed timeout_s={self.cfg.timeout_s}")
                except asyncio.CancelledError:  # Ctrl-C: a sync task on its thread can stop cooperatively
                    ctx.cancelled.set()
                    raise
                try:
                    tt.set_io(self.redactor.text(_safe_text(row.inputs)), None if error else self.redactor.text(_safe_text(output)))
                except Exception:
                    pass
                if error is not None:
                    tt.record_error(RuntimeError(f"{error.type}: {error.message}"))
        finally:
            _params.unbind(token)
        latency_ms = (time.monotonic() - started) * 1000.0
        if getattr(tt, "capture", None) is not None:
            self._note_capture(tt.capture)
        usage = usage_from_spans([*tt.spans, *getattr(tt.spans, "usage_only", ())])  # past the capture limits too
        usage.added_usd = ctx.added_cost_usd
        cost, unpriced = budget.record(usage)
        recorded_for = getattr(self.cfg.task, "recorded_for", None)  # log_results: what was measured there
        rec = recorded_for(row.id, trial) if callable(recorded_for) else None
        if rec is not None:
            latency_ms = rec.latency_ms if rec.latency_ms is not None else None
            cost = rec.cost_usd
            if rec.trace_id:
                tt = _RecordedTrace(rec.trace_id, rec.root_span_id, tt)
        status = "completed" if error is None else "failed"
        scores: dict[str, EvalScore] = {}
        if status == "completed" and evaluators:
            starter = getattr(tracing, "child_starter", None)
            ec = EvalContext(row=row, output=output, ctx=ctx, trace=tt.spans if tt.captured else None,
                             tool_spans_expected=self.tool_spans_expected, instrument_hint=self.instrument_hint,
                             start_span=starter(tt) if callable(starter) and getattr(tt, "span", None) else None,
                             price=lambda m, i, o: priced_usd(_one_call(m, i, o), budget.prices)[0],
                             output_column=self.cfg.task.column if isinstance(self.cfg.task, FromColumn) else None)
            scores = await self._evaluate(evaluators, ec)
            if ec.usage:  # judge() calls: they count toward max_cost_usd, apart from the task's cost
                eval_usage = Usage()
                for model, tin, tout in ec.usage:
                    eval_usage.add(model, tin, tout)
                _, eval_unpriced = budget.record(eval_usage, evaluator=True)
                unpriced = list(unpriced) + [m for m in eval_unpriced if m not in unpriced]
        self._record(row, trial, run_id, journal, status=status, output=output, error=error,
                     latency_ms=latency_ms, usage=usage, cost=cost, trace=tt, scores=scores,
                     attempts=holder["attempts"])
        _debug.trial(row.id, trial, status, latency_ms, holder["attempts"], error, scores)  # --verbose
        self._fail_fast(shared, status, error)
        return unpriced

    async def _attempts(self, row: Row, ctx: TaskContext, runner: TaskRunner, holder: dict,
                        deadline: Optional[float] = None):
        user_left = self.limits.retries
        transient_used = 0
        while True:
            _check_deadline(deadline)
            holder["attempts"] += 1
            try:
                output = await self._call(row, ctx, runner)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                _check_deadline(deadline)
                recorded_type = getattr(exc, "error_type", None)
                if recorded_type is not None and type(exc).__name__ == "RecordedTrialError":
                    return None, TrialError(type=recorded_type, message=self.redactor.text(str(exc))[:4000])
                info = _engine_pool.transient_info(exc)
                if info.transient and transient_used < self.limits.transient_retries:
                    if info.rate_limited:
                        self.limiter.on_rate_limited()
                    backoff = _engine_pool.TRANSIENT_BACKOFF_S
                    delay = info.retry_after if info.retry_after is not None else backoff[
                        min(transient_used, len(backoff) - 1)]
                    transient_used += 1
                    maybe_span_event(ctx.span, "fi.retry.transient", error=type(exc).__name__, delay_s=delay)
                    await asyncio.sleep(delay)
                    continue
                if user_left > 0:
                    user_left -= 1
                    maybe_span_event(ctx.span, "fi.retry", error=type(exc).__name__)
                    continue
                tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                message = str(exc)
                retired = _provider_errors.from_exception(exc)
                if retired is not None:  # name the model and say the provider retired it
                    message = f"{_provider_errors.describe(retired)} {message}"
                return None, TrialError(type=type(exc).__name__, message=self.redactor.text(message)[:4000],
                                        traceback=self.redactor.text(tb)[-8000:])
            else:
                _check_deadline(deadline)
                return output, None

    async def _call(self, row: Row, ctx: TaskContext, runner: TaskRunner) -> Any:
        if isinstance(runner, FactoryRunner):
            runner = await run_in_daemon_thread(runner.product)
            if runner.needs_single_input:
                row.input  # raises AmbiguousInputError for several input columns
        if runner.is_async:
            return await runner.acall(row, ctx)
        result = await asyncio.shield(run_in_daemon_thread(runner.call, row, ctx))
        if inspect.isawaitable(result):
            result = await result
        return result

    async def _evaluate(self, evaluators: Sequence[Evaluator], ec: EvalContext) -> dict[str, EvalScore]:
        scores: dict[str, EvalScore] = {}
        for ev in evaluators:
            try:
                if ev.is_async:
                    got = await ev.aevaluate(ec)
                elif ev.kind == "local":
                    got = await run_in_daemon_thread(ev.evaluate, ec)
                else:
                    got = ev.evaluate(ec)
            except Exception as exc:  # an evaluator never crashes the run
                got = {n: error_score(exc) for n in ev.names}
            for n in ev.names:
                scores[n] = got.get(n) or EvalScore(status="error", explanation="the evaluator returned no score")
        return scores

    def _note_capture(self, stats: Any) -> None:
        """A trial whose span capture hit a limit: counted for the run summary (never silent, F7)."""
        t = self.capture_limited
        if not t:
            t.update(trials=0, dropped_spans=0, truncated_values=0, usage_spans_lost=0, max_spans=stats.max_spans,
                     max_bytes=stats.max_bytes, max_value_bytes=stats.max_value_bytes)
        t["trials"] += 1
        t["dropped_spans"] += stats.dropped
        t["truncated_values"] += stats.truncated_values
        t["usage_spans_lost"] += stats.usage_lost

    def _fail_fast(self, shared: _Shared, status: str, error: Optional[TrialError]) -> None:
        n = self.limits.fail_fast
        if not n or shared.stop_reason:
            return
        if len(shared.outcomes) < n:
            shared.outcomes.append((status, error.type if error else None))
            if status != "completed" and shared.first_traceback is None and error is not None:
                shared.first_traceback = error.traceback or f"{error.type}: {error.message}"
            if len(shared.outcomes) == n:
                kinds = {k for s, k in shared.outcomes if s != "completed"}
                if all(s != "completed" for s, _ in shared.outcomes) and len(kinds) == 1:
                    shared.stop_reason = "failed_fast"

    def _record(self, row, trial, run_id, journal, *, status, output, error, latency_ms, usage, cost, trace,
                scores, attempts) -> None:
        item = {
            "example_id": row.id,
            "number": row.number,
            "trial_number": trial,
            "status": status,
            "output": self.redactor.value(to_jsonable(output), by_key=False) if status == "completed" else None,
            "error": error.model_dump(exclude_none=True) if error else None,
            "latency_ms": round(latency_ms, 3) if latency_ms is not None else None,
            "token_usage": usage.to_json() if usage is not None and usage.total_tokens else None,
            "cost": round(cost, 8) if cost is not None else None,
            "trace_id": getattr(trace, "trace_id", None),
            "root_span_id": getattr(trace, "root_span_id", None),
            "attempts": attempts,
            "scores": {k: v.model_dump(exclude_none=True) for k, v in scores.items()},
        }
        data = canonical_bytes(item)
        receipt = receipt_key(run_id, row.id, trial, data)
        journal.append(JournalRecord(row.id, trial, status, receipt, data))  # journaled before it is sent
        self.results[(row.id, trial)] = _result_from_item(json.loads(data), receipt)
        if getattr(self, "uploader", None) is not None:
            self.uploader.submit(receipt, data)


class _RecordedTrace:
    """The trace a logged result already points at (its own trace id), with the trial's captured spans."""

    def __init__(self, trace_id: str, root_span_id: Optional[str], inner: Any) -> None:
        self.trace_id = trace_id
        self.root_span_id = root_span_id
        self.spans = getattr(inner, "spans", [])
        self.captured = getattr(inner, "captured", False)


def _check_deadline(deadline: Optional[float]) -> None:
    if deadline is not None and time.monotonic() >= deadline:
        raise asyncio.TimeoutError


def _one_call(model: str, input_tokens: int, output_tokens: int) -> Usage:
    usage = Usage()
    usage.add(model, input_tokens, output_tokens)
    return usage


def _safe_text(value: Any) -> str:
    try:
        return _text(value)
    except Exception:
        return repr(value)


def _result_from_item(item: dict, receipt: str) -> TrialResult:
    err = item.get("error")
    return TrialResult(
        example_id=str(item["example_id"]),
        number=int(item.get("number") or 0),
        trial=int(item.get("trial_number", 1)),
        status=item["status"],
        output=item.get("output"),
        error=TrialError(**err) if err else None,
        latency_ms=item.get("latency_ms"),
        cost_usd=item.get("cost"),
        tokens=item.get("token_usage"),
        trace_id=item.get("trace_id"),
        root_span_id=item.get("root_span_id"),
        attempts=int(item.get("attempts") or 0),
        scores={k: EvalScore(**v) for k, v in (item.get("scores") or {}).items()},
        receipt_key=receipt,
    )
