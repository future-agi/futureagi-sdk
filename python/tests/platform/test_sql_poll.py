"""SQL live-test polling policy, without a backend or real sleeps."""

from types import SimpleNamespace

import pytest
from test_all_operations_live import _poll_sql_result, _run_with_cleanup_preserving_primary


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
