"""``futureagi-py sandbox mcp`` against a real sandbox API, through the official MCP client over stdio.

Opt-in like every live test: it runs only when ``FI_E2E_REQUIRED`` is set (any non-empty value), and
then a missing setting fails instead of skipping. It needs the ``sandbox-mcp`` extra, ``OMEGA_BASE_URL``
and one credential (``FI_API_KEY`` + ``FI_SECRET_KEY``, or ``FUTUREAGI_OMEGA_API_KEY`` for an EE on
loopback) in the environment, which the server process inherits. It lists the tools, then creates a
sandbox, runs ``echo hi``, writes, reads and lists a file, and deletes it; a second session creates a
sandbox and disconnects without deleting it, and the sandbox must be gone after the server exits."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("FI_E2E_REQUIRED"), reason="live sandbox tests require FI_E2E_REQUIRED=1"
)

TOOLS = {"sandbox_list", "sandbox_create", "sandbox_exec", "sandbox_read_file", "sandbox_write_file",
         "sandbox_list_files", "sandbox_delete"}


def _command() -> tuple:
    """The console script when installed, else this interpreter running the CLI module."""
    script = shutil.which("futureagi-py")
    if script:
        return script, ["sandbox", "mcp"]
    return sys.executable, ["-m", "fi._cli.main", "sandbox", "mcp"]


def _settings() -> dict:
    env = dict(os.environ)
    if not env.get("OMEGA_BASE_URL"):
        pytest.fail("FI_E2E_REQUIRED is set but OMEGA_BASE_URL is not")
    keys = env.get("FI_API_KEY") and env.get("FI_SECRET_KEY")
    if not keys and not env.get("FUTUREAGI_OMEGA_API_KEY"):
        pytest.fail("FI_E2E_REQUIRED is set but no sandbox credential is")
    return env


def _data(result) -> dict:
    """A tool result's JSON: the structured content when given, else the first text block."""
    assert not (getattr(result, "isError", False) or getattr(result, "is_error", False)), result
    structured = getattr(result, "structuredContent", None) or getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured.get("result", structured) if set(structured) == {"result"} else structured
    return json.loads(result.content[0].text)


async def _session(body):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    command, args = _command()
    params = StdioServerParameters(command=command, args=args, env=_settings())
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await body(session)


def test_live_mcp_tools_end_to_end():
    pytest.importorskip("mcp")

    async def body(session):
        listed = await session.list_tools()
        assert {tool.name for tool in listed.tools} == TOOLS
        created = _data(await session.call_tool("sandbox_create", {"name": "mcp-live"}))
        ident = created["id"]
        try:
            ran = _data(await session.call_tool("sandbox_exec", {"sandbox_id": ident, "command": "echo hi"}))
            assert ran["exit_code"] == 0 and ran["stdout"] == "hi\n"
            wrote = _data(await session.call_tool(
                "sandbox_write_file", {"sandbox_id": ident, "path": "live/notes.txt", "content": "hello"}))
            assert wrote["bytes"] == 5
            read = _data(await session.call_tool("sandbox_read_file", {"sandbox_id": ident, "path": "live/notes.txt"}))
            assert read["encoding"] == "utf8" and read["content"] == "hello"
            listed_files = _data(await session.call_tool("sandbox_list_files", {"sandbox_id": ident, "path": "live"}))
            assert [entry["name"] for entry in listed_files["entries"]] == ["notes.txt"]
        finally:
            deleted = _data(await session.call_tool("sandbox_delete", {"sandbox_id": ident}))
        assert deleted["id"] == ident

    asyncio.run(_session(body))


def test_live_mcp_deletes_what_it_created_on_exit():
    pytest.importorskip("mcp")

    async def create(session):
        return _data(await session.call_tool("sandbox_create", {"name": "mcp-live-exit"}))["id"]

    async def look(session):
        return _data(await session.call_tool("sandbox_list", {}))["sandboxes"]

    ident = asyncio.run(_session(create))  # the client disconnects; the server deletes it
    rows = asyncio.run(_session(look))
    assert all(row["id"] != ident or row["state"] == "destroyed" for row in rows)
