"""Sync entry points over the async engine.

- ``run()`` drives the engine on a private event loop in its own (daemon) thread, so it works
  from plain scripts and from inside a running loop (Jupyter) alike. Ctrl-C in the caller's
  thread cancels the run; the engine flushes the journal and ``RunInterrupted`` is raised.
- ``timeout_s`` bounds the task's attempts in each trial, including retries, not evaluators;
  evaluators keep their own limits and their timeouts produce error scores (``_engine_trial``).
- Sync tasks run on daemon threads. When the runner handles a task timeout, it sets
  ``ctx.cancelled``, abandons the attempt and records a timeout. The concurrency slot is released
  without waiting for the thread to return. Threads ignoring this cooperative stop signal can
  exceed ``concurrency`` until they return; there is no forced kill. Work a task starts in the
  default executor can also occupy workers until it returns. The runner's daemon task threads
  do not block interpreter exit.
- Async cancellation can be delayed; an async task that suppresses cancellation can currently
  have its late result recorded instead of a timeout, without ``ctx.cancelled`` being set.
  This is being fixed.
- ``exit_after_flush(code)`` is for the CLI only: it flushes stdout/stderr and calls
  ``os._exit`` so abandoned threads cannot hold the process.
"""

from __future__ import annotations

import asyncio
import contextvars
import os
import sys
import threading
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")

_abandoned_lock = threading.Lock()
_running_threads = 0


def running_task_threads() -> int:
    with _abandoned_lock:
        return _running_threads


def run_in_daemon_thread(fn: Callable[..., T], *args: Any) -> "asyncio.Future[T]":
    """Run ``fn(*args)`` on a new daemon thread with the caller's context; return a future on the
    current loop."""
    global _running_threads
    loop = asyncio.get_running_loop()
    future: asyncio.Future = loop.create_future()
    ctx = contextvars.copy_context()

    def deliver(ok: bool, value: Any) -> None:
        if future.cancelled():
            return
        if ok:
            future.set_result(value)
        else:
            future.set_exception(value)

    def target() -> None:
        global _running_threads
        try:
            value = ctx.run(fn, *args)
        except BaseException as exc:  # delivered to the awaiting trial
            ok, value = False, exc
        else:
            ok = True
        finally:
            with _abandoned_lock:
                _running_threads -= 1
        try:
            loop.call_soon_threadsafe(deliver, ok, value)
        except RuntimeError:
            pass  # the loop is closed: the trial was abandoned

    with _abandoned_lock:
        _running_threads += 1
    threading.Thread(target=target, name="fi-experiments-task", daemon=True).start()
    return future


def run_coroutine_sync(make: Callable[[], Awaitable[T]]) -> T:
    """Run the coroutine from ``make()`` on a private loop in a daemon thread and wait for it."""
    box: dict[str, Any] = {}
    done = threading.Event()
    ctx = contextvars.copy_context()

    def target() -> None:
        loop = asyncio.new_event_loop()
        box["loop"] = loop
        try:
            task = loop.create_task(make())  # type: ignore[arg-type]
            box["task"] = task
            box["value"] = loop.run_until_complete(task)
        except BaseException as exc:
            box["error"] = exc
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except BaseException:
                pass
            loop.close()
            done.set()

    thread = threading.Thread(target=lambda: ctx.run(target), name="fi-experiments-loop", daemon=True)
    thread.start()
    try:
        while not done.wait(0.05):
            pass
    except KeyboardInterrupt:
        loop, task = box.get("loop"), box.get("task")
        if loop is not None and task is not None:
            try:
                loop.call_soon_threadsafe(task.cancel)
            except RuntimeError:
                pass
        done.wait(60)  # the engine flushes the journal, then raises RunInterrupted
        error = box.get("error")
        if isinstance(error, KeyboardInterrupt):
            raise error from None
        raise
    if "error" in box:
        raise box["error"]
    return box["value"]


def exit_after_flush(code: int) -> None:  # pragma: no cover - exercised by the CLI subprocess tests
    """CLI only: flush and exit now, so abandoned task threads cannot hold the process."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.flush()
        except Exception:
            pass
    os._exit(code)
