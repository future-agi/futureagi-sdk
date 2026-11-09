"""Offline deadline regressions for execution handles and evaluator polling."""
from concurrent.futures import TimeoutError as FutureTimeoutError
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from requests import ConnectionError, Response

from fi.evals.evaluator import Evaluator
from fi.evals.execution import Execution, ExecutionError
from tests.core import _egress


@pytest.fixture(autouse=True)
def no_egress(monkeypatch, tmp_path):
    _egress.install(monkeypatch, tmp_path)
    yield
    _egress.assert_no_attempts()


@pytest.fixture
def clock(monkeypatch):
    # Both modules use the same time module; no real sleep or network is needed.
    import time

    state = SimpleNamespace(now=100.0, sleeps=[])

    def sleep(seconds):
        assert seconds >= 0
        state.sleeps.append(seconds)
        state.now += seconds

    monkeypatch.setattr(time, "monotonic", lambda: state.now)
    monkeypatch.setattr(time, "sleep", sleep)
    return state


def terminal(status="completed"):
    return Execution("exec-1", "eval", status=status, result="score", error_message="failed")


@pytest.mark.parametrize("timeout", [0, -1, 0.01])
def test_expired_wait_never_polls_or_oversleeps(clock, timeout):
    refresh = Mock(return_value=terminal())
    handle = Execution("exec-1", "eval", _refresher=refresh)

    with pytest.raises(TimeoutError, match="exec-1"):
        handle.wait(timeout=timeout, poll_interval=1)

    refresh.assert_not_called()
    assert sum(clock.sleeps) == pytest.approx(max(timeout, 0))
    assert handle.status == "pending"


def test_overslept_deadline_does_not_start_a_poll(clock, monkeypatch):
    import time

    def oversleep(seconds):
        clock.now += seconds + 2

    monkeypatch.setattr(time, "sleep", oversleep)
    refresh = Mock(return_value=terminal())
    handle = Execution("exec-1", "eval", _refresher=refresh)
    with pytest.raises(TimeoutError):
        handle.wait(timeout=1, poll_interval=0.1)
    refresh.assert_not_called()


@pytest.mark.parametrize("status", ["completed", "failed", "pending"])
@pytest.mark.parametrize("elapsed", [0.75, 1.0])
def test_poll_finishing_at_or_after_deadline_times_out(clock, status, elapsed):
    def refresh():
        clock.now += elapsed
        return terminal(status)

    handle = Execution("exec-1", "eval", _refresher=refresh)
    with pytest.raises(TimeoutError, match="exec-1"):
        handle.wait(timeout=1, poll_interval=0.25)


def test_completed_poll_before_deadline_returns_same_handle(clock):
    handle = Execution("exec-1", "eval", _refresher=lambda: terminal())
    assert handle.wait(timeout=1, poll_interval=0.25) is handle
    assert handle.result == "score"


@pytest.mark.parametrize("raise_on_failure", [True, False])
def test_failure_before_deadline_keeps_failure_policy(clock, raise_on_failure):
    handle = Execution("exec-1", "eval", _refresher=lambda: terminal("failed"))
    if raise_on_failure:
        with pytest.raises(ExecutionError):
            handle.wait(timeout=1, poll_interval=0.25)
    else:
        assert handle.wait(timeout=1, poll_interval=0.25, raise_on_failure=False) is handle


@pytest.mark.parametrize("status", ["completed", "failed"])
def test_already_terminal_handle_does_not_wait(clock, status):
    handle = terminal(status)
    assert handle.wait(timeout=0, raise_on_failure=False) is handle
    assert clock.sleeps == []
    if status == "failed":
        with pytest.raises(ExecutionError):
            handle.wait(timeout=0)


class ScriptedFuture:
    def __init__(self, clock, response, elapsed=0, error=None):
        self.clock = clock
        self.response = response
        self.elapsed = elapsed
        self.error = error
        self.waits = []
        self.cancel = Mock(return_value=False)

    def result(self, timeout=None):
        self.waits.append(timeout)
        if timeout is not None and self.elapsed > timeout:
            self.clock.now += timeout
            raise FutureTimeoutError()
        self.clock.now += self.elapsed
        if self.error:
            raise self.error
        return self.response


def poll_response(status="completed", execution_id="exec-1"):
    response = Mock(spec=Response)
    response.status_code = 200
    response.json.return_value = {
        "status": True,
        "result": {
            "eval_status": status,
            "result": {"name": "tone", "output": "Passed", "eval_id": execution_id},
        },
    }
    return response


def submitted_response(ids):
    response = Mock(spec=Response)
    response.status_code = 200
    response.json.return_value = {
        "status": True,
        "result": [{"evaluations": [{"eval_id": value} for value in ids]}],
    }
    return response


def evaluator_with_futures(futures, timeout=200):
    client = object.__new__(Evaluator)
    client._base_url = "http://127.0.0.1:9"
    client._default_headers = {"X-Api-Key": "test-key", "X-Secret-Key": "test-secret"}
    client._default_timeout = timeout
    client._session = Mock()
    client._session.request.side_effect = futures
    return client


@pytest.mark.parametrize("factory", ["submit", "get_execution"])
@pytest.mark.parametrize("client_timeout", [200, 0.1])
def test_wait_caps_http_and_future_timeouts(clock, factory, client_timeout):
    initial = submitted_response(["exec-1"]) if factory == "submit" else poll_response("pending")
    fetched = ScriptedFuture(clock, poll_response())
    client = evaluator_with_futures([ScriptedFuture(clock, initial), fetched], client_timeout)
    handle = client.submit("tone", {"output": "hello"}) if factory == "submit" else client.get_execution("exec-1")

    assert handle.wait(timeout=1, poll_interval=0.25) is handle

    calls = client._session.request.call_args_list
    assert calls[0].kwargs["timeout"] == client_timeout
    assert calls[1].kwargs["timeout"] == pytest.approx(min(client_timeout, 0.75))
    assert fetched.waits == [pytest.approx(0.75)]
    assert calls[1].kwargs["headers"] == client._default_headers
    assert calls[1].kwargs["params"] == {"eval_id": "exec-1"}


