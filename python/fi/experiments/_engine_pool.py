"""The trial pool: transient-error detection, the adaptive concurrency limiter, the run's shared
state, and running every planned trial under the limit with the cost gate and the fail-fast skips.

Split out of ``_engine.py`` (the 400-line module rule). ``PoolMixin`` is mixed into ``Engine``.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Optional

from fi.experiments._dataset import Row
from fi.experiments._journal import Journal
from fi.experiments.errors import UnpricedModelError
from fi.experiments.results import TrialError

TRANSIENT_BACKOFF_S: tuple[float, ...] = (2.0, 4.0, 8.0)
RECOVER_EVERY_S = 30.0
_TRANSIENT_NAMES = {
    "APIConnectionError",
    "APITimeoutError",
    "ConnectError",
    "ConnectTimeout",
    "ReadTimeout",
    "RemoteProtocolError",
    "ServiceUnavailableError",
    "InternalServerError",
    "OverloadedError",
}


# ---- transient errors and the adaptive limiter ------------------------------------------------


@dataclass
class TransientInfo:
    transient: bool
    rate_limited: bool
    retry_after: Optional[float]


def transient_info(exc: BaseException) -> TransientInfo:
    status = None
    response = getattr(exc, "response", None)
    for obj in (exc, response):
        if obj is None:
            continue
        for attr in ("status_code", "status", "http_status"):
            value = getattr(obj, attr, None)
            if isinstance(value, int) and not isinstance(value, bool):
                status = value
                break
        if status is not None:
            break
    name = type(exc).__name__
    rate = status == 429 or "RateLimit" in name
    transient = (
        rate
        or (status is not None and 500 <= status < 600)
        or isinstance(exc, ConnectionError)
        or name in _TRANSIENT_NAMES
    )
    retry_after = None
    headers = getattr(response, "headers", None)
    if headers is not None:
        try:
            raw = headers.get("retry-after") or headers.get("Retry-After")
            retry_after = float(raw) if raw is not None else None
        except (TypeError, ValueError):
            retry_after = None
    return TransientInfo(transient, rate, retry_after)


class AdaptiveLimiter:
    """At most ``limit`` trials in flight; halves on a 429, recovers by one every 30 s."""

    def __init__(self, maximum: int) -> None:
        self.maximum = maximum
        self.limit = maximum
        self.active = 0
        self.peak = 0
        self._cond = asyncio.Condition()
        self._changed = time.monotonic()

    def _recover(self) -> None:
        now = time.monotonic()
        if self.limit < self.maximum and now - self._changed >= RECOVER_EVERY_S:
            self.limit += 1
            self._changed = now

    async def acquire(self) -> None:
        async with self._cond:
            while True:
                self._recover()
                if self.active < self.limit:
                    break
                try:
                    await asyncio.wait_for(self._cond.wait(), timeout=1.0)
                except asyncio.TimeoutError:
                    pass
            self.active += 1
            self.peak = max(self.peak, self.active)

    async def release(self) -> None:
        async with self._cond:
            self.active -= 1
            self._cond.notify_all()

    def on_rate_limited(self) -> None:
        self.limit = max(1, self.limit // 2)
        self._changed = time.monotonic()


@dataclass
class _Shared:
    stop_reason: Optional[str] = None  # "failed_fast" | "stopped_cost"
    fatal: Optional[BaseException] = None
    outcomes: list[tuple[str, Optional[str]]] = field(default_factory=list)  # completion order
    first_traceback: Optional[str] = None
    done: int = 0


class PoolMixin:
    """``Engine``'s pool methods: ``_run_all`` and ``_skip``."""

    async def _run_all(self, todo, runner, evaluators, budget, journal, tracing, run_id, shared, total) -> None:
        limiter = AdaptiveLimiter(int(self.cfg.concurrency))
        self.limiter = limiter
        queue: deque = deque(todo)
        gate = asyncio.Event()
        first = {"taken": False}
        if not budget.active:
            gate.set()
        bar = _progress_bar(total, len(self.results), self.cfg.progress, self.stream)

        async def worker() -> None:
            while queue:
                if not gate.is_set():
                    if first["taken"]:
                        await gate.wait()
                        continue
                    first["taken"] = True
                    is_first = True
                else:
                    is_first = False
                if not queue:
                    break
                uploader = getattr(self, "uploader", None)
                if uploader is not None and uploader.fatal is not None:  # a refused upload stops new trials
                    break
                if shared.fatal is not None:
                    break
                row, trial = queue.popleft()
                if shared.stop_reason is None and budget.active and budget.exhausted():
                    shared.stop_reason = "stopped_cost"
                if shared.stop_reason is not None:
                    why = "cost_cap" if shared.stop_reason == "stopped_cost" else "fail_fast"
                    self._skip(row, trial, why, run_id, journal)
                    bar.update(1)
                    if is_first:
                        gate.set()
                    continue
                await limiter.acquire()
                try:
                    unpriced = await self._run_trial(row, trial, runner, evaluators, budget, journal, tracing, run_id, shared)
                finally:
                    await limiter.release()
                    bar.update(1)
                if unpriced and budget.active and shared.fatal is None:
                    # fail closed at whichever trial first shows a model with no price: no new trial starts
                    shared.fatal = UnpricedModelError(unpriced)
                if is_first:
                    if not unpriced and budget.active and not budget.measured:
                        self.say("Warning  max_cost_usd: the first trial showed no token usage or cost, so the cap "
                                 "is not enforced yet. Is the model client instrumented? "
                                 f"({self.instrument_hint}, or traceAI-openai / traceAI-anthropic for direct "
                                 "provider calls)")
                    gate.set()

        workers = [asyncio.ensure_future(worker()) for _ in range(int(self.cfg.concurrency))]
        try:
            await asyncio.gather(*workers)
        except asyncio.CancelledError:
            for w in workers:
                w.cancel()
            await asyncio.gather(*workers, return_exceptions=True)
            raise
        finally:
            bar.close()
            self.peak = limiter.peak

    def _skip(self, row: Row, trial: int, why: str, run_id: str, journal: Journal) -> None:
        msg = "run budget reached (max_cost_usd)" if why == "cost_cap" else "the run stopped early"
        self._record(row, trial, run_id, journal, status="skipped", output=None,
                     error=TrialError(type=why, message=msg), latency_ms=None, usage=None, cost=None,
                     trace=None, scores={}, attempts=0)


class _NoBar:
    def update(self, n: int) -> None:
        return None

    def close(self) -> None:
        return None


def _progress_bar(total: int, initial: int, enabled: bool, stream: Any):
    if not enabled:
        return _NoBar()
    try:
        from tqdm.auto import tqdm
    except ImportError:  # pragma: no cover
        return _NoBar()
    return tqdm(total=total, initial=initial, file=stream, unit="trial", leave=False, dynamic_ncols=True)
