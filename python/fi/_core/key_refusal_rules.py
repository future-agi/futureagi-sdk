"""Rules of the 0.8.1 line for sending keys, kept apart from the plain-HTTP policy (``fi._core.http_security``) and the
proxy routing (``fi._core.proxy_routing``) that apply them: host spellings the opt-in does not unlock, the connection
pools that count as direct, and the cookies that carry a key."""
from __future__ import annotations

import ipaddress
import re
from typing import Any, Optional

_SCHEME_PREFIX = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")


_BLANK = re.compile(r"[\x00-\x20\x7f]")
_NUMERIC_HOST = re.compile(r"^(0x[0-9a-f]*|[0-9]+)(\.(0x[0-9a-f]*|[0-9]+))*\.?$")


def written_authority(text: str) -> str:
    """The authority (host and port, user info kept) as ``text`` writes it, for a URL with a scheme."""
    match = _SCHEME_PREFIX.match(text.strip())
    rest = text.strip()[match.end():] if match else ""
    return re.split(r"[/?#]", rest, maxsplit=1)[0]


def spelling_problem(text: str, written: str) -> Optional[str]:
    """Why a plain-HTTP host that is not loopback is written in a form readers take differently (the 0.8.1 rule): a
    host or port with a non-ASCII character (the libraries map some of them to ASCII before they connect), a host
    ending in a dot, or a host written as numbers that are not an IPv4 address in four plain decimal parts
    (``127.1``, ``2130706433``, ``0x7f.0.0.1``, ``0177.0.0.1``). The opt-in does not unlock such a host."""
    if not written_authority(text).isascii() or not written.isascii():
        return "writes its host or port with a non-ASCII character"
    if _BLANK.search(written_authority(text)):
        return "writes its host or port with whitespace or a control character"
    if written.endswith("."):
        return "writes its host with a trailing dot"
    if _NUMERIC_HOST.match(written):
        try:
            ipaddress.IPv4Address(written)
        except ValueError:
            return "writes its host as an IPv4 address in a short, hex or octal form"
    return None


# A pool counts as direct only when it is exactly one of these httpcore classes (a subclass may route anywhere), holds no
# ``proxy=`` setting and uses exactly one of httpcore's own network backends for that pool (the 0.8.1 rule).
_DIRECT_POOL_BACKENDS = (
    ("ConnectionPool", (("httpcore", "SyncBackend"),)),
    (
        "AsyncConnectionPool",
        (("httpcore._backends.auto", "AutoBackend"), ("httpcore", "AnyIOBackend"), ("httpcore", "TrioBackend")),
    ),
)
# Methods that, set on a pool or backend instance, take the place of httpcore's own.
_POOL_METHODS = ("handle_request", "handle_async_request", "create_connection")
_BACKEND_METHODS = ("connect_tcp", "connect_unix_socket")
# The backends httpcore's automatic backend hands each connection to, once it has picked one.
_AUTO_INNER_BACKENDS = (("httpcore", "AnyIOBackend"), ("httpcore", "TrioBackend"))
# The SDK's own wrappers that dial the name ``localhost`` to loopback and hand every other host to the backend they hold.
_LOCALHOST_BACKENDS = (("fi._core.loopback", "LocalhostBackend"), ("fi._core.loopback", "AsyncLocalhostBackend"))


def _named_class(module: str, name: str) -> Optional[type]:
    import importlib

    try:
        cls = getattr(importlib.import_module(module), name, None)
    except Exception:
        return None
    return cls if isinstance(cls, type) else None


def _instance_names(value: Any) -> dict:
    return getattr(value, "__dict__", None) or {}


def _is_exactly(value: Any, classes: tuple) -> bool:
    return any(cls is not None and type(value) is cls for cls in (_named_class(*each) for each in classes))


def _is_own_backend(backend: Any, classes: tuple) -> bool:
    """Whether ``backend`` is exactly one of ``classes`` with none of its methods set on the instance and, when it hands
    connections to a backend it holds (httpcore's automatic backend), that backend exactly httpcore's AnyIO or Trio
    backend with none of its methods set on the instance. The SDK's localhost wrapper counts when the backend it holds
    passes the same test."""
    names = _instance_names(backend)
    if any(name in names for name in _BACKEND_METHODS):
        return False
    if _is_exactly(backend, _LOCALHOST_BACKENDS):
        return "_inner" in names and _is_own_backend(names["_inner"], classes)
    if not _is_exactly(backend, classes):
        return False
    if "_backend" in names:
        return _is_own_backend(names["_backend"], _AUTO_INNER_BACKENDS)
    return True


