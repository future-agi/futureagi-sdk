"""Offline wait deadlines with the real futures session and bounded executor."""
import json
import threading
import time
from concurrent.futures import Future
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests
from requests_futures.sessions import FuturesSession

from fi.evals.evaluator import Evaluator
from fi.evals.execution import _WAIT_DEADLINE
from fi.utils.executor import BoundedExecutor
from tests.core import _egress


@pytest.fixture
def client(monkeypatch, tmp_path):
    _egress.install(monkeypatch, tmp_path)
    state = SimpleNamespace(calls=[], status="pending")

    def request(session, method, url, **kwargs):
        state.calls.append((method, kwargs))
        response = requests.Response()
        response.status_code = 200
        body = (
            {"status": True, "result": [{"evaluations": [{"eval_id": "exec-1"}]}]}
            if method == "POST" else
            {"status": True, "result": {"eval_status": state.status,
             "result": {"name": "tone", "output": "Passed", "eval_id": "exec-1"}}}
        )
        response._content = json.dumps(body).encode()
        return response

    monkeypatch.setattr(requests.sessions.Session, "request", request)
    evaluator = Evaluator(
        fi_api_key="test-key", fi_secret_key="test-secret",
        fi_base_url="http://127.0.0.1:9", max_workers=1, max_queue=0,
    )
    assert isinstance(evaluator._session, FuturesSession)
    assert isinstance(evaluator._session.executor, BoundedExecutor)
    try:
        yield evaluator, state
    finally:
        evaluator.close()
        _egress.assert_no_attempts()


@pytest.mark.parametrize("factory", ["submit", "get_execution"])
@pytest.mark.parametrize("queue_size", [0, 1])
def test_saturated_executor_does_not_extend_wait(client, factory, queue_size):
    evaluator, state = client
    handle = (evaluator.submit("tone", {"output": "hello"}) if factory == "submit"
              else evaluator.get_execution("exec-1"))
    state.status = "completed"
    state.calls.clear()
    executor = evaluator._session.executor
    if queue_size:
        executor.shutdown()
        executor = BoundedExecutor(bound=queue_size, max_workers=1)
        evaluator._session.executor = executor
    occupied, release = threading.Event(), threading.Event()

    def busy():
        occupied.set()
        assert release.wait(2), "test must release its worker"

    blocker = executor.submit(busy)
    timer = None
    try:
        assert occupied.wait(1)
        # A watchdog makes the regression fail promptly even on the old executor.
        timer = threading.Timer(0.5, release.set)
        timer.start()
        start = time.monotonic()
        with pytest.raises(TimeoutError, match="exec-1"):
            handle.wait(timeout=0.03, poll_interval=0.001)
        elapsed = time.monotonic() - start
        print(json.dumps({"factory": factory, "queue_size": queue_size,
                          "timeout_seconds": 0.03, "elapsed_seconds": elapsed}))
        assert elapsed < 0.25, "executor admission must share the wait budget"
        assert not release.is_set(), "wait must return while the executor is still full"
    finally:
        release.set()
        if timer is not None:
            timer.cancel()
            timer.join(1)
        blocker.result(timeout=1)
        # Drain accepted work before checking that no late HTTP poll was sent.
        executor.submit(lambda: None).result(timeout=1)
    assert state.calls == []
    assert handle.status == "pending"
    # The timed-out context and all semaphore permits must have been restored.
    assert handle.refresh().status == "completed"
    assert state.calls[0][1]["timeout"] == evaluator._default_timeout


def test_capacity_available_before_deadline_allows_poll(client):
    evaluator, state = client
    handle = evaluator.submit("tone", {"output": "hello"})
    state.status = "completed"
    occupied, release = threading.Event(), threading.Event()

    def busy():
        occupied.set()
        assert release.wait(2)

    blocker = evaluator._session.executor.submit(busy)
    timer = threading.Timer(0.03, release.set)
    try:
        assert occupied.wait(1)
        timer.start()
        assert handle.wait(timeout=1, poll_interval=0.001) is handle
        assert handle.status == "completed"
        assert 0 < state.calls[-1][1]["timeout"] <= 1
        assert "deadline" not in state.calls[-1][1]
    finally:
        release.set()
        timer.cancel()
        timer.join(1)
        blocker.result(timeout=1)


