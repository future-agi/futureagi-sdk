"""Plain callables: ``task(row)``, ``task(row, ctx)``, sync or async, and zero-argument factories."""

from __future__ import annotations

import inspect
from typing import Any, Callable

from fi.experiments.adapters._base import TaskRunner, is_async_callable, qualname
from fi.experiments.errors import UsageError


def positional_arity(fn: Callable[..., Any]) -> int:
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return 1
    count = 0
    for p in sig.parameters.values():
        if p.kind in (p.VAR_POSITIONAL,):
            return 2
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) and p.default is p.empty:
            count += 1
        elif p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) and p.name == "ctx":
            count += 1
    return count


class CallableRunner(TaskRunner):
    framework = "callable"

    def __init__(self, fn: Callable[..., Any]) -> None:
        arity = positional_arity(fn)
        if arity > 2:
            raise UsageError(
                f"task {qualname(fn)} takes {arity} arguments; a task takes (row) or (row, ctx)"
            )
        self.fn = fn
        self.arity: int = max(arity, 1)
        self.is_async: bool = is_async_callable(fn)

    def describe(self) -> str:
        args = "row, ctx" if self.arity == 2 else "row"
        prefix = "await " if self.is_async else ""
        return f"{prefix}{qualname(self.fn)}({args})"

    def _args(self, row: Any, ctx: Any) -> tuple[Any, ...]:
        return (row, ctx) if self.arity == 2 else (row,)

    def call(self, row: Any, ctx: Any) -> Any:
        return self.fn(*self._args(row, ctx))

    async def acall(self, row: Any, ctx: Any) -> Any:
        result = self.fn(*self._args(row, ctx))
        if inspect.isawaitable(result):
            result = await result
        return result


class FactoryRunner(TaskRunner):
    """A zero-argument callable: called once per trial; its product is the task for that trial."""

    is_factory = True

    def __init__(self, factory: Callable[[], Any], resolve: Callable[[Any], TaskRunner]) -> None:
        if is_async_callable(factory):
            raise UsageError(
                f"{qualname(factory)} is an async function with no arguments. A task takes (row) "
                "or (row, ctx); a factory is a plain function that returns the agent."
            )
        self.factory = factory
        self._resolve = resolve
        self.framework = "factory"

    def describe(self) -> str:
        return f"{qualname(self.factory)}() per trial → the object's call"

    def product(self) -> TaskRunner:
        obj = self.factory()
        if obj is None:
            raise UsageError(f"factory {qualname(self.factory)}() returned None")
        runner = self._resolve(obj, from_factory=True)
        if runner.is_factory:
            raise UsageError(f"factory {qualname(self.factory)}() returned another factory")
        return runner
