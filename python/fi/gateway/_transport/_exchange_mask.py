"""Mask SDK-known exchanges without depending on optional diagnostic discovery.

This is fixed HTTPX storage handling, not an arbitrary object-graph walk. Each
captured exchange is processed separately after authentication completes. Native
storage reads bypass caller attribute hooks and use a separate fixed layout bound;
headers are then masked in one linear pass. Caller-mutated layouts are best effort.
"""
from __future__ import annotations

from typing import Any

import httpx

from fi.gateway._constants import is_credential_name

_MRO = type.__dict__["__mro__"]
_DICT = type.__dict__["__dict__"]
_STORAGE = tuple((cls, _DICT.__get__(cls)["__dict__"])
                 for cls in (httpx.Request, httpx.Response, httpx.Headers)) + (
    (httpx.HTTPError, BaseException.__dict__["__dict__"]),
)
_MASK = b"[REDACTED]"


def _is(value: Any, cls: type) -> bool:
    return any(base is cls for base in _MRO.__get__(type(value)))


def _fields(value: Any) -> dict[str, Any]:
    for cls, descriptor in _STORAGE:
        if _is(value, cls):
            stored = descriptor.__get__(value, type(value))
            result = {}
            # Supported HTTPX layouts have fewer than 32 fields. Padding or
            # moving native storage requires caller mutation, not normal HTTPX.
            for index, (name, item) in enumerate(dict.items(stored)):
                if index >= 64:
                    break
                if _is(name, str):
                    native = type(name) is str
                    name = "".join((name,))
                    if name in {"headers", "_list", "_request", "request", "response", "next_request", "history"}:
                        if native or name not in result:
                            result[name] = item
            return result
    return {}


def _headers(value: Any, names: frozenset[str]) -> None:
    if not _is(value, httpx.Headers):
        return
    rows = _fields(value).get("_list")
    if not _is(rows, list):
        return
    for index, row in enumerate(list.__iter__(rows)):
        # An unknown row shape is discarded, never retained as raw diagnostics.
        replacement = (b"x-redacted", b"x-redacted", _MASK)
        if type(row) is tuple and len(row) == 3 and all(type(part) is bytes for part in row):
            original, lower, raw = row
            try:
                name = lower.decode("ascii")
                replacement = (original, lower, _MASK) if name in names or is_credential_name(name) else row
            except UnicodeDecodeError:
                pass
        list.__setitem__(rows, index, replacement)


def mask_known_exchange(request: Any, response: Any, names: frozenset[str], error: Any = None) -> None:
    """Mask known request/response headers and HTTPX's native redirect links.

    Capture invokes this once per actual exchange, so neither graph budgets nor
    a failure in graph discovery can discard an exchanged request's header mask.
    No methods, properties, iterator overrides or diagnostic objects are invoked.
    """
    pending = [request, response, error]
    seen = set()
    # HTTPX's supported redirect limit is 20; capture also processes each actual
    # exchange independently. A wider injected history remains best effort.
    for _ in range(64):
        if not pending:
            break
        value = pending.pop()
        if value is None or id(value) in seen:
            continue
        seen.add(id(value))
        try:
            fields = _fields(value)
            if _is(value, httpx.Response):
                _headers(fields.get("headers"), frozenset())
                pending.extend((fields.get("_request"), fields.get("next_request")))
                history = fields.get("history")
                if type(history) is list:
                    pending.extend(list.__getitem__(history, slice(0, 20)))
            elif _is(value, httpx.Request):
                _headers(fields.get("headers"), names)
            elif _is(value, httpx.Headers):
                _headers(value, names)
            elif _is(value, httpx.HTTPError):
                pending.extend((fields.get("_request"), fields.get("request"), fields.get("response")))
        except BaseException:
            # Caller-mutated storage cannot replace the original send failure.
            continue
