"""SQL live-test polling policy, without a backend or real sleeps."""

from types import SimpleNamespace

import pytest
from test_all_operations_live import _poll_sql_result


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
