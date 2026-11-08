"""``TaskContext``: what a ``task(row, ctx)`` receives."""

from __future__ import annotations

import threading
from typing import Any, Mapping, Optional


class TaskContext:
    """``run_id``, ``example_id``, ``trial``, ``params``, ``cancelled`` (a ``threading.Event``),
    ``span`` (the trial's root span, or None), ``add_cost(usd)``.

    ``timeout_s`` bounds the task's attempts in each trial, including retries, not evaluators.
    Evaluators keep their own limits (such as judge or provider request timeouts); their
    timeouts produce error scores. An evaluator without its own bound may wait indefinitely;
    it does not extend or reuse the task's ``timeout_s``.

    When the runner handles a task timeout, it sets ``ctx.cancelled``, abandons the attempt and
    records a timeout. The concurrency slot is released without waiting for a synchronous task's
    thread to return. Cancellation is cooperative: check ``ctx.cancelled.is_set()`` and stop.
    Threads ignoring the event keep running until they return and can exceed ``concurrency``;
    there is no forced kill. Work a task starts in the default executor can also occupy workers
    until it returns. Async cancellation can be delayed; an async task that suppresses cancellation
    can currently have its late result recorded instead of a timeout, without ``ctx.cancelled``
    being set. This is being fixed.

    The runner also sets the event when handling Ctrl-C cancellation. The cost cap never cancels
    a trial in flight, it only stops new ones.
    """

    __slots__ = ("run_id", "example_id", "trial", "params", "cancelled", "span", "_added_usd", "_lock")

    def __init__(
        self,
        run_id: str,
        example_id: str,
        trial: int,
        params: Mapping[str, Any],
        span: Any = None,
    ) -> None:
        self.run_id = run_id
        self.example_id = example_id
        self.trial = trial
        self.params = params
        self.cancelled = threading.Event()
        self.span = span
        self._added_usd = 0.0
        self._lock = threading.Lock()

    def add_cost(self, usd: float) -> None:
        """Spend that no span shows (a paid API). Counts toward ``max_cost_usd``."""
        if usd < 0:
            raise ValueError("add_cost() takes a non-negative amount")
        with self._lock:
            self._added_usd += float(usd)

    @property
    def added_cost_usd(self) -> float:
        return self._added_usd

    def __repr__(self) -> str:
        return f"TaskContext(run_id={self.run_id!r}, example_id={self.example_id!r}, trial={self.trial})"


def maybe_span_event(span: Optional[Any], name: str, **attrs: Any) -> None:
    if span is not None:
        span.add_event(name, {k: str(v) for k, v in attrs.items()})
