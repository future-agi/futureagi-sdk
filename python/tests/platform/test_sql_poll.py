"""SQL live-test polling policy, without a backend or real sleeps."""

import asyncio
from types import SimpleNamespace

import pytest
from test_all_operations_live import (
    _cancel_sql_job_bounded_async,
    _poll_sql_result,
    _poll_sql_result_async,
    _run_async_with_cleanup_preserving_primary,
    _run_with_cleanup_preserving_primary,
)


@pytest.mark.parametrize("terminal", ["succeeded", "failed", "cancelled", None])
def test_sql_poll_waits_for_known_terminal_state_or_deadline(terminal):
    now = 0.0

    def sleep(seconds):
        nonlocal now
        now += seconds

    def get_result(job_id, *, project_id, offset, limit, options):
        assert 0 < options.timeout <= 150 - now and options.max_retries == 0
        state = "queued" if now < 89 else "running"
        if now >= 126:
            state = "finishing"  # future state, not necessarily terminal
        if terminal and now >= 133:
            state = terminal
        return SimpleNamespace(id=job_id, project_id=project_id, state=state)

    def poll():
        return _poll_sql_result(get_result, "job", "project", clock=lambda: now, sleep=sleep)

    if terminal is None:
        with pytest.raises(AssertionError, match="150s: finishing"):
            poll()
        assert now == 150
    else:
        assert poll().state == terminal
        assert now == 133


def test_async_sql_poll_charges_transport_time_before_bounded_sleep():
    clock = [0.0]
    sleeps = []
    calls = []

    class FakeTransport:
        class SQL:
            async def get_result(self, job_id, *, project_id, offset, limit, options):
                calls.append(options)
                assert options.timeout == 150.0 - clock[0]
                assert options.timeout > 0 and options.max_retries == 0
                clock[0] = 149.75
                return SimpleNamespace(id=job_id, project_id=project_id, state="queued")

        sql = SQL()

    async def sleep(seconds):
        sleeps.append(seconds)
        clock[0] += seconds

    with pytest.raises(AssertionError, match="150s: queued"):
        asyncio.run(
            _poll_sql_result_async(
                FakeTransport(),
                "job",
                "project",
                clock=lambda: clock[0],
                sleep=sleep,
            )
        )

    assert len(calls) == 1
    assert sleeps == [0.25]
    assert clock[0] == 150.0


def test_sql_cleanup_failure_is_reported_without_masking_primary_failure():
    def work():
        raise ValueError("primary assertion")

    def cleanup():
        raise RuntimeError("cleanup transport")

    with pytest.warns(RuntimeWarning, match="RuntimeError"):
        with pytest.raises(ValueError, match="primary assertion"):
            _run_with_cleanup_preserving_primary(work, cleanup)


def test_sql_cleanup_failure_is_raised_when_the_work_succeeds():
    def cleanup():
        raise RuntimeError("cleanup transport")

    with pytest.raises(RuntimeError, match="cleanup transport"):
        _run_with_cleanup_preserving_primary(lambda: "ok", cleanup)


def test_async_sql_cleanup_transport_failure_does_not_mask_primary_failure():
    calls = []

    class FakeTransport:
        class SQL:
            async def cancel(self, job_id, *, project_id, options):
                calls.append(options)
                raise RuntimeError("cleanup transport")

        sql = SQL()

    async def work():
        raise ValueError("primary assertion")

    async def cleanup():
        await _cancel_sql_job_bounded_async(
            FakeTransport(),
            "job",
            "project",
            clock=lambda: 0.0,
        )

    with pytest.warns(RuntimeWarning, match="RuntimeError"):
        with pytest.raises(ValueError, match="primary assertion"):
            asyncio.run(_run_async_with_cleanup_preserving_primary(work, cleanup))
    assert calls and calls[0].timeout > 0 and calls[0].max_retries == 0


def test_async_sql_cleanup_failure_is_raised_when_the_work_succeeds():
    async def cleanup():
        raise RuntimeError("cleanup transport")

    with pytest.raises(RuntimeError, match="cleanup transport"):
        asyncio.run(_run_async_with_cleanup_preserving_primary(lambda: _async_ok(), cleanup))


async def _async_ok():
    return "ok"
