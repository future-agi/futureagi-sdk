"""Late task values are never evaluated or journaled as completed trials."""

import asyncio
import json
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from fi import experiments
from fi.experiments import Limits, _engine_pool, _engine_trial

ROWS = [{"id": "late", "input": "question"}]
TIMEOUT_S = 0.05
LATE = "discard this late value"


async def _run(task, evaluated, **kwargs):
    async def score(output):
        evaluated.append(output)
        return True

    kwargs.setdefault("timeout_s", TIMEOUT_S)
    kwargs.setdefault("limits", Limits(retries=0, transient_retries=0, fail_fast=0))
    rows = kwargs.pop("rows", ROWS)
    return await experiments.arun(
        rows, task, evaluators=[score], upload=False, trace=False, progress=False,
        concurrency=1, **kwargs,
    )


def _journal(result):
    records = []
    for line in (Path(result.journal_dir) / "journal.jsonl").read_text().splitlines():
        record = json.loads(line)
        if record["type"] == "item":
            record["item"] = json.loads(record["item"])
            records.append(record)
    return records


def _assert_timeout(item, record, ctx, *, attempts=1, timeout_s=TIMEOUT_S):
    assert item.status == record["status"] == record["item"]["status"] == "failed"
    assert item.error.type == record["item"]["error"]["type"] == "timeout"
    message = f"the trial passed timeout_s={timeout_s}"
    assert item.error.message == record["item"]["error"]["message"] == message
    assert item.output is record["item"]["output"] is None
    assert item.scores == record["item"]["scores"] == {}
    assert item.attempts == record["item"]["attempts"] == attempts
    assert ctx.cancelled.is_set()


def _retry_policy(kind):
    if kind == "transient":
        return ConnectionError, Limits(transient_retries=1, fail_fast=0)
    error = TimeoutError if kind == "timeout-error" else ValueError
    return error, Limits(retries=1, transient_retries=0, fail_fast=0)


@pytest.mark.parametrize("retry_kind", ["none", "user", "transient"])
def test_suppressed_cancellation_is_discarded(monkeypatch, retry_kind):
    # Expected RED before the fix: wait_for returns the cancellation-suppressing value.
    monkeypatch.setattr(_engine_pool, "TRANSIENT_BACKOFF_S", (0.0,))
    error, limits = _retry_policy(retry_kind)
    contexts, evaluated = [], []

    async def task(row, ctx):
        contexts.append(ctx)
        if retry_kind != "none" and len(contexts) == 1:
            raise error("retry before the deadline")
        ctx.add_cost(0.25)
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            return LATE

    result = asyncio.run(_run(task, evaluated, limits=limits))
    records = _journal(result)
    attempts = 1 if retry_kind == "none" else 2
    assert len(result.items) == len(records) == 1
    assert len(contexts) == attempts
    _assert_timeout(result.items[0], records[0], contexts[-1], attempts=attempts)
    assert evaluated == []
    assert result.items[0].cost_usd == records[0]["item"]["cost"] == 0.25


@pytest.mark.parametrize("following_trial", [False, True], ids=["alone", "following-trial"])
def test_sync_late_result_is_discarded(monkeypatch, following_trial):
    # Expected GREEN already: shielding abandons the thread; keep that behavior.
    release = threading.Event()
    contexts, evaluated, futures = [], [], []
    real_thread = _engine_trial.run_in_daemon_thread

    def observe_thread(fn, *args):
        future = real_thread(fn, *args)
        futures.append(future)
        return future

    monkeypatch.setattr(_engine_trial, "run_in_daemon_thread", observe_thread)

    async def scenario():
        started = asyncio.Event()
        loop = asyncio.get_running_loop()

        def task(row, ctx):
            if row.id == "following":
                return "fresh value"
            contexts.append(ctx)
            loop.call_soon_threadsafe(started.set)
            # Ignore ctx.cancelled; only the test releases this abandoned attempt.
            assert release.wait(2), "test did not release the task thread"
            return LATE

        rows = ROWS + ([{"id": "following", "input": "next"}] if following_trial else [])
        pending = asyncio.create_task(_run(task, evaluated, rows=rows, limits=Limits(
            retries=1, transient_retries=1, fail_fast=0,
        )))
        try:
            await asyncio.wait_for(started.wait(), timeout=1)
            result = await pending
            before = _journal(result)
        finally:
            release.set()
            if futures:
                late_value = await asyncio.wait_for(asyncio.shield(futures[0]), timeout=1)
        assert late_value == LATE  # The real thread's value arrived on the still-live loop.
        assert _journal(result) == before
        assert len(result.items) == len(before) == len(rows)
        assert len(contexts) == 1  # A timeout must not start a user or transient retry.
        _assert_timeout(result.items[0], before[0], contexts[0])
        assert evaluated == (["fresh value"] if following_trial else [])
        if following_trial:
            assert result.items[1].status == before[1]["status"] == "completed"
            assert result.items[1].output == before[1]["item"]["output"] == "fresh value"

    asyncio.run(scenario())


