"""The process-wide egress guard for the Python runner, under every client.

    guard = EgressGuard(allow=["rig-host"])
    process = install_process_guard(guard)   # BEFORE the SDK under test is imported
    ...
    process.uninstall()

``EgressGuard.transport()`` refuses a request before httpx sees it, but only for a client built with
that transport. This module is the backstop for everything else in the process. A client the SDK
builds itself (its own ``httpx.Client``, ``urllib``, ``requests``, an OTLP/HTTP span exporter, asyncio)
resolves names through ``socket.getaddrinfo`` and connects through ``socket.socket.connect``, so:

- a name lookup (``getaddrinfo``, ``gethostbyname``, ``gethostbyname_ex``) of a host the rule refuses
  trips before any DNS query is made; the addresses an allowed name resolves to are remembered, so
  connecting to them is allowed (``create_connection`` connects to the resolved address, not the name);
- a ``connect``, ``connect_ex`` or ``sendto`` to an address that is not loopback, not allowlisted and not
  resolved from an allowed name trips before the socket is used;
- importing a module that does its networking in native code these patches cannot see (``grpc``: the
  OTLP gRPC exporter's transport; ``pycurl``) trips at import: the run fails closed.

Every trip is recorded on the ``EgressGuard`` (the same list ``receipt()`` reports), whether or not the
SDK swallows the exception, so a trip fails the run either way.

Limits of in-process patching: a child process, native code other than the refused modules, and a raw
``_socket.socket`` are outside it; the host's network rules are the layer beneath.
"""

from __future__ import annotations

import importlib.abc
import socket
import sys
from datetime import datetime, timezone
from typing import Any, Callable

from no_prod_egress import EgressBlockedError, EgressGuard, normalize_host

REFUSED_NATIVE_MODULES = ("grpc", "pycurl")
_UNSET = object()


class NativeNetworkingRefused(EgressBlockedError, ImportError):
    """An import of a module whose networking the guard cannot see (an ImportError, so optional imports degrade)."""


def _host_text(host: Any) -> str | None:
    if host is None:
        return None
    if isinstance(host, (bytes, bytearray)):
        return bytes(host).decode("ascii", errors="replace")
    return str(host)


def _strip_scope(host: str) -> str:
    return normalize_host(host.split("%", 1)[0])


class _RefuseNativeNetworking(importlib.abc.MetaPathFinder):
    def __init__(self, process: "ProcessGuard") -> None:
        self.process = process

    def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
        root = fullname.split(".", 1)[0]
        if root in REFUSED_NATIVE_MODULES:
            self.process.refuse_native(root)
        return None


class ProcessGuard:
    def __init__(self, guard: EgressGuard) -> None:
        self.guard = guard
        self.resolved: set[str] = set()
        self.refused_imports: list[str] = []
        self._restore: list[Callable[[], None]] = []
        self.installed = False

    # The rule, applied to a host name or an address.
    def admit(self, host: Any, via: str) -> None:
        text = _host_text(host)
        if text is None or text == "":
            return  # a passive lookup or an unspecified local address: nothing leaves the host
        value = _strip_scope(text)
        if value in self.resolved:
            return
        self.guard.check(value, via)

    def admit_address(self, address: Any, via: str) -> None:
        if isinstance(address, (str, bytes, bytearray)):
            return  # an AF_UNIX path: local
        if (
            isinstance(address, tuple)
            and address
            and isinstance(address[0], (str, bytes, bytearray))
        ):
            self.admit(address[0], via)

    def refuse_native(self, module: str) -> None:
        reason = "native networking the egress guard cannot see (refused at import)"
        self._trip(module, reason)
        self.refused_imports.append(module)
        raise NativeNetworkingRefused(f"(import {module})", reason)

    def _trip(self, module: str, reason: str) -> None:
        self.guard.trips.append(
            {
                "host": f"(import {module})",
                "reason": reason,
                "via": "import",
                "at": datetime.now(timezone.utc).isoformat(),
            }
        )

    # Patching.
    def _patch_attr(self, owner: Any, name: str, wrapper: Callable[[Any], Any]) -> None:
        had = name in vars(owner)
        original = getattr(owner, name)
        setattr(owner, name, wrapper(original))
        self._restore.append(
            lambda: setattr(owner, name, original) if had else delattr(owner, name)
        )

    def install(self) -> "ProcessGuard":
        if self.installed:
            return self
        for module in REFUSED_NATIVE_MODULES:
            if module in sys.modules:
                self._trip(module, "imported before the guard was armed")
        process = self

        def lookup(
            name_of: Callable[..., Any], via: str, remember: Callable[[Any], list[str]]
        ) -> Callable[[Any], Any]:
            def wrap(original: Any) -> Any:
                def guarded(*args: Any, **kwargs: Any) -> Any:
                    host = name_of(*args, **kwargs)
                    process.admit(host, via)
                    result = original(*args, **kwargs)
                    if _host_text(host):
                        process.resolved.update(
                            _strip_scope(a)
                            for a in remember(result)
                            if isinstance(a, str)
                        )
                    return result

                return guarded

            return wrap

        first = lambda host=None, *_, **__: host  # noqa: E731
        self._patch_attr(
            socket,
            "getaddrinfo",
            lookup(first, "socket.getaddrinfo", lambda r: [entry[4][0] for entry in r]),
        )
        self._patch_attr(
            socket,
            "gethostbyname",
            lookup(first, "socket.gethostbyname", lambda r: [r]),
        )
        self._patch_attr(
            socket,
            "gethostbyname_ex",
            lookup(first, "socket.gethostbyname_ex", lambda r: list(r[2])),
        )

        def connecting(via: str) -> Callable[[Any], Any]:
            def wrap(original: Any) -> Any:
                def guarded(sock: Any, address: Any) -> Any:
                    process.admit_address(address, via)
                    return original(sock, address)

                return guarded

            return wrap

        self._patch_attr(socket.socket, "connect", connecting("socket.connect"))
        self._patch_attr(socket.socket, "connect_ex", connecting("socket.connect_ex"))

        def sendto(original: Any) -> Any:
            def guarded(sock: Any, data: Any, *rest: Any) -> Any:
                if rest:
                    process.admit_address(rest[-1], "socket.sendto")
                return original(sock, data, *rest)

            return guarded

        self._patch_attr(socket.socket, "sendto", sendto)
        finder = _RefuseNativeNetworking(self)
        sys.meta_path.insert(0, finder)
        self._restore.append(
            lambda: sys.meta_path.remove(finder) if finder in sys.meta_path else None
        )
        self.installed = True
        return self

    def uninstall(self) -> None:
        while self._restore:
            self._restore.pop()()
        self.installed = False

    def describe(self) -> dict[str, Any]:
        return {
            "armed": self.installed,
            "patched": [
                "socket.getaddrinfo",
                "socket.gethostbyname",
                "socket.gethostbyname_ex",
                "socket.socket.connect",
                "socket.socket.connect_ex",
                "socket.socket.sendto",
            ],
            "refusedNativeModules": list(REFUSED_NATIVE_MODULES),
            "refusedImports": list(self.refused_imports),
        }


def install_process_guard(guard: EgressGuard) -> ProcessGuard:
    return ProcessGuard(guard).install()
