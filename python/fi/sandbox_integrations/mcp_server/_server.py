"""The sandbox tools on an MCP server, served over standard input and output.

The server class is the official MCP Python SDK's: ``MCPServer`` (``mcp`` 2.x) or ``FastMCP`` (``mcp``
1.x), which both take ``add_tool(fn, name=, description=)`` and ``run_stdio_async()``. Without ``mcp``,
importing this module raises :class:`fi.errors.MissingExtraError`, whose message is the install line.

A refused or failed call is raised to the framework as its ``ToolError`` with the text of
:class:`~fi.sandbox_integrations.mcp_server._tools.SandboxToolError`: the client gets a tool result marked
as an error that the model can read (MCP 2.x withholds the text of any other exception).

This module has no ``from __future__ import annotations``: the framework reads each tool's parameter
types from its annotations to build the tool's input schema.
"""

import asyncio
import signal
import sys
from typing import Any, Awaitable, Callable, Dict, List, Literal, Optional, Tuple

from fi.errors import MissingExtraError

from ._tools import SandboxTools, SandboxToolError

SERVER_NAME = "futureagi-sandbox"
INSTRUCTIONS = (
    "Future AGI sandboxes: isolated Linux computers that run shell commands and keep files under "
    "/workspace until deleted. Create one with sandbox_create (or use the one this server is pinned "
    "to), run commands with sandbox_exec, and move files with sandbox_write_file and "
    "sandbox_read_file. A non-zero exit code is a result, not an error."
)
#: The line that installs ``mcp``.
INSTALL_LINE = 'pip install "futureagi[sandbox-mcp]"'
#: The oldest and newest Python the ``sandbox-mcp`` extra installs ``mcp`` on (its pyproject.toml marker).
SUPPORTED_PYTHONS = ((3, 10), (3, 13))


def missing_mcp(version: Tuple[Any, ...]) -> MissingExtraError:
    """The error for a missing ``mcp`` on Python ``version``: the install line, and on a Python newer than the
    extra covers (3.14 or later), that the extra installs nothing there."""
    low, high = SUPPORTED_PYTHONS
    span = f"Python {low[0]}.{low[1]} to {high[0]}.{high[1]}"
    if tuple(version[:2]) > high:
        message = (f"mcp is not installed: the sandbox-mcp extra installs it on {span} only, and this is "
                   f"Python {version[0]}.{version[1]}. Use {span}, then run: {INSTALL_LINE}")
    else:
        message = f"mcp is not installed. Run: {INSTALL_LINE} (the extra supports {span})"
    return MissingExtraError(message, extra="sandbox-mcp", module="mcp")


def _framework() -> Tuple[Any, Any]:
    """The MCP server class and its ``ToolError``, from ``mcp`` 2.x, else 1.x."""
    try:
        from mcp.server import MCPServer
        from mcp.server.mcpserver.exceptions import ToolError

        return MCPServer, ToolError
    except ImportError:
        pass
    try:
        from mcp.server.fastmcp import FastMCP
        from mcp.server.fastmcp.exceptions import ToolError as LegacyToolError

        return FastMCP, LegacyToolError
    except ImportError:
        raise missing_mcp(tuple(sys.version_info)) from None


ServerClass, ToolError = _framework()

DESCRIPTIONS = {
    "sandbox_list": "List your sandboxes and the workspace's sandbox limits (templates, sizes, the most "
                    "active sandboxes, and caps.exec: the default and longest command time limits).",
    "sandbox_create": "Create an isolated Linux sandbox. It keeps files in /workspace until deleted. "
                      "Every argument is optional: name (1 to 120 bytes), template and size (sandbox_list "
                      "shows the choices), idle_ttl_seconds (hibernate after that long without activity). "
                      "Returns its id.",
    "sandbox_exec": "Run a shell command in a sandbox and wait for it to end (pipes and && work). "
                    "cwd is the folder to run in, relative to /workspace (src means /workspace/src; left "
                    "out, /workspace itself); an absolute path under /workspace also works, and a folder "
                    "outside it is refused (cd inside the command instead). "
                    "timeout_seconds defaults to the workspace's default and is kept between 1 and the "
                    "workspace's longest limit (sandbox_list shows both). Returns the whole exit record: "
                    "exit_code (None after a signal or when it could not start), signal, timed_out, "
                    "cancelled, error, and the last characters of stdout and stderr (stdout_clipped and "
                    "stderr_clipped say when earlier output was dropped). Pass plain values to the "
                    "command inside it (export NAME=value; ...), never credentials.",
    "sandbox_read_file": "Read a file from a sandbox: UTF-8 text as it is, any other file as base64 "
                         "(encoding says which). max_bytes reads at most that many bytes; truncated "
                         "says the file is longer.",
    "sandbox_write_file": "Write a file in a sandbox; missing folders are created. encoding is utf8 "
                          "(content is the text) or base64 (content is the bytes, base64-encoded).",
    "sandbox_list_files": "List a folder in a sandbox (default: the top folder of its files): each "
                          "entry's name, size, mode and whether it is a folder.",
    "sandbox_delete": "Delete a sandbox and its files for good.",
}
#: The tools pinned mode keeps (it hands an agent one sandbox and no power to create or delete).
PINNED_TOOLS = ("sandbox_exec", "sandbox_read_file", "sandbox_write_file", "sandbox_list_files")