@pytest.fixture
def trial_clock(monkeypatch):
    # Only the trial's monotonic reading is controlled, not asyncio's timer or time globally.
    clock = [100.0]
    monkeypatch.setattr(_engine_trial, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    return clock


def _task_kind(kind, finish):
    async def async_task(row, ctx):
        return finish(ctx)

    def sync_task(row, ctx):
        return finish(ctx)

    def sync_awaitable(row, ctx):
        return async_task(row, ctx)

    def factory():
        return async_task

    return {"async": async_task, "sync": sync_task,
            "sync-awaitable": sync_awaitable, "factory": factory}[kind]


@pytest.mark.parametrize("kind", ["async", "sync", "sync-awaitable", "factory"])
@pytest.mark.parametrize("boundary", ["before", "at", "after", "unlimited"])
def test_result_deadline_boundary(trial_clock, kind, boundary):
    # Expected RED for at/after: a value can arrive before the timeout callback runs.
    # Before/unlimited are success controls; the logical clock avoids timing margins.
    contexts, evaluated = [], []
    timeout_s = None if boundary == "unlimited" else 1.0
    offset = {"before": -0.001, "at": 0.0, "after": 0.001, "unlimited": 1.0}[boundary]

    def finish(ctx):
        contexts.append(ctx)
        trial_clock[0] = 101.0 + offset
        return "boundary value"

    result = asyncio.run(_run(_task_kind(kind, finish), evaluated, timeout_s=timeout_s))
    records = _journal(result)
    assert len(result.items) == len(records) == len(contexts) == 1
    item = result.items[0]
    if boundary in ("at", "after"):
        _assert_timeout(item, records[0], contexts[0], timeout_s=timeout_s)
        assert evaluated == []
    else:
        assert item.status == records[0]["status"] == "completed"
        assert item.output == records[0]["item"]["output"] == "boundary value"
        assert item.error is None and item.scores
        assert evaluated == ["boundary value"]
        assert not contexts[0].cancelled.is_set()


@pytest.mark.parametrize("retry_kind", ["user", "transient"])
def test_cancellation_suppression_cannot_start_retry(monkeypatch, retry_kind):
    # Expected RED: a swallowed cancellation followed by an exception starts a new attempt.
    monkeypatch.setattr(_engine_pool, "TRANSIENT_BACKOFF_S", (0.0,))
    error, limits = _retry_policy(retry_kind)
    contexts, evaluated = [], []

    async def task(row, ctx):
        contexts.append(ctx)
        if len(contexts) > 1:
            return "must not rescue the timed-out trial"
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            raise error("the attempt failed after cancellation")

    result = asyncio.run(_run(task, evaluated, limits=limits))
    records = _journal(result)
    assert len(contexts) == len(result.items) == len(records) == 1
    _assert_timeout(result.items[0], records[0], contexts[0])
    assert evaluated == []


@pytest.mark.parametrize("kind", ["async", "sync"])
@pytest.mark.parametrize("retry_kind", ["user", "transient"])
def test_retry_uses_remaining_trial_deadline(monkeypatch, trial_clock, kind, retry_kind):
    # Expected RED: the second attempt's late value is accepted instead of timing out.
    monkeypatch.setattr(_engine_pool, "TRANSIENT_BACKOFF_S", (0.0,))
    error, limits = _retry_policy(retry_kind)
    contexts, evaluated = [], []

    def finish(ctx):
        contexts.append(ctx)
        if len(contexts) == 1:
            trial_clock[0] = 100.75
            raise error("first attempt failed within the budget")
        trial_clock[0] = 101.0  # Within a fresh attempt's budget, but not the trial's.
        return LATE

    result = asyncio.run(_run(_task_kind(kind, finish), evaluated, timeout_s=1.0, limits=limits))
    records = _journal(result)
    assert len(result.items) == len(records) == 1
    assert len(contexts) == 2 and contexts[0] is contexts[1]
    _assert_timeout(result.items[0], records[0], contexts[1], attempts=2, timeout_s=1.0)
    assert evaluated == []


@pytest.mark.parametrize("retry_kind", ["user", "transient", "timeout-error"])
def test_predeadline_retries_still_succeed(monkeypatch, trial_clock, retry_kind):
    # Expected GREEN: ordinary retries (even a user TimeoutError) keep their semantics.
    monkeypatch.setattr(_engine_pool, "TRANSIENT_BACKOFF_S", (0.0,))
    error, limits = _retry_policy(retry_kind)
    contexts, evaluated = [], []

    async def task(row, ctx):
        contexts.append(ctx)
        if len(contexts) == 1:
            trial_clock[0] = 100.25
            raise error("retry me")
        trial_clock[0] = 100.999
        return "on time"

    result = asyncio.run(_run(task, evaluated, timeout_s=1.0, limits=limits))
    records = _journal(result)
    assert len(result.items) == len(records) == 1
    item = result.items[0]
    assert item.status == records[0]["status"] == "completed"
    assert item.attempts == records[0]["item"]["attempts"] == 2
    assert item.output == records[0]["item"]["output"] == "on time"
    assert item.error is None and item.scores
    assert evaluated == ["on time"]
    assert len(contexts) == 2 and contexts[0] is contexts[1]
    assert not contexts[0].cancelled.is_set()
