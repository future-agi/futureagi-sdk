"""Engine unit tests: concurrency, timeouts, retries, fail-fast, run budget, run() in a loop."""

import asyncio
import threading
import time

import pytest

from fi import experiments
from fi.experiments import Limits, _engine_pool
from fi.experiments.errors import UnpricedModelError, UsageError

ROWS = [{"id": f"r{i}", "question": f"q{i}", "expected": f"a{i}"} for i in range(1, 7)]


def _run(task, rows=ROWS, **kw):
    kw.setdefault("upload", False)
    kw.setdefault("progress", False)
    return experiments.run(rows, task, **kw)


@pytest.mark.parametrize("limit", [1, 3])
def test_concurrency_bounds_overlap(limit):
    active, peak, lock = [0], [0], threading.Lock()

    async def task(row):
        with lock:
            active[0] += 1
            peak[0] = max(peak[0], active[0])
        await asyncio.sleep(0.05)
        with lock:
            active[0] -= 1
        return row.input

    result = _run(task, concurrency=limit)
    assert len(result.items) == 6 and all(i.status == "completed" for i in result.items)
    assert peak[0] == limit


def test_trials_number_every_row():
    result = _run(lambda row: row.input, trials=3)
    assert sorted((i.example_id, i.trial) for i in result.items) == sorted(
        (f"r{n}", t) for n in range(1, 7) for t in (1, 2, 3)
    )


def test_async_timeout_cancels_and_runs_finally():
    cleaned = []

    async def task(row):
        try:
            await asyncio.sleep(10)
        finally:
            cleaned.append(row.id)

    started = time.monotonic()
    result = _run(task, rows=ROWS[:2], timeout_s=0.2, limits=Limits(fail_fast=0))
    assert time.monotonic() - started < 3
    assert {i.error.type for i in result.items} == {"timeout"}
    assert sorted(cleaned) == ["r1", "r2"]


def test_fail_fast_stops_after_first_n_same_error():
    def task(row):
        raise ValueError("bad key")

    rows = [{"id": f"x{i}", "q": "x"} for i in range(12)]
    result = _run(task, rows=rows, concurrency=1)
    assert result.status == "failed_fast"
    kinds = [i.error.type for i in result.items]
    assert kinds.count("ValueError") == 5 and kinds.count("fail_fast") == 7


def test_fail_fast_off():
    result = _run(lambda row: 1 / 0, rows=ROWS, concurrency=1, limits=Limits(fail_fast=0))
    assert result.status == "no_upload"
    assert all(i.error.type == "ZeroDivisionError" for i in result.items)


class RateLimitError(Exception):
    status_code = 429


def test_transient_retry_then_success(monkeypatch):
    monkeypatch.setattr(_engine_pool, "TRANSIENT_BACKOFF_S", (0.0, 0.0, 0.0))
    calls = {}

    def task(row):
        calls[row.id] = calls.get(row.id, 0) + 1
        if calls[row.id] == 1:
            raise RateLimitError("slow down")
        return "ok"

    result = _run(task, rows=ROWS[:3])
    assert all(i.status == "completed" and i.attempts == 2 for i in result.items)


def test_transient_retries_exhausted(monkeypatch):
    monkeypatch.setattr(_engine_pool, "TRANSIENT_BACKOFF_S", (0.0,))

    def task(row):
        raise RateLimitError("always")

    result = _run(task, rows=ROWS[:1], limits=Limits(transient_retries=2))
    assert result.items[0].error.type == "RateLimitError" and result.items[0].attempts == 3


def test_user_retries():
    seen = {}

    def task(row):
        seen[row.id] = seen.get(row.id, 0) + 1
        if seen[row.id] < 2:
            raise RuntimeError("flaky")
        return "ok"

    result = _run(task, rows=ROWS[:2], limits=Limits(retries=1))
    assert [i.attempts for i in result.items] == [2, 2]


def test_run_inside_running_loop():
    async def main():
        return experiments.run(ROWS[:2], lambda row: row.input, upload=False, progress=False)

    result = asyncio.run(main())
    assert len(result.items) == 2


def test_arun_in_asyncio_run():
    result = asyncio.run(experiments.arun(ROWS[:2], lambda row: row.input, upload=False, progress=False))
    assert [i.output for i in result.items] == ["q1", "q2"]


def _llm_span_task(model="m1"):
    from opentelemetry import trace

    def task(row):
        with trace.get_tracer("test").start_as_current_span(
            "llm",
            attributes={
                "gen_ai.request.model": model,
                "gen_ai.usage.input_tokens": 1000,
                "gen_ai.usage.output_tokens": 1000,
            },
        ):
            return row.input

    return task


def test_run_budget_stops_with_injected_prices():
    result = _run(
        _llm_span_task(),
        concurrency=1,
        max_cost_usd=3.0,
        limits=Limits(prices={"m1": (1000.0, 1000.0)}),
    )
    assert result.status == "stopped_cost"
    done = [i for i in result.items if i.status == "completed"]
    assert len(done) == 2 and all(i.cost_usd == pytest.approx(2.0) for i in done)
    assert all(i.error.type == "cost_cap" for i in result.items if i.status == "skipped")
    assert result.summary().tokens["total"] == 4000


def test_unpriced_model_refused_before_second_trial():
    with pytest.raises(UnpricedModelError) as info:
        _run(_llm_span_task("mystery-model"), max_cost_usd=1.0)
    assert "mystery-model" in str(info.value)


def test_add_cost_counts():
    def task(row, ctx):
        ctx.add_cost(0.25)
        return 1

    result = _run(task, rows=ROWS[:2])
    assert [i.cost_usd for i in result.items] == [0.25, 0.25]


def test_params_reach_ctx_and_param():
    got = []

    def make():
        model = experiments.param("model")

        def task(row, ctx):
            got.append((model, ctx.params["model"]))
            return model

        return task

    result = _run(make, rows=ROWS[:2], params={"model": "m-x"})
    assert got == [("m-x", "m-x"), ("m-x", "m-x")]
    assert result.items[0].output == "m-x"


def test_upload_without_keys_is_refused_clearly():
    from fi._credentials import CredentialsMissingError

    with pytest.raises(CredentialsMissingError) as info:
        experiments.run(experiments.dataset(ROWS, name="t-keys"), lambda row: 1, progress=False)
    assert "upload=False" in str(info.value)


def test_bad_arguments():
    with pytest.raises(UsageError):
        _run(lambda row: 1, trials=0)
    with pytest.raises(UsageError):
        _run(lambda row, ctx, extra: 1)


def test_progress_false_prints_nothing(capsys):
    _run(lambda row: 1, rows=ROWS[:1])
    captured = capsys.readouterr()
    assert captured.err == "" and captured.out == ""


def test_cost_cap_needs_tracing_and_warns_when_nothing_measured(capsys):
    from fi.experiments.errors import CapNotEnforceableError

    with pytest.raises(CapNotEnforceableError):
        _run(lambda row: 1, max_cost_usd=1.0, trace=False)
    experiments.run(ROWS[:2], lambda row: 1, upload=False, max_cost_usd=1.0, concurrency=1)
    assert "showed no token usage" in capsys.readouterr().err
