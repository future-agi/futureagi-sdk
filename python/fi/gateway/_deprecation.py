"""The warning the agentcc 2.0 compatibility package emits on import.

It lives here, not in ``agentcc``, so a suite running with ``-W error`` can filter it
by class without importing agentcc::

    warnings.filterwarnings("ignore", category=fi.gateway.AgentCCDeprecationWarning)

It is a ``FutureWarning``: PEP 565 hides ``DeprecationWarning`` outside ``__main__``, so
a library user would never see it.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar, cast
import inspect
import warnings

_T = TypeVar("_T")


def deprecated(api: _T) -> _T:
    """Warn on use while preserving callable signatures and class identity."""
    target = api.__init__ if isinstance(api, type) else api
    name = getattr(api, "__qualname__", "gateway API")

    def warn() -> None:
        warnings.warn(
            f"{name} is a deprecated released gateway compatibility API.",
            DeprecationWarning, stacklevel=3,
        )

    if inspect.iscoroutinefunction(target):
        @wraps(target)
        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            try:
                warn()
                return await target(*args, **kwargs)
            finally:
                args, kwargs = (), {}
    else:
        @wraps(target)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            try:
                warn()
                return target(*args, **kwargs)
            finally:
                args, kwargs = (), {}
    if isinstance(api, type):
        api.__init__ = wrapped
        return api
    return cast(_T, wrapped)


def deprecated_options(*names: str, positional: bool = False) -> Callable[[_T], _T]:
    """Warn for explicitly supplied legacy constructor options, even False/None."""
    def decorate(cls: _T) -> _T:
        original = cls.__init__

        @wraps(original)
        def init(self: Any, *args: Any, **kwargs: Any) -> None:
            try:
                supplied = [name for name in names if name in kwargs]
                if positional and args:
                    supplied.append("positional arguments")
                if supplied:
                    warnings.warn(
                        "Deprecated gateway compatibility options: " + ", ".join(supplied),
                        DeprecationWarning, stacklevel=2,
                    )
                original(self, *args, **kwargs)
            finally:
                # Rebind only our aliases; never mutate caller arguments/frames.
                self, args, kwargs = None, (), {}

        cls.__init__ = init
        return cls
    return decorate


class AgentCCDeprecationWarning(FutureWarning):
    """agentcc is now part of futureagi: ``from fi.gateway import AgentCC`` (same names)."""
