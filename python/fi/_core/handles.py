"""Handles: ``Deployment``, ``Sandbox`` and ``Run`` share one base, in both modes.

A handle wraps one resource's wire-shaped dict:

- attribute access for its fields (``handle.id``, ``handle.status``; a snake_case name reads the
  camelCase wire key, so ``run.agent_id`` reads ``agentId``);
- ``.data`` is the dict itself and ``.to_dict()`` a deep copy;
- ``.refresh()`` re-reads it from the server and returns the handle;
- **one waiter**, ``.wait(timeout=...)``: polls ``refresh()`` with backoff until the subclass's
  ``_is_done()`` holds, and raises ``APITimeoutError`` when the time runs out. Errors from a
  refresh propagate at once (a typed error is never retried here).

A resource namespace subclasses :class:`Handle` / :class:`AsyncHandle` and defines ``_get()`` (the read call)
and ``_is_done()`` (from its contract's terminal statuses). :func:`poll_until` and
:func:`apoll_until` are the shared loop for any other waiter (``wait_for_approval``).
"""

from __future__ import annotations

import asyncio
import copy
import re
import time
from typing import Any, Awaitable, Callable, Mapping, Optional, TypeVar

from fi.errors import APITimeoutError

T = TypeVar("T")
_CAMEL = re.compile(r"_([a-z0-9])")


def camel(name: str) -> str:
    """``agent_id`` → ``agentId``."""
    return _CAMEL.sub(lambda m: m.group(1).upper(), name)


def _timeout(label: str, seconds: float) -> APITimeoutError:
    err = APITimeoutError(f"{label} did not finish within {seconds:g} s")
    err.kind, err.possibly_applied = "timeout", True
    return err


def poll_until(
    check: Callable[[], Optional[T]],
    *,
    timeout: float,
    interval: float = 0.5,
    max_interval: float = 5.0,
    label: str = "the wait",
    sleep: Callable[[float], Any] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> T:
    """Call ``check`` until it returns something other than None, and return that (sync)."""
    deadline = clock() + timeout
    while True:
        value = check()
        if value is not None:
            return value
        remaining = deadline - clock()
        if remaining <= 0:
            raise _timeout(label, timeout)
        sleep(min(interval, remaining))
        interval = min(interval * 2, max_interval)


async def apoll_until(
    check: Callable[[], Awaitable[Optional[T]]],
    *,
    timeout: float,
    interval: float = 0.5,
    max_interval: float = 5.0,
    label: str = "the wait",
    sleep: Optional[Callable[[float], Any]] = None,
    clock: Callable[[], float] = time.monotonic,
) -> T:
    """Await ``check`` until it returns something other than None, and return that (async)."""
    deadline = clock() + timeout
    while True:
        value = await check()
        if value is not None:
            return value
        remaining = deadline - clock()
        if remaining <= 0:
            raise _timeout(label, timeout)
        result = (sleep or asyncio.sleep)(min(interval, remaining))
        if asyncio.iscoroutine(result):
            await result
        interval = min(interval * 2, max_interval)


class _HandleBase:
    #: The resource's noun, for messages (``deployment``).
    noun = "resource"

    def __init__(self, namespace: Any, data: Mapping[str, Any]) -> None:
        object.__setattr__(self, "_ns", namespace)
        object.__setattr__(self, "_data", dict(data))

    @property
    def data(self) -> dict[str, Any]:
        """The wire-shaped dict (the same object each time until the next ``refresh()``)."""
        return self._data

    def to_dict(self) -> dict[str, Any]:
        """A deep copy of the wire-shaped dict."""
        return copy.deepcopy(self._data)

    @property
    def id(self) -> Any:
        return self._data.get("id")

    @property
    def status(self) -> Any:
        return self._data.get("status")

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        data = object.__getattribute__(self, "_data")
        for key in (name, camel(name)):
            if key in data:
                return data[key]
        raise AttributeError(f"{type(self).__name__} has no field {name!r} (see .data for every field)")

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"{type(self).__name__} is read-only; call the namespace's methods to change it")

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id!r}, status={self.status!r})"

    def __eq__(self, other: object) -> bool:
        return type(other) is type(self) and other.id == self.id and other._data == self._data  # type: ignore[attr-defined]

    __hash__ = None  # type: ignore[assignment]

    def _is_done(self) -> bool:
        raise NotImplementedError

    def _replace(self, data: Mapping[str, Any]) -> None:
        object.__setattr__(self, "_data", dict(data))


class Handle(_HandleBase):
    """The sync base: subclasses define ``_get()`` and ``_is_done()``."""

    def _get(self) -> Mapping[str, Any]:
        raise NotImplementedError

    def refresh(self) -> "Handle":
        """Re-read the resource from the server; returns the handle."""
        self._replace(self._get())
        return self

    def wait(
        self,
        timeout: float = 300.0,
        *,
        interval: float = 0.5,
        max_interval: float = 5.0,
        sleep: Callable[[float], Any] = time.sleep,
    ) -> "Handle":
        """Poll until the resource reaches a final state; returns the handle."""
        if self._is_done():
            return self
        return poll_until(
            lambda: self if self.refresh()._is_done() else None,
            timeout=timeout,
            interval=interval,
            max_interval=max_interval,
            label=f"waiting for {self.noun} {self.id}",
            sleep=sleep,
        )


class AsyncHandle(_HandleBase):
    """The async base: subclasses define ``async _get()`` and ``_is_done()``."""

    async def _get(self) -> Mapping[str, Any]:
        raise NotImplementedError

    async def refresh(self) -> "AsyncHandle":
        self._replace(await self._get())
        return self

    async def wait(
        self,
        timeout: float = 300.0,
        *,
        interval: float = 0.5,
        max_interval: float = 5.0,
        sleep: Optional[Callable[[float], Any]] = None,
    ) -> "AsyncHandle":
        if self._is_done():
            return self

        async def check() -> Optional["AsyncHandle"]:
            await self.refresh()
            return self if self._is_done() else None

        return await apoll_until(
            check,
            timeout=timeout,
            interval=interval,
            max_interval=max_interval,
            label=f"waiting for {self.noun} {self.id}",
            sleep=sleep,
        )