@pytest.mark.parametrize("expiry_point", ["before_acquire", "after_acquire", "worker_start"])
def test_expired_poll_never_dispatches_and_releases_capacity(client, monkeypatch, expiry_point):
    evaluator, state = client
    handle = evaluator.submit("tone", {"output": "hello"})
    state.status = "completed"
    state.calls.clear()
    executor = evaluator._session.executor
    now = SimpleNamespace(value=10.0)
    monkeypatch.setattr(time, "monotonic", lambda: now.value)
    real_acquire = executor.semaphore.acquire
    real_request = evaluator._session.request
    real_submit = executor.executor.submit
    acquire = Mock(wraps=real_acquire)
    monkeypatch.setattr(executor.semaphore, "acquire", acquire)

    if expiry_point == "before_acquire":
        def delayed_request(*args, **kwargs):
            now.value = 11.0
            return real_request(*args, **kwargs)
        monkeypatch.setattr(evaluator._session, "request", delayed_request)
    elif expiry_point == "after_acquire":
        def delayed_acquire(*args, **kwargs):
            result = real_acquire(*args, **kwargs)
            now.value = 11.0
            return result
        acquire.side_effect = delayed_acquire
    else:
        def delayed_worker(fn, *args, **kwargs):
            # Model a dequeued, already-running task: Future.cancel cannot save it.
            result = Future()
            assert result.set_running_or_notify_cancel()
            now.value = 11.0
            try:
                result.set_result(fn(*args, **kwargs))
            except BaseException as exc:
                result.set_exception(exc)
            return result
        monkeypatch.setattr(executor.executor, "submit", delayed_worker)

    token = _WAIT_DEADLINE.set(11.0)
    try:
        with pytest.raises(TimeoutError):
            handle.refresh()
    finally:
        _WAIT_DEADLINE.reset(token)
    assert state.calls == [], "expired work must not reach the HTTP transport"
    if expiry_point == "before_acquire":
        acquire.assert_not_called()
    else:
        assert acquire.call_args.kwargs["timeout"] == pytest.approx(1.0)
    monkeypatch.setattr(executor.semaphore, "acquire", real_acquire)
    monkeypatch.setattr(executor.executor, "submit", real_submit)
    monkeypatch.setattr(evaluator._session, "request", real_request)
    assert executor.semaphore.acquire(blocking=False), "permit was leaked on expiry"
    executor.semaphore.release()
    assert handle.refresh().status == "completed"


def test_executor_without_deadline_still_blocks_and_forwards_keywords():
    executor = BoundedExecutor(bound=0, max_workers=1)
    occupied, release, submitting, admitted = (threading.Event() for _ in range(4))
    results, errors = [], []

    def busy():
        occupied.set()
        assert release.wait(2)

    def submit():
        submitting.set()
        try:
            future = executor.submit(lambda **kwargs: kwargs, timeout="value", deadline="value")
            admitted.set()
            results.append(future.result(timeout=1))
        except BaseException as exc:
            errors.append(exc)

    blocker = executor.submit(busy)
    thread = threading.Thread(target=submit)
    try:
        assert occupied.wait(1)
        thread.start()
        assert submitting.wait(1)
        assert not admitted.wait(0.03)
        release.set()
        thread.join(1)
        assert not thread.is_alive()
        assert not errors
        assert results == [{"timeout": "value", "deadline": "value"}]
    finally:
        release.set()
        if thread.ident is not None:
            thread.join(1)
        blocker.result(timeout=1)
        executor.shutdown()


def test_executor_releases_capacity_after_worker_and_submission_errors():
    executor = BoundedExecutor(bound=0, max_workers=1)
    try:
        def fail():
            raise ValueError("synthetic failure")
        with pytest.raises(ValueError, match="synthetic failure"):
            executor.submit(fail).result(timeout=1)
        assert executor.submit(lambda: "ok").result(timeout=1) == "ok"
    finally:
        executor.shutdown()
    with pytest.raises(RuntimeError, match="shutdown"):
        executor.submit(lambda: None)
    assert executor.semaphore.acquire(blocking=False)
    executor.semaphore.release()
