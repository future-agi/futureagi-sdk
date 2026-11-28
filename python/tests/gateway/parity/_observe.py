"""Turn whatever a case returns or raises into stable, JSON-able data.

Types are named by ``__qualname__`` only: the module a class lives in is not
behaviour (fi.gateway splits agentcc's modules), and where each public name is
exported is recorded separately by the surface cases. Strings lose memory
addresses and install paths (up to ``site-packages/``, ``dist-packages/`` or
``src/``); nothing else is rewritten, and ``_hygiene.py`` refuses to write any
other local path.
"""

from __future__ import annotations

import base64
import dataclasses
import enum
import inspect
import json
import math
import pickle
import re
from typing import Any

_ADDR = re.compile(r"0x[0-9a-fA-F]{6,}")
_PATH = re.compile(r"(?:/[\w.@+-]+)+/(?:site-packages|dist-packages|src)/")
MAX_DEPTH = 8


def clean(text: str) -> str:
    return _PATH.sub("<path>/", _ADDR.sub("0x?", text))


def type_name(obj: Any) -> str:
    cls = obj if isinstance(obj, type) else type(obj)
    return cls.__qualname__


def _float(value: float) -> Any:
    if math.isnan(value) or math.isinf(value):
        return repr(value)
    return value


def _pickle(exc: BaseException) -> dict[str, Any]:
    try:
        back = pickle.loads(pickle.dumps(exc))
    except Exception as err:  # the failure itself is the observation
        return {"ok": False, "error": type_name(err), "message": clean(str(err))}
    return {
        "ok": True,
        "type": type_name(back),
        "str": clean(str(back)),
        "args": observe(back.args),
    }


def observe_exception(exc: BaseException, depth: int = 0) -> dict[str, Any]:
    attrs = {}
    for key, value in sorted(vars(exc).items()):
        if key in {"response", "request", "__notes__"}:
            continue
        attrs[key] = observe(value, depth + 1)
    out: dict[str, Any] = {
        "__exception__": type_name(exc),
        "mro": [c.__qualname__ for c in type(exc).__mro__],
        "str": clean(str(exc)),
        "repr": clean(repr(exc)),
        "args": observe(exc.args, depth + 1),
        "attrs": attrs,
        "pickle": _pickle(exc),
    }
    response = vars(exc).get("response")
    if response is not None:
        out["response_status"] = getattr(response, "status_code", type_name(response))
    if exc.__cause__ is not None:
        out["cause"] = type_name(exc.__cause__)
    return out


def _model(value: Any, depth: int) -> dict[str, Any]:
    try:
        data = value.model_dump(mode="json")
    except Exception as err:
        data = {"__dump_error__": type_name(err)}
    out = {"__model__": type_name(value), "data": data}
    declared = getattr(type(value), "model_fields", {})
    if "agentcc" not in declared and "agentcc" in vars(value):
        out["agentcc"] = observe(vars(value)["agentcc"], depth + 1)
    return out


def _object(value: Any, depth: int) -> dict[str, Any]:
    try:
        attrs = {k: v for k, v in vars(value).items() if not k.startswith("_")}
    except TypeError:
        return {"__object__": type_name(value), "repr": clean(repr(value))}
    return {
        "__object__": type_name(value),
        "attrs": {k: observe(v, depth + 1) for k, v in sorted(attrs.items())},
    }


def observe(value: Any, depth: int = 0) -> Any:
    if depth > MAX_DEPTH:
        return {"__truncated__": type_name(value)}
    if (
        value is None
        or isinstance(value, (bool, int, str))
        and not isinstance(value, enum.Enum)
    ):
        return clean(value) if isinstance(value, str) else value
    if isinstance(value, float):
        return _float(value)
    if isinstance(value, enum.Enum):
        return {"__enum__": type_name(value), "value": observe(value.value, depth + 1)}
    if isinstance(value, (bytes, bytearray)):
        try:
            return {"__bytes__": bytes(value).decode("utf-8")}
        except UnicodeDecodeError:
            return {"__bytes_b64__": base64.b64encode(bytes(value)).decode("ascii")}
    if isinstance(value, BaseException):
        return observe_exception(value, depth)
    if isinstance(value, dict):
        return {str(k): observe(v, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [observe(v, depth + 1) for v in value]
    if isinstance(value, (set, frozenset)):
        items = [observe(v, depth + 1) for v in value]
        return {"__set__": sorted(items, key=lambda x: json.dumps(x, sort_keys=True))}
    if isinstance(value, type):
        return {"__class__": value.__qualname__}
    if hasattr(value, "model_dump") and hasattr(type(value), "model_fields"):
        return _model(value, depth)
    if dataclasses.is_dataclass(value):
        fields = {
            f.name: observe(getattr(value, f.name), depth + 1)
            for f in dataclasses.fields(value)
        }
        return {"__dataclass__": type_name(value), "fields": fields}
    module = type(value).__module__ or ""
    if module.startswith("httpx"):
        if hasattr(value, "status_code"):
            return {"__httpx__": type_name(value), "status": value.status_code}
        if hasattr(value, "multi_items"):
            return {
                "__httpx__": type_name(value),
                "items": sorted(list(p) for p in value.multi_items()),
            }
        return {"__httpx__": type_name(value)}
    if inspect.isroutine(value) or callable(value) and not hasattr(value, "__dict__"):
        return {"__callable__": getattr(value, "__qualname__", type_name(value))}
    if inspect.isgenerator(value) or inspect.isasyncgen(value):
        return {"__generator__": getattr(value, "__qualname__", type_name(value))}
    return _object(value, depth)


def dump(data: Any) -> str:
    """The one serialisation goldens use: sorted keys, ASCII, one trailing newline."""
    return (
        json.dumps(data, indent=1, sort_keys=True, ensure_ascii=True, allow_nan=False)
        + "\n"
    )
