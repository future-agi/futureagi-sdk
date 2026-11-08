"""Every httpx request reachable from returned, raised or callback objects is scrubbed.

The guarantee covers data attributes only: exception args, ``__dict__``/``__slots__``
values, ``__cause__``/``__context__``, exception-group children, ``__notes__``,
containers, ``Response.request``/``history`` and ``Headers``. Interpreter introspection
(frames, tracebacks, closures, gc) is outside it, and tracebacks are never cleared.
"""
import builtins
import inspect
import sys
import types
from types import SimpleNamespace

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway._gateway_config import GatewayConfig
from fi.gateway._transport import _scrub

ORIGIN = "https://gateway.example.test"
KEY = "synthetic-reach-key"
DEFAULT = "synthetic-reach-default"
CONFIG = "synthetic-reach-config"
SESSION = "synthetic-reach-session"
META = "synthetic-reach-metadata"
SECRETS = (KEY, DEFAULT, CONFIG, SESSION, META)
MASK = "[REDACTED]"
CHAT = {"id": "reply", "object": "chat.completion", "created": 0, "model": "fixture", "choices": []}
HAS_GROUPS = hasattr(builtins, "ExceptionGroup")

_LEAVES = (str, bytes, bytearray, memoryview)
_NOT_DATA = (type, types.ModuleType, types.FunctionType, types.MethodType,
             types.BuiltinFunctionType, types.GeneratorType, types.CoroutineType,
             types.AsyncGeneratorType, types.FrameType, types.TracebackType)


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


def reachable(root, limit=50000):
    """Independent value-aware walk over stored data; returns paths holding a secret.

    No globals, closures, frames, tracebacks or gc. Headers are read through their
    stored raw list so a masked header can never be mistaken for a live one.
    """
    stack, seen, hits = [("$", root)], set(), []
    while stack:
        path, value = stack.pop()
        if isinstance(value, _LEAVES):
            text = value if isinstance(value, str) else bytes(value).decode("utf-8", "replace")
            hits.extend(path for secret in SECRETS if secret in text)
            continue
        if value is None or isinstance(value, (bool, int, float, complex, *_NOT_DATA)):
            continue
        if id(value) in seen:
            continue
        seen.add(id(value))
        assert len(seen) < limit, "reachability walk exceeded its bound"
        if isinstance(value, dict):
            for index, (key, item) in enumerate(value.items()):
                stack.extend(((f"{path}.key[{index}]", key), (f"{path}[{key!r}]", item)))
        elif isinstance(value, (list, tuple, set, frozenset)):
            stack.extend((f"{path}[{i}]", item) for i, item in enumerate(value))
        if isinstance(value, BaseException):
            for name in ("args", "__cause__", "__context__", "exceptions", "__notes__"):
                stack.append((f"{path}.{name}", getattr(value, name, None)))
        try:
            stored = vars(value)
        except TypeError:
            stored = {}
        stack.extend((f"{path}.{name}", item) for name, item in stored.items() if name != "__traceback__")
        for cls in type(value).__mro__:
            slots = cls.__dict__.get("__slots__", ())
            for name in (slots,) if isinstance(slots, str) else slots:
                if name not in {"__dict__", "__weakref__"}:
                    try:
                        stack.append((f"{path}.{name}", getattr(value, name)))
                    except (AttributeError, TypeError):
                        pass
    return hits


def requests_in(root):
    """Every httpx.Request reachable through the same data attributes."""
    stack, seen, found = [root], set(), []
    while stack:
        value = stack.pop()
        if value is None or isinstance(value, (*_LEAVES, bool, int, float, *_NOT_DATA)) or id(value) in seen:
            continue
        seen.add(id(value))
        if isinstance(value, httpx.Request):
            found.append(value)
            continue
        if isinstance(value, dict):
            stack.extend([*value, *value.values()])
        elif isinstance(value, (list, tuple, set, frozenset)):
            stack.extend(value)
        if isinstance(value, BaseException):
            stack.extend((value.args, value.__cause__, value.__context__,
                          getattr(value, "exceptions", ()), getattr(value, "__notes__", ())))
        try:
            stack.extend(vars(value).values())
        except TypeError:
            pass
        for cls in type(value).__mro__:
            slots = cls.__dict__.get("__slots__", ())
            for name in (slots,) if isinstance(slots, str) else slots:
                if name not in {"__dict__", "__weakref__"}:
                    stack.append(getattr(value, name, None))
    return found


class SlotError(Exception):
    __slots__ = ("held",)


class Config(GatewayConfig):
    def to_headers(self):
        return {"X-Reach-Config": CONFIG}


OUTCOMES = [
    "auth_diagnostic", "error_attribute", "args_namespace", "containers", "slots",
    "notes", "chain", "history", "headers_alias", "status_diagnostic",
]
if HAS_GROUPS:
    OUTCOMES.append("group")
FAILING = set(OUTCOMES) - {"history"}


def raise_custom(outcome, request, first):
    if outcome == "auth_diagnostic":
        error = httpx.ConnectError("second auth exchange failed", request=request)
        error.diagnostic = SimpleNamespace(auth_response=first[0])
    elif outcome == "error_attribute":
        error = RuntimeError("custom transport failure")
        error.request = request
    elif outcome == "args_namespace":
        error = RuntimeError(SimpleNamespace(request=request))
    elif outcome == "containers":
        error = RuntimeError("containers")
        error.by_request = {request: "attempt"}
        error.frozen = frozenset({request})
        error.pairs = [("attempt", (request,))]
        error.nested = ({"deep": [request]},)
    elif outcome == "slots":
        error = SlotError("slots")
        error.held = SimpleNamespace(response=httpx.Response(500, request=request))
    elif outcome == "notes":
        error = RuntimeError("notes")
        error.__notes__ = [SimpleNamespace(request=request)]
    elif outcome == "chain":
        inner = RuntimeError("inner")
        inner.request = request
        error = RuntimeError("outer")
        error.__cause__ = RuntimeError("middle")
        error.__cause__.__context__ = inner
    elif outcome == "headers_alias":
        error = RuntimeError("alias")
        error.captured = request.headers
    elif outcome == "status_diagnostic":
        error = RuntimeError("status")
        error.response = httpx.Response(502, request=request)
    else:
        child = RuntimeError("child")
        child.request = request
        error = builtins.ExceptionGroup("grouped", [RuntimeError("other"), child])
    raise error


