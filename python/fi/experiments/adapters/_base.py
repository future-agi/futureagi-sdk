from __future__ import annotations

import inspect
from typing import Any, Optional


class TaskRunner:
    """The resolved way to call a task for one trial."""

    framework: str = "callable"
    is_async: bool = False
    is_factory: bool = False
    needs_single_input: bool = False
    instrumentor: Optional[str] = None  # the instrument.FRAMEWORKS key

    def describe(self) -> str:  # the resolved call, printed before the first trial
        raise NotImplementedError

    def call(self, row: Any, ctx: Any) -> Any:  # sync runners
        raise NotImplementedError

    async def acall(self, row: Any, ctx: Any) -> Any:  # async runners
        raise NotImplementedError


def qualname(obj: Any) -> str:
    name = getattr(obj, "__qualname__", None) or getattr(obj, "__name__", None)
    if name is None:
        name = type(obj).__name__
    return str(name)


def is_async_callable(obj: Any) -> bool:
    if inspect.iscoroutinefunction(obj):
        return True
    call = getattr(obj, "__call__", None)
    return call is not None and inspect.iscoroutinefunction(call)
