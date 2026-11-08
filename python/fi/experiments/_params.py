"""``params=``, ``ctx.params`` and ``experiments.param()`` (SDK-18).

The engine sets a context variable for each trial, so ``experiments.param("model", "gpt-x")``
reads this trial's value anywhere: inside the task, inside a factory, inside a tool.
"""

from __future__ import annotations

import contextvars
import json
from types import MappingProxyType
from typing import Any, Mapping, Optional

_current: contextvars.ContextVar[Optional[Mapping[str, Any]]] = contextvars.ContextVar(
    "fi_experiments_params", default=None
)
_MISSING = object()


def param(name: str, default: Any = _MISSING) -> Any:
    """This trial's param ``name``; ``default`` outside a trial or when the run did not set it."""
    current = _current.get()
    if current is not None and name in current:
        return current[name]
    if default is _MISSING:
        if current is None:
            raise LookupError(f"experiments.param({name!r}) was called outside a trial and has no default")
        raise LookupError(f"the run sets no param {name!r} (params: {', '.join(current) or 'none'})")
    return default


def frozen(params: Optional[Mapping[str, Any]]) -> Mapping[str, Any]:
    return MappingProxyType(dict(params or {}))


def bind(params: Mapping[str, Any]) -> contextvars.Token:
    return _current.set(params)


def unbind(token: contextvars.Token) -> None:
    _current.reset(token)


def parse_cli_param(text: str, *, as_string: bool = False) -> tuple[str, Any]:
    """``k=v`` with ``v`` JSON-typed (``--param``), or kept as a string (``--param-str``)."""
    if "=" not in text:
        raise ValueError(f"expected k=v, got {text!r}")
    key, raw = text.split("=", 1)
    key = key.strip()
    if not key:
        raise ValueError(f"expected k=v, got {text!r}")
    if as_string:
        return key, raw
    try:
        return key, json.loads(raw)
    except ValueError:
        return key, raw
