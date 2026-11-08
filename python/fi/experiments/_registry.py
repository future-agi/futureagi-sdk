"""File mode: in CLI context, ``experiments.run(...)`` calls declared in a run file register
instead of executing, so nothing runs twice; the CLI then runs each once with its flags as
overlays."""

from __future__ import annotations

import contextvars
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator, Optional

_collect: contextvars.ContextVar[Optional[list]] = contextvars.ContextVar("fi_exp_collect", default=None)


@dataclass
class DeclaredRun:
    kwargs: dict

    @property
    def name(self) -> str:
        explicit = self.kwargs.get("name")
        if explicit:
            return str(explicit)
        task = self.kwargs.get("task")
        return str(getattr(task, "__name__", None) or getattr(task, "name", None) or type(task).__name__)

    def __getattr__(self, item: str) -> Any:
        if item.startswith("__"):
            raise AttributeError(item)
        from fi.experiments.errors import UsageError

        raise UsageError(
            "this experiments.run(...) was declared in a run file that `futureagi-py run` is loading; "
            "the CLI runs it after loading the file, so its result is not available at import time. "
            "Move code that reads the result under `if __name__ == \"__main__\":` in a script you run with python."
        )


def collecting() -> bool:
    return _collect.get() is not None


def declare(kwargs: dict) -> DeclaredRun:
    declared = DeclaredRun(dict(kwargs))
    bucket = _collect.get()
    assert bucket is not None
    bucket.append(declared)
    return declared


@contextmanager
def collect() -> Iterator[list]:
    bucket: list = []
    token = _collect.set(bucket)
    try:
        yield bucket
    finally:
        _collect.reset(token)