def test_wait_bounds_stalled_future_and_attempts_cancellation(clock):
    fetched = ScriptedFuture(clock, poll_response(), elapsed=200)
    client = evaluator_with_futures([ScriptedFuture(clock, poll_response("pending")), fetched])
    handle = client.get_execution("exec-1")

    with pytest.raises(TimeoutError, match="exec-1"):
        handle.wait(timeout=1, poll_interval=0.25)

    assert clock.now == pytest.approx(101)
    assert client._session.request.call_count == 2
    fetched.cancel.assert_called_once_with()


def test_retry_backoff_cannot_start_poll_after_deadline(clock):
    failed = ScriptedFuture(clock, None, error=ConnectionError("synthetic disconnect"))
    client = evaluator_with_futures([
        ScriptedFuture(clock, poll_response("pending")), failed,
        ScriptedFuture(clock, poll_response()),
    ])
    handle = client.get_execution("exec-1")

    with pytest.raises(TimeoutError):
        handle.wait(timeout=0.5, poll_interval=0.1)

    assert clock.now == pytest.approx(100.5)
    assert client._session.request.call_count == 2
    assert clock.sleeps == pytest.approx([0.1, 0.4])


def test_retry_recomputes_remaining_budget(clock):
    failed = ScriptedFuture(clock, None, elapsed=0.25, error=ConnectionError("synthetic disconnect"))
    retried = ScriptedFuture(clock, poll_response())
    client = evaluator_with_futures([ScriptedFuture(clock, poll_response("pending")), failed, retried])
    handle = client.get_execution("exec-1")

    assert handle.wait(timeout=3, poll_interval=0.25) is handle

    calls = client._session.request.call_args_list
    assert calls[1].kwargs["timeout"] == pytest.approx(2.75)
    assert calls[2].kwargs["timeout"] == pytest.approx(1.5)
    assert failed.waits == [pytest.approx(2.75)]
    assert retried.waits == [pytest.approx(1.5)]


def test_retry_exhaustion_preserves_transport_exception_before_deadline(clock):
    error = ConnectionError("synthetic disconnect")
    client = evaluator_with_futures([
        ScriptedFuture(clock, poll_response("pending")),
        *(ScriptedFuture(clock, None, error=error) for _ in range(3)),
    ])
    handle = client.get_execution("exec-1")
    with pytest.raises(ConnectionError, match="synthetic disconnect"):
        handle.wait(timeout=10, poll_interval=0.25)
    assert client._session.request.call_count == 4
    assert clock.sleeps == [0.25, 1, 1]


def test_manual_refresh_restores_default_timeout_and_retry_policy(clock):
    client = evaluator_with_futures([
        ScriptedFuture(clock, poll_response("pending")),
        ScriptedFuture(clock, poll_response()),
        ScriptedFuture(clock, None, error=ConnectionError("synthetic disconnect")),
        ScriptedFuture(clock, poll_response()),
    ])
    handle = client.get_execution("exec-1")
    handle.wait(timeout=1, poll_interval=0.25)
    assert handle.refresh() is handle
    assert [call.kwargs["timeout"] for call in client._session.request.call_args_list] == [200, 0.75, 200, 200]
    assert clock.sleeps == [0.25, 1]


def test_timed_out_wait_does_not_leak_budget_to_next_refresh(clock):
    client = evaluator_with_futures([
        ScriptedFuture(clock, poll_response("pending")),
        ScriptedFuture(clock, poll_response(), elapsed=200),
        ScriptedFuture(clock, poll_response()),
    ])
    handle = client.get_execution("exec-1")
    with pytest.raises(TimeoutError):
        handle.wait(timeout=1, poll_interval=0.25)
    assert handle.refresh() is handle
    assert client._session.request.call_args.kwargs["timeout"] == 200


def test_batch_polls_share_one_deadline(clock):
    first = ScriptedFuture(clock, poll_response(execution_id="exec-1"), elapsed=0.25)
    second = ScriptedFuture(clock, poll_response(execution_id="exec-2"), elapsed=200)
    client = evaluator_with_futures([
        ScriptedFuture(clock, submitted_response(["exec-1", "exec-2"])), first, second,
    ])
    handle = client.submit("tone", {"output": ["hello", "goodbye"]}, batch=True)

    with pytest.raises(TimeoutError):
        handle.wait(timeout=1, poll_interval=0.25)

    assert first.waits == [pytest.approx(0.75)]
    assert second.waits == [pytest.approx(0.5)]
    assert clock.now == pytest.approx(101)


def test_batch_does_not_dispatch_next_poll_at_deadline(clock):
    client = evaluator_with_futures([
        ScriptedFuture(clock, submitted_response(["exec-1", "exec-2"])),
        ScriptedFuture(clock, poll_response(execution_id="exec-1"), elapsed=0.75),
        ScriptedFuture(clock, poll_response(execution_id="exec-2")),
    ])
    handle = client.submit("tone", {"output": ["hello", "goodbye"]}, batch=True)

    with pytest.raises(TimeoutError):
        handle.wait(timeout=1, poll_interval=0.25)

    assert client._session.request.call_count == 2
