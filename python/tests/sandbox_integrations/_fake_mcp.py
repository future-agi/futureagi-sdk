"""A fake ``mcp`` package (the 2.x layout: ``mcp.server.MCPServer`` and
``mcp.server.mcpserver.exceptions.ToolError``) for the MCP server tests, so they run where ``mcp`` is
not installed, or is an older version. The fake server records each ``add_tool`` and each
``run_stdio_async`` call; ``on_run`` (a coroutine function taking the server) stands in for a client
during the run.

The server module binds the framework when it is imported, so each test imports it afresh:
:func:`isolate_server` forgets it (in ``sys.modules`` and on its package) and returns a function that
puts back what was there."""

from __future__ import annotations

import importlib
import inspect
import sys
import types
from typing import Any, Callable, Dict, List, Optional

PACKAGE = "fi.sandbox_integrations.mcp_server"
SERVER = PACKAGE + "._server"
#: Every module either branch of the server's import shim reads.
MCP_MODULES = (
    "mcp",
    "mcp.server",
    "mcp.server.mcpserver",
    "mcp.server.mcpserver.exceptions",
    "mcp.server.fastmcp",
    "mcp.server.fastmcp.exceptions",
)


class ToolError(Exception):
    """The fake framework's tool error: what the model would read as an error result."""


class FakeMCPServer:
    instances: List["FakeMCPServer"] = []
    on_run: Optional[Callable[["FakeMCPServer"], Any]] = None

    def __init__(self, name: Optional[str] = None, *, instructions: Optional[str] = None, **kwargs: Any) -> None:
        self.name = name
        self.instructions = instructions
        self.kwargs = kwargs
        self.tools: Dict[str, Callable[..., Any]] = {}
        self.descriptions: Dict[str, Optional[str]] = {}
        self.runs = 0
        type(self).instances.append(self)

    def add_tool(self, fn: Callable[..., Any], name: Optional[str] = None,
                 description: Optional[str] = None, **kwargs: Any) -> None:
        assert inspect.iscoroutinefunction(fn)
        self.tools[name or fn.__name__] = fn
        self.descriptions[name or fn.__name__] = description

    def parameters(self, name: str) -> List[str]:
        return list(inspect.signature(self.tools[name]).parameters)

    async def run_stdio_async(self) -> None:
        self.runs += 1
        hook = type(self).on_run
        if hook is not None:
            await hook(self)


def isolate_server() -> Callable[[], None]:
    """Forget the imported server module; the returned function restores what was there."""
    package = importlib.import_module(PACKAGE)
    saved_module = sys.modules.pop(SERVER, None)
    saved_attribute = package.__dict__.pop("_server", None)

    def restore() -> None:
        sys.modules.pop(SERVER, None)
        package.__dict__.pop("_server", None)
        if saved_module is not None:
            sys.modules[SERVER] = saved_module
        if saved_attribute is not None:
            package._server = saved_attribute

    return restore


def install(monkeypatch: Any) -> type:
    """Put the fake in ``sys.modules`` for this test; returns a fresh server class whose
    ``instances`` lists the servers built in this test."""
    server_class = type("MCPServer", (FakeMCPServer,), {"instances": [], "on_run": None})
    modules = {name: types.ModuleType(name) for name in MCP_MODULES[:4]}
    modules["mcp"].server = modules["mcp.server"]
    modules["mcp.server"].MCPServer = server_class
    modules["mcp.server"].mcpserver = modules["mcp.server.mcpserver"]
    modules["mcp.server.mcpserver"].MCPServer = server_class
    modules["mcp.server.mcpserver"].exceptions = modules["mcp.server.mcpserver.exceptions"]
    modules["mcp.server.mcpserver.exceptions"].ToolError = ToolError
    for name in MCP_MODULES:
        monkeypatch.setitem(sys.modules, name, modules.get(name))
    return server_class


def block(monkeypatch: Any) -> None:
    """Make ``mcp`` impossible to import for this test, whatever is installed."""
    for name in MCP_MODULES:
        monkeypatch.setitem(sys.modules, name, None)
