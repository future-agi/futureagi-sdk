"""Tests for lazy worker initialization in _TaskManager."""

import threading
import time

import pytest

from fi.prompt.cache import _TaskManager


class TestLazyWorkerInit:
    def test_no_workers_at_init(self):
        tm = _TaskManager(num_workers=2)
        assert tm._workers == []
        assert tm._started is False

    def test_workers_start_on_first_submit(self):
        tm = _TaskManager(num_workers=2)
        done = threading.Event()
        tm.submit(done.set)
        assert done.wait(timeout=3), "task never executed"
        assert len(tm._workers) == 2
        assert tm._started is True
        tm._shutdown()

    def test_ensure_started_is_idempotent(self):
        tm = _TaskManager(num_workers=2)
        tm._ensure_started()
        tm._ensure_started()
        tm._ensure_started()
        assert len(tm._workers) == 2
        tm._shutdown()

    def test_shutdown_safe_before_any_submit(self):
        tm = _TaskManager(num_workers=2)
        # _shutdown must not raise even when workers were never started
        tm._shutdown()
        assert tm._workers == []