def is_direct_pool(pool: Any) -> bool:
    """Whether ``pool`` is exactly httpcore's ``ConnectionPool`` or ``AsyncConnectionPool`` (not a subclass), with no
    ``proxy=`` setting, none of its request or connection methods set on the instance, and exactly one of httpcore's own
    network backends (see :func:`_is_own_backend`). A pool without a readable backend counts as not direct."""
    missing = object()
    backend = getattr(pool, "_network_backend", missing)
    if backend is missing or getattr(pool, "_proxy", None) is not None:
        return False
    if any(name in _instance_names(pool) for name in _POOL_METHODS):
        return False
    for pool_name, backends in _DIRECT_POOL_BACKENDS:
        pool_class = _named_class("httpcore", pool_name)
        if pool_class is not None and type(pool) is pool_class:
            return _is_own_backend(backend, backends)
    return False


_KEY_COOKIE_NAMES = frozenset({"x-api-key", "x-secret-key"})


def _name(value: Any) -> str:
    text = bytes(value).decode("latin-1") if isinstance(value, (bytes, bytearray)) else str(value)
    return text.strip().casefold().replace("_", "-")


def cookie_names_a_key(name: Any, value: Any) -> bool:
    """Whether ``name: value`` is a ``Cookie`` header holding a cookie named ``X-Api-Key`` or ``X-Secret-Key`` (names
    compared as header names are), as the 0.8.1 rule reads it: a server that maps cookies to headers receives the key."""
    if value is None or _name(name) != "cookie":
        return False
    text = bytes(value).decode("latin-1") if isinstance(value, (bytes, bytearray)) else str(value)
    return any(_name(part.split("=", 1)[0]) in _KEY_COOKIE_NAMES for part in text.split(";"))


def _attributes(holder: Any) -> list:
    values = list(getattr(holder, "__dict__", {}).values())
    for cls in type(holder).__mro__:
        slots = cls.__dict__.get("__slots__", ())
        for slot in (slots,) if isinstance(slots, str) else slots:
            if slot not in ("__dict__", "__weakref__") and hasattr(holder, slot):
                values.append(getattr(holder, slot))
    return values


def inner_transports(transport: Any) -> list:
    """The transports ``transport`` holds (the 0.8.1 rule): in its attributes (``__dict__`` and ``__slots__``), in dicts,
    lists, tuples and sets at any depth, and the transports of an ``httpx`` client it holds (its own and every mounted
    one)."""
    import httpx

    found: list = []
    seen: set = set()
    pending = _attributes(transport)
    while pending:
        value = pending.pop()
        if id(value) in seen:
            continue
        seen.add(id(value))
        if isinstance(value, (httpx.BaseTransport, httpx.AsyncBaseTransport)):
            found.append(value)
        elif isinstance(value, (httpx.Client, httpx.AsyncClient)):
            pending.append(getattr(value, "_transport", None))
            pending.extend((getattr(value, "_mounts", None) or {}).values())
        elif isinstance(value, dict):
            pending.extend(value.values())
        elif isinstance(value, (list, tuple, set, frozenset)):
            pending.extend(value)
    return found


def authority_readable(text: str) -> bool:
    """Whether the authority ``text`` writes is ASCII with no whitespace or control character (the 0.8.1 rule before
    the loopback exception applies)."""
    authority = written_authority(text)
    return authority.isascii() and not _BLANK.search(authority)


def sdk_direct(transport: Any) -> bool:
    """Whether ``transport`` is one the SDK built to send direct (it carries ``_fi_decided_by_environment``) and holds no
    pool, or exactly httpcore's own pool with no proxy setting: such a marker on a proxy pool is not taken on trust."""
    if not getattr(transport, "_fi_decided_by_environment", False):
        return False
    pool = getattr(transport, "_pool", None)
    return pool is None or is_direct_pool(pool)
