"""Shared paths, loaders and the no-egress guard for the platform gate tests."""

from __future__ import annotations

import importlib.util
import json
import socket
import typing
from pathlib import Path
from types import ModuleType

import pytest

REPO = Path(__file__).resolve().parents[3]
PLATFORM = REPO / "openapi" / "platform"
SCOPED = PLATFORM / "generated" / "futureagi-platform.openapi.json"
TS_POLICY = REPO / "typescript/futureagi/src/generated/platform/policy.gen.ts"
METHODS = ("get", "post", "put", "patch", "delete")


def load(name: str, relative: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict[str, typing.Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def operations(
    doc: dict[str, typing.Any]
) -> dict[str, tuple[str, dict[str, typing.Any]]]:
    out = {}
    for item in doc["paths"].values():
        for method in METHODS:
            if method in item:
                sdk = item[method]["x-omega-sdk"]
                out[f"{sdk['family']}.{sdk['method']}"] = (method.upper(), item[method])
    return out


def routes(
    doc: dict[str, typing.Any]
) -> dict[str, tuple[str, str, dict[str, typing.Any]]]:
    """``{sdk name: (METHOD, path template, operation)}`` for every operation of a document."""
    out = {}
    for route, item in doc["paths"].items():
        for method in METHODS:
            if method in item:
                sdk = item[method]["x-omega-sdk"]
                key = f"{sdk['family']}.{sdk['method']}"
                out[key] = (method.upper(), route, item[method])
    return out


def spec_retry_class(method: str, op: dict[str, typing.Any]) -> str:
    """The retry class the contract implies, read from the operation itself (the four classes of ``fi._core.policy``)."""
    if op.get("x-omega-idempotent") is True:
        durable = (op.get("x-omega-idempotency") or {}).get("durable")
        return "keyed-not-durable" if durable is False else "keyed"
    return "http-idempotent" if method in ("GET", "PUT", "DELETE") else "unsafe"


def guard_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make any connection outside loopback fail the test (the gates read files only)."""
    real_connect = socket.socket.connect

    def guarded(self: socket.socket, address: typing.Any) -> typing.Any:
        host = address[0] if isinstance(address, tuple) else str(address)
        if host not in ("127.0.0.1", "::1", "localhost") and not str(
            address
        ).startswith("/"):
            raise AssertionError(f"platform gates must not connect to {address!r}")
        return real_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", guarded)
