"""An MCP server with Future AGI sandbox tools (``pip install "futureagi[sandbox-mcp]"``).

Run it as a command (credentials from its environment)::

    futureagi-py sandbox mcp

or build it in code::

    from fi.sandbox_integrations.mcp_server import SandboxTools, build_server

``SandboxTools`` (the tool bodies, over ``client.sandboxes``) needs no MCP package; ``build_server`` and
``serve_stdio`` load ``mcp`` when first used, and raise :class:`fi.errors.MissingExtraError` with the
install line when it is missing. The module path and the extra name are provisional. See ``README.md``.
"""

from __future__ import annotations

from typing import Any

from ._tools import DEFAULT_MAX_OUTPUT_CHARS, SandboxTools, SandboxToolError

_FROM_SERVER = ("SERVER_NAME", "build_server", "serve_stdio")


def __getattr__(name: str) -> Any:
    if name in _FROM_SERVER:
        from . import _server

        return getattr(_server, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "DEFAULT_MAX_OUTPUT_CHARS",
    "SERVER_NAME",
    "SandboxToolError",
    "SandboxTools",
    "build_server",
    "serve_stdio",
]
