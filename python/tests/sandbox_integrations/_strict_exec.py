"""The sandbox API's path rules, on the frozen-OpenAPI mock server.

The exec route takes ``cwd`` relative to ``/workspace`` (absent or empty: ``/workspace`` itself) and answers
400 for an absolute folder, or one with a ``.`` or ``..`` segment, as the sandbox service does (conformance
case ``sandboxes.exec.absolute-cwd``). The files routes take every path relative to ``/workspace`` as well:
a leading slash, a backslash or a NUL gets 400 ``validation`` "<field> must be a workspace-relative path.",
a ``.`` or ``..`` segment gets 400 ``validation`` too, and the root (an empty path, or none) is taken by the
listing only. A path in the URL loses its leading slash on the way (``/workspace/a`` is sent as
``workspace/a``, which the service would put at ``/workspace/workspace/a``), so a first folder named
``workspace`` there is refused as the absolute path it was. With the rules in front of a mock server, code
that sends a wrong path fails its test instead of passing against a server that takes anything.

:func:`enforce_everywhere` turns the rules on for every mock server made during a test (the conftest in this
folder does that for each test here); :func:`strict` turns them on for one server, before any transport or
client is built from it.
"""

from __future__ import annotations

import functools
import json
import re
from typing import Any, Callable, Optional
from urllib.parse import unquote

import httpx

from tests.platform._sandbox_mock import MockServer, Route, Seen, error

EXEC_ROUTE = "sandboxes.commands.run"
LIST_ROUTE = "sandboxes.files.list"
MOVE_ROUTE = "sandboxes.files.rename"
#: The files routes that carry the path in the URL (``files/{path}``, ``download/{path}`` ...).
URL_PATH_ROUTES = frozenset({"sandboxes.files.read", "sandboxes.files.write", "sandboxes.files.remove",
                             "sandboxes.files.download", "sandboxes.files.upload", "sandboxes.files.makeDir"})

Handler = Callable[[MockServer, httpx.Request], httpx.Response]


def _body(request: httpx.Request) -> Any:
    try:
        return json.loads(request.read() or b"{}")
    except ValueError:
        return None


def refused_cwd(request: httpx.Request) -> Optional[str]:
    """The ``cwd`` of an exec request body that the service refuses, else None."""
    body = _body(request)
    cwd = body.get("cwd") if isinstance(body, dict) else None
    if isinstance(cwd, str) and (cwd.startswith("/") or {".", ".."} & set(cwd.split("/"))):
        return cwd
    return None


def path_refusal(value: Any, field: str, root: bool = False) -> Optional[str]:
    """The service's refusal of one files path (``field`` names it in the message), else None."""
    if not isinstance(value, str) or value.startswith("/") or "\\" in value or "\x00" in value:
        return f"{field} must be a workspace-relative path."
    parts = [part for part in value.split("/") if part]
    if "." in parts or ".." in parts:
        return (f'{field} must not contain "." or ".." path segments. Use a path relative to /workspace '
                "without those segments; use an empty string for the root only where this operation "
                "permits it.")
    if not parts and not root:
        return f"{field} must name a file inside the sandbox workspace."
    return None


def _url_path(route: Route, request: httpx.Request) -> str:
    """The decoded ``{path}`` of a files request whose route carries it in the URL."""
    raw = request.url.raw_path.decode("ascii").split("?", 1)[0]
    prefix = re.sub(r"\\\{[^}]+\\\}", "[^/]+", re.escape(route.template.split("{path}", 1)[0]))
    found = re.search(prefix, raw)
    tail = raw[found.end():] if found else raw
    return "/".join(unquote(part) for part in tail.split("/"))


def refused_file_path(route: Route, request: httpx.Request) -> Optional[str]:
    """The service's refusal of a files request's path, else None (not a files route: None)."""
    if route.name == LIST_ROUTE:
        value = request.url.params.get("path")
        return None if value is None else path_refusal(value, "path", root=True)
    if route.name == MOVE_ROUTE:
        body = _body(request)
        body = body if isinstance(body, dict) else {}
        return path_refusal(body.get("from"), '"from"') or path_refusal(body.get("to"), '"to"')
    if route.name in URL_PATH_ROUTES:
        value = _url_path(route, request)
        if value.split("/", 1)[0] == "workspace":  # /workspace/... with its leading slash dropped
            return "path must be a workspace-relative path."
        return path_refusal(value, "path")
    return None


def _refusal(route: Route, request: httpx.Request) -> Optional[httpx.Response]:
    if route.name == EXEC_ROUTE:
        cwd = refused_cwd(request)
        if cwd is None:
            return None
        return error(400, "validation", message=f"cwd is relative to the workspace; {cwd!r} is refused",
                     detail={"reason": "invalid_cwd", "field": "cwd"})
    message = refused_file_path(route, request)
    return None if message is None else error(400, "validation", message=message)


def _with_rule(answer: Handler) -> Handler:
    """``answer`` (a ``MockServer.handler``) with the exec and files path rules in front of it. A refused
    request is still recorded in ``seen``, so tests that count requests see it."""

    def handler(server: MockServer, request: httpx.Request) -> httpx.Response:
        route = server.route(request)
        refused = _refusal(route, request)
        if refused is None:
            return answer(server, request)
        server.seen.append(Seen(route.name, request, request.read()))
        return refused

    return handler


def enforce_everywhere(monkeypatch: Any) -> None:
    """Every mock server made or used during this test answers exec and files as the service does."""
    monkeypatch.setattr(MockServer, "handler", _with_rule(MockServer.handler))


def strict(server: MockServer) -> MockServer:
    """``server`` answers exec and files as the service does; returns it."""
    server.handler = functools.partial(_with_rule(type(server).handler), server)  # type: ignore[method-assign]
    return server