async def _call(pending: Awaitable[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        return await pending
    except SandboxToolError as error:
        raise ToolError(str(error)) from None


def tool_functions(tools: SandboxTools) -> List[Tuple[str, Callable[..., Any]]]:
    """``(name, coroutine function)`` for each tool to register, with the parameters the model sees."""

    async def sandbox_list() -> Dict[str, Any]:
        return await _call(tools.sandbox_list())

    async def sandbox_create(
        name: Optional[str] = None,
        template: Optional[str] = None,
        size: Optional[str] = None,
        idle_ttl_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        return await _call(tools.sandbox_create(name, template, size, idle_ttl_seconds))

    async def sandbox_exec(
        command: str,
        sandbox_id: Optional[str] = None,
        cwd: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        return await _call(tools.sandbox_exec(command, sandbox_id, cwd, timeout_seconds))

    async def sandbox_read_file(
        path: str, sandbox_id: Optional[str] = None, max_bytes: Optional[int] = None
    ) -> Dict[str, Any]:
        return await _call(tools.sandbox_read_file(path, sandbox_id, max_bytes))

    async def sandbox_write_file(
        path: str,
        content: str,
        sandbox_id: Optional[str] = None,
        encoding: Literal["utf8", "base64"] = "utf8",
    ) -> Dict[str, Any]:
        return await _call(tools.sandbox_write_file(path, content, sandbox_id, encoding))

    async def sandbox_list_files(path: str = ".", sandbox_id: Optional[str] = None) -> Dict[str, Any]:
        return await _call(tools.sandbox_list_files(path, sandbox_id))

    async def sandbox_delete(sandbox_id: str) -> Dict[str, Any]:
        return await _call(tools.sandbox_delete(sandbox_id))

    every = (sandbox_list, sandbox_create, sandbox_exec, sandbox_read_file, sandbox_write_file,
             sandbox_list_files, sandbox_delete)
    keep = PINNED_TOOLS if tools.pinned is not None else tuple(DESCRIPTIONS)
    return [(fn.__name__, fn) for fn in every if fn.__name__ in keep]


def build_server(tools: SandboxTools, *, name: str = SERVER_NAME) -> Any:
    """An MCP server (``MCPServer``, or ``FastMCP`` on ``mcp`` 1.x) with the sandbox tools; in pinned
    mode only the exec and file tools."""
    instructions = INSTRUCTIONS
    if tools.pinned is not None:
        instructions += f" This server serves only sandbox {tools.pinned}: leave sandbox_id out."
    server = ServerClass(name, instructions=instructions)
    for tool_name, fn in tool_functions(tools):
        server.add_tool(fn, name=tool_name, description=DESCRIPTIONS[tool_name])
    return server


#: After SIGTERM, how long the tool calls in flight get to end before the cleanup starts.
STOP_GRACE_SECONDS = 0.1


def _note(text: str) -> None:
    print(text, file=sys.stderr, flush=True)


def _on_signal(loop: asyncio.AbstractEventLoop, signum: int, callback: Callable[[], None]) -> Callable[[], None]:
    """Run ``callback`` in ``loop`` when signal ``signum`` arrives; returns the function that puts the
    signal's previous handling back. Where a loop cannot take signals (Windows, or a thread other than
    the main one) nothing is installed and the signal keeps its usual effect."""
    previous = signal.getsignal(signum)
    try:
        loop.add_signal_handler(signum, callback)
    except (NotImplementedError, RuntimeError, ValueError):
        return lambda: None

    def restore() -> None:
        loop.remove_signal_handler(signum)
        if previous is not None:
            signal.signal(signum, previous)

    return restore


async def _finish(tools: SandboxTools, keep: bool) -> None:
    if keep:
        for sandbox_id in sorted(tools.created):
            _note(f"kept sandbox {sandbox_id} (--keep); delete it when you are done")
        return
    for sandbox_id in await tools.cleanup():
        _note(f"deleted sandbox {sandbox_id}, which this server created")
    for sandbox_id, text in tools.cleanup_failures:
        _note(f"{text} (sandbox {sandbox_id} was not deleted)")


async def serve_stdio(tools: SandboxTools, *, keep: bool = False, name: str = SERVER_NAME) -> None:
    """Serve over standard input and output until the client disconnects, the process gets SIGTERM, or
    the task is cancelled; then delete the sandboxes this server created unless ``keep``.

    An MCP client stops a stdio server by closing its stdin and, if the server is still running after
    a short grace period (2 s in the official MCP SDK), sending SIGTERM, then killing it. SIGTERM while
    serving stops serving and runs the same cleanup, and returns normally; SIGTERM during the cleanup
    does not interrupt it. :meth:`SandboxTools.cleanup` sends the deletes together, so the cleanup
    takes about as long as one delete. Notes go to stderr: stdout carries the protocol only."""
    server = build_server(tools, name=name)
    loop = asyncio.get_running_loop()
    serving = asyncio.ensure_future(server.run_stdio_async())
    serving.add_done_callback(lambda task: task.cancelled() or task.exception())
    stop = loop.create_future()
    noted: List[bool] = []

    def on_sigterm() -> None:
        if not serving.done():
            if not stop.done():
                stop.set_result(None)
        elif not keep and not noted:
            noted.append(True)
            _note("SIGTERM: stopping once the sandboxes this server created are deleted")

    restore = _on_signal(loop, signal.SIGTERM, on_sigterm)
    try:
        await asyncio.wait({serving, stop}, return_when=asyncio.FIRST_COMPLETED)
        if serving.done():
            serving.result()  # what ended serving: an error or a cancel is raised after the cleanup
        else:
            # A pending read of stdin can hold the cancel until stdin closes: wait briefly, not for it.
            serving.cancel()
            await asyncio.wait({serving}, timeout=STOP_GRACE_SECONDS)
    finally:
        if not serving.done():
            serving.cancel()
        try:
            await _finish(tools, keep)
        finally:
            restore()


__all__ = ["SERVER_NAME", "PINNED_TOOLS", "build_server", "serve_stdio", "tool_functions"]
