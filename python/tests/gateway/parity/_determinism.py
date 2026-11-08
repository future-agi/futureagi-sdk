"""Make a case repeatable: fake clock, recorded sleeps, fixed randomness.

Everything is patched on the stdlib and anyio modules themselves, never on a
target module path, so the same harness serves ``agentcc`` and ``fi.gateway``.

* ``time.sleep`` / ``asyncio.sleep`` / ``anyio.sleep`` record the delay and
  advance the fake clock instead of waiting (``sleep(0)`` still yields).
* ``time.time`` and ``time.monotonic`` read the fake clock in sync mode only;
  the asyncio loop keeps the real ``time.monotonic`` in async mode.
* ``random.uniform(a, b)`` records ``[a, b]`` and returns the midpoint, so a
  backoff schedule shows its base delay and its jitter band separately.
* ``random.random`` returns a fixed sequence; ``uuid.uuid4`` counts up.
"""

from __future__ import annotations

import asyncio
import random
import time
import uuid
from typing import Any

EPOCH = 1761177600.0  # 2025-10-23T00:00:00Z, also the fixture frames' "created"


class Determinism:
    def __init__(self, *, sync_clock: bool) -> None:
        self.sync_clock = sync_clock
        self.now = EPOCH
        self.sleeps: list[float] = []
        self.jitter: list[list[float]] = []
        self._uuid = 0
        self._rand = 0
        self._saved: list[tuple[Any, str, Any]] = []

    # -- replacements --------------------------------------------------------
    def _sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += max(seconds, 0)

    def _time(self) -> float:
        return self.now

    def _monotonic(self) -> float:
        return self.now - EPOCH + 1000.0

    def _uniform(self, a: float, b: float) -> float:
        self.jitter.append([a, b])
        return (a + b) / 2

    def _random(self) -> float:
        self._rand += 1
        return (self._rand * 0.137) % 1.0

    def _uuid4(self) -> uuid.UUID:
        self._uuid += 1
        return uuid.UUID(int=self._uuid, version=4)

    # -- install / remove --------------------------------------------------------
    def install(self) -> None:
        import anyio

        real_asyncio_sleep = asyncio.sleep
        state = self

        async def asyncio_sleep(delay: float, result: Any = None) -> Any:
            if delay:
                state._sleep(delay)
            return await real_asyncio_sleep(0, result)

        async def anyio_sleep(delay: float) -> None:
            if delay:
                state._sleep(delay)
            await real_asyncio_sleep(0)

        patches: list[tuple[Any, str, Any]] = [
            (time, "sleep", self._sleep),
            (asyncio, "sleep", asyncio_sleep),
            (anyio, "sleep", anyio_sleep),
            (random, "uniform", self._uniform),
            (random, "random", self._random),
            (uuid, "uuid4", self._uuid4),
        ]
        if self.sync_clock:
            patches += [
                (time, "time", self._time),
                (time, "monotonic", self._monotonic),
            ]
        for owner, name, replacement in patches:
            self._saved.append((owner, name, getattr(owner, name)))
            setattr(owner, name, replacement)

    def remove(self) -> None:
        while self._saved:
            owner, name, original = self._saved.pop()
            setattr(owner, name, original)

    def report(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.sleeps:
            out["sleeps"] = self.sleeps
        if self.jitter:
            out["jitter"] = self.jitter
        return out
