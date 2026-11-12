"""The sandbox API's rule for a command's folder, on the frozen-OpenAPI mock server.

The exec route takes ``cwd`` relative to ``/workspace`` (absent or empty: ``/workspace`` itself) and answers
400 for an absolute folder, or one with a ``.`` or ``..`` segment, as the sandbox service does (conformance
case ``sandboxes.exec.absolute-cwd``). With the rule in front of a mock server, code that sends a wrong
folder fails its test instead of passing against a server that takes anything.

:func:`enforce_everywhere` turns the rule on for every mock server made during a test (the conftest in this
folder does that for each test here); :func:`strict` turns it on for one server, before any transport or
client is built from it.
"""

from __future__ import annotations

import functools
import json
from typing import Any, Callable, Optional

import httpx

from tests.platform._sandbox_mock import MockServer, Seen, error

EXEC_ROUTE = "sandboxes.commands.run"

Handler = Callable[[MockServer, httpx.Request], httpx.Response]


def refused_cwd(request: httpx.Request) -> Optional[str]:
    """The ``cwd`` of an exec request body that the service refuses, else None."""
    try:
        body: Any = json.loads(request.read() or b"{}")
    except ValueError:
        return None
    cwd = body.get("cwd") if isinstance(body, dict) else None
    if isinstance(cwd, str) and (cwd.startswith("/") or {".", ".."} & set(cwd.split("/"))):
        return cwd
    return None


def _with_rule(answer: Handler) -> Handler:
    """``answer`` (a ``MockServer.handler``) with the exec route's folder rule in front of it. A refused
    request is still recorded in ``seen``, so tests that count requests see it."""

    def handler(server: MockServer, request: httpx.Request) -> httpx.Response:
        route = server.route(request)
        cwd = refused_cwd(request) if route.name == EXEC_ROUTE else None
        if cwd is None:
            return answer(server, request)
        server.seen.append(Seen(route.name, request, request.read()))
        return error(400, "validation", message=f"cwd is relative to the workspace; {cwd!r} is refused",
                     detail={"reason": "invalid_cwd", "field": "cwd"})

    return handler


def enforce_everywhere(monkeypatch: Any) -> None:
    """Every mock server made or used during this test answers exec as the service does."""
    monkeypatch.setattr(MockServer, "handler", _with_rule(MockServer.handler))


def strict(server: MockServer) -> MockServer:
    """``server`` answers exec as the service does; returns it."""
    server.handler = functools.partial(_with_rule(type(server).handler), server)  # type: ignore[method-assign]
    return server
