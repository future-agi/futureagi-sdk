"""``futureagi-py sandbox mcp``: a sub-command of the one ``sandbox`` group (no plugin entry of its
own), ``--help`` without ``mcp`` installed, exit 3 with the install line when ``mcp`` is missing (and on
Python 3.14 or later, a message naming the Pythons the extra covers), exit 2
on stderr for a setup problem, the tools it registers (all seven, or four when pinned), serving stdio
and deleting what it created on exit (unless ``--keep``), also when stopped by SIGTERM or a cancel and
when a SIGTERM arrives during the deletes, tool errors handed to the framework as its ``ToolError``, and
nothing on stdout from the command itself. ``mcp`` is faked (``_fake_mcp``); the sandbox API is the
frozen-OpenAPI mock on a loopback EE. Fake credentials only."""

from __future__ import annotations

import asyncio
import signal
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from fi._cli import main as cli_main
from fi._cli import registry
from tests.platform._sandbox_cli_support import (  # noqa: F401 (registers the server fixture)
    OTHER,
    SECRETS,
    answer,
    exec_body,
    names,
    no_secret,
    record,
    refuse,
    run,
    server_fixture,
)
from tests.platform._sandbox_mock import EXIT0, FAKE_KEY, FAKE_SECRET, SBX, api

from . import _fake_mcp

ALL_TOOLS = {
    "sandbox_list": [],
    "sandbox_create": ["name", "template", "size", "idle_ttl_seconds"],
    "sandbox_exec": ["command", "sandbox_id", "cwd", "timeout_seconds"],
    "sandbox_read_file": ["path", "sandbox_id", "max_bytes"],
    "sandbox_write_file": ["path", "content", "sandbox_id", "encoding"],
    "sandbox_list_files": ["path", "sandbox_id"],
    "sandbox_delete": ["sandbox_id"],
}
PINNED = ("sandbox_exec", "sandbox_read_file", "sandbox_write_file", "sandbox_list_files")
INSTALL = 'pip install "futureagi[sandbox-mcp]"'


@pytest.fixture(name="fresh")
def fresh_fixture():
    """Each test imports the server module afresh (it binds the framework on import)."""
    restore = _fake_mcp.isolate_server()
    yield
    restore()


@pytest.fixture(name="fake")
def fake_fixture(monkeypatch, fresh):
    return _fake_mcp.install(monkeypatch)


def built(fake):
    assert len(fake.instances) == 1
    return fake.instances[0]


def test_help_works_without_mcp_installed(server, monkeypatch, fresh, capsys):
    _fake_mcp.block(monkeypatch)
    assert run("mcp", "--help") == 0
    out = capsys.readouterr().out
    for text in ("--sandbox", "--keep", "--max-output-chars", "--base-url", INSTALL, "claude mcp add", "stderr"):
        assert text in out, text
    assert run("--help") == 0
    assert "mcp" in capsys.readouterr().out
    assert _fake_mcp.SERVER not in sys.modules
    assert server.seen == []


def test_mcp_is_a_sub_command_of_the_one_sandbox_entry_point(server, capsys):
    """Replaces the second-plugin-entry tests: there is one entry point, ``sandbox``, and the
    sandbox group itself adds ``mcp``, so no load order or absent group can drop it."""
    assert "sandbox_mcp" not in registry.source_tree_groups()
    assert [ep.name for ep in registry.entry_points()] == ["sandbox"]
    parser = cli_main.build_parser(warn=lambda message: pytest.fail(message))
    args = parser.parse_args(["sandbox", "mcp", "--sandbox", SBX, "--keep"])
    assert args.sandbox == SBX and args.keep is True and args.max_output_chars == 20_000
    assert args.install_hint == INSTALL


def test_registering_the_group_imports_neither_mcp_nor_the_server():
    py_root = Path(__file__).resolve().parents[2]
    code = (
        f"import sys; sys.path.insert(0, {str(py_root)!r})\n"
        "import argparse, fi._cli.sandbox as g\n"
        "g.register(argparse.ArgumentParser(prog='futureagi-py').add_subparsers())\n"
        "print(sorted(m for m in sys.modules if m.split('.')[0] in ('mcp', 'httpx')\n"
        "             or m.startswith(('fi.sandbox', 'fi.sandbox_integrations'))))\n"
    )
    out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, check=True).stdout
    assert out.strip() == "[]", out


def test_missing_mcp_exits_3_with_install_hint(server, monkeypatch, fresh, capsys):
    _fake_mcp.block(monkeypatch)
    assert run("mcp") == 3
    captured = capsys.readouterr()
    assert captured.out == ""
    assert INSTALL in captured.err and captured.err.count("\n") == 1
    assert server.seen == []


@pytest.mark.parametrize("env,code", [
    ({"OMEGA_BASE_URL": None}, "missing_base_url"),
    ({"OMEGA_BASE_URL": "   "}, "missing_base_url"),
    ({"FUTUREAGI_OMEGA_API_KEY": None}, "missing_credentials"),
    ({"FI_API_KEY": FAKE_KEY, "FI_SECRET_KEY": FAKE_SECRET}, "mixed_credentials"),
    ({"OMEGA_BASE_URL": "http://sandbox.example.test"}, "insecure_sandbox_origin"),
    ({"OMEGA_BASE_URL": "https://sandbox.example.test"}, "custom_base_url_not_allowed"),
])
def test_missing_base_url_exits_2_with_empty_stdout(server, fake, monkeypatch, capsys, env, code):
    for name, value in env.items():
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)
    assert run("mcp") == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith(f"{code}: ")
    no_secret(captured.err)
    assert fake.instances == [] and server.seen == []


def test_base_url_flag_stands_in_for_the_environment(server, fake, monkeypatch, capsys):
    monkeypatch.delenv("OMEGA_BASE_URL")
    assert run("mcp", "--base-url", "http://127.0.0.1:8787") == 0
    assert built(fake).runs == 1 and capsys.readouterr().out == ""


def test_all_tools_are_registered_with_their_parameters(server, fake, capsys):
    assert run("mcp") == 0
    srv = built(fake)
    assert srv.name == "futureagi-sandbox" and srv.runs == 1
    assert {name: srv.parameters(name) for name in srv.tools} == ALL_TOOLS
    assert all(srv.descriptions[name] for name in srv.tools)
    assert "900" not in srv.descriptions["sandbox_exec"]  # the limit is the workspace's, read from caps
    assert "relative to /workspace" in srv.descriptions["sandbox_exec"]
    assert capsys.readouterr().out == ""


def test_exec_tool_sends_a_folder_under_the_workspace_relative_to_it(server, fake, capsys):
    server.on("sandboxes.getInfo", answer(200, json=record()))
    server.on("sandboxes.commands.run", exec_body(("exit", EXIT0)))
    seen = {}

    async def client(srv):
        seen["ran"] = await srv.tools["sandbox_exec"](command="pwd", sandbox_id=SBX, cwd="/workspace/src")
        with pytest.raises(_fake_mcp.ToolError) as caught:
            await srv.tools["sandbox_exec"](command="pwd", sandbox_id=SBX, cwd="/etc")
        seen["refused"] = str(caught.value)

    fake.on_run = client
    assert run("mcp") == 0
    assert seen["ran"]["exit_code"] == 0
    bodies = [s.json() for s in server.seen if s.name == "sandboxes.commands.run"]
    assert bodies == [{"command": "pwd", "cwd": "src"}]  # the refused one sent nothing
    assert seen["refused"].startswith("invalid_cwd: ")
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("version", [(3, 14, 0), (3, 15, 2, "final", 0)])
def test_missing_mcp_on_a_python_the_extra_skips_names_the_supported_range(fake, version):
    from fi.sandbox_integrations.mcp_server import _server

    error = _server.missing_mcp(version)
    text = str(error)
    assert "Python 3.10 to 3.13" in text and f"this is Python {version[0]}.{version[1]}" in text
    assert INSTALL in text and "\n" not in text
    assert error.extra == "sandbox-mcp" and error.install_hint == INSTALL


@pytest.mark.parametrize("version", [(3, 10, 0), (3, 13, 9)])
def test_missing_mcp_on_a_supported_python_gives_the_install_line(fake, version):
    from fi.sandbox_integrations.mcp_server import _server

    text = str(_server.missing_mcp(version))
    assert text.startswith(f"mcp is not installed. Run: {INSTALL}") and "Python 3.10 to 3.13" in text
    assert "this is Python" not in text


def test_pinned_mode_registers_four_tools(server, fake, capsys):
    server.on("sandboxes.getInfo", answer(200, json=record()))
    server.on("sandboxes.commands.run", exec_body(("stdout", {"data": "hi\n"}), ("exit", EXIT0)))
    seen = {}

    async def client(srv):
        seen["ran"] = await srv.tools["sandbox_exec"](command="echo hi")
        with pytest.raises(_fake_mcp.ToolError) as caught:
            await srv.tools["sandbox_exec"](command="ls", sandbox_id=OTHER)
        seen["refused"] = str(caught.value)

    fake.on_run = client
    assert run("mcp", "--sandbox", SBX) == 0
    srv = built(fake)
    assert sorted(srv.tools) == sorted(PINNED)
    assert seen["ran"]["stdout"] == "hi\n" and seen["ran"]["exit_code"] == 0
    assert seen["refused"].startswith("pinned: ") and SBX in seen["refused"]
    assert SBX in srv.instructions
    assert "sandboxes.kill" not in names(server)  # pinned mode creates nothing, so deletes nothing
    assert capsys.readouterr().out == ""


def test_server_runs_stdio_and_cleans_up_on_exit(server, fake, capsys):
    server.on("sandboxes.create", answer(201, json=record()))
    server.on("sandboxes.kill", answer(200, json=record(state="destroyed")))

    async def client(srv):
        created = await srv.tools["sandbox_create"](name="job")
        assert created["id"] == SBX

    fake.on_run = client
    assert run("mcp") == 0
    assert built(fake).runs == 1
    assert names(server) == ["sandboxes.create", "sandboxes.kill"]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"deleted sandbox {SBX}" in captured.err


def test_cleanup_failure_is_reported_on_stderr_and_exit_is_still_0(server, fake, capsys):
    server.on("sandboxes.create", answer(201, json=record()))
    server.on("sandboxes.kill", refuse(403, "forbidden"))

    async def client(srv):
        await srv.tools["sandbox_create"]()

    fake.on_run = client
    assert run("mcp") == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "forbidden: " in captured.err and f"sandbox {SBX} was not deleted" in captured.err
    no_secret(captured.err)


def caught_signals(monkeypatch):
    """Stand in for the server's signal hook: ``handlers[signum]`` is the callback it would run, and
    ``restored`` counts the restores. No real signal is sent or installed."""
    from fi.sandbox_integrations.mcp_server import _server

    handlers, restored = {}, []

    def on_signal(loop, signum, callback):
        handlers[signum] = callback
        return lambda: restored.append(signum)

    monkeypatch.setattr(_server, "_on_signal", on_signal)
    return handlers, restored


def test_sigterm_while_serving_runs_the_cleanup_and_exits_0(server, fake, monkeypatch, capsys):
    server.on("sandboxes.create", answer(201, json=record()))
    server.on("sandboxes.kill", answer(200, json=record(state="destroyed")))
    handlers, restored = caught_signals(monkeypatch)

    async def client(srv):
        await srv.tools["sandbox_create"]()
        handlers[signal.SIGTERM]()
        await asyncio.sleep(3600)  # stands in for a read of stdin that never ends

    fake.on_run = client
    assert run("mcp") == 0
    assert names(server) == ["sandboxes.create", "sandboxes.kill"]
    assert restored == [signal.SIGTERM]
    captured = capsys.readouterr()
    assert captured.out == "" and f"deleted sandbox {SBX}" in captured.err


def test_sigterm_during_the_cleanup_does_not_stop_it(server, fake, monkeypatch, capsys):
    """The official MCP client closes stdin, waits 2 s, then sends SIGTERM: one that arrives while the
    deletes run must let them finish."""
    made = iter([SBX, OTHER])
    server.on("sandboxes.create", lambda request: httpx.Response(201, json=record(ident=next(made))))
    handlers, _restored = caught_signals(monkeypatch)

    def kill(request):
        handlers[signal.SIGTERM]()
        return httpx.Response(200, json=record(state="destroyed"))

    server.on("sandboxes.kill", kill)

    async def client(srv):
        await srv.tools["sandbox_create"]()
        await srv.tools["sandbox_create"]()

    fake.on_run = client
    assert run("mcp") == 0
    assert names(server).count("sandboxes.kill") == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"deleted sandbox {SBX}" in captured.err and f"deleted sandbox {OTHER}" in captured.err
    assert captured.err.count("SIGTERM: stopping once") == 1


def test_a_cancelled_serve_still_deletes_what_it_created(server, fake):
    server.on("sandboxes.create", answer(201, json=record()))
    server.on("sandboxes.kill", answer(200, json=record(state="destroyed")))
    from fi.sandbox_integrations.mcp_server import SandboxTools, _server

    async def client(srv):
        await srv.tools["sandbox_create"]()
        raise asyncio.CancelledError

    fake.on_run = client
    tools = SandboxTools(api(server, "async"))
    with pytest.raises(asyncio.CancelledError):
        _run(_server.serve_stdio(tools))
    assert names(server) == ["sandboxes.create", "sandboxes.kill"]
    assert tools.created == set()


@pytest.mark.skipif(sys.platform == "win32", reason="the event loop takes no signal handlers on Windows")
def test_signal_hook_installs_and_puts_back_the_previous_handler(fake):
    from fi.sandbox_integrations.mcp_server import _server

    before = signal.getsignal(signal.SIGTERM)
    if before is None:
        pytest.skip("this interpreter's SIGTERM handler was not installed from Python")

    async def go():
        restore = _server._on_signal(asyncio.get_running_loop(), signal.SIGTERM, lambda: None)
        during = signal.getsignal(signal.SIGTERM)
        restore()
        return during

    assert _run(go()) != before
    assert signal.getsignal(signal.SIGTERM) == before


def test_keep_flag_skips_cleanup(server, fake, capsys):
    server.on("sandboxes.create", answer(201, json=record()))

    async def client(srv):
        await srv.tools["sandbox_create"]()

    fake.on_run = client
    assert run("mcp", "--keep") == 0
    assert "sandboxes.kill" not in names(server)
    captured = capsys.readouterr()
    assert captured.out == "" and f"kept sandbox {SBX}" in captured.err


def test_tool_errors_reach_the_framework_as_its_tool_error(server, fake, capsys):
    server.on("sandboxes.create", refuse(409, "quota_exceeded"))
    texts = []

    async def client(srv):
        with pytest.raises(_fake_mcp.ToolError) as caught:
            await srv.tools["sandbox_create"]()
        texts.append(str(caught.value))

    fake.on_run = client
    assert run("mcp") == 0
    assert texts and texts[0].startswith("quota_exceeded: ") and "sandbox_list" in texts[0]
    no_secret(*texts)
    assert capsys.readouterr().out == ""


def test_handler_never_writes_to_stdout(server, fake, monkeypatch, capsys):
    """Every path above checks stdout; this one runs them back to back in one capture."""
    server.on("sandboxes.create", answer(201, json=record()))
    server.on("sandboxes.getInfo", answer(200, json=record()))
    server.on("sandboxes.commands.run", exec_body(("stdout", {"data": "to the tool, not stdout\n"}),
                                                  ("exit", EXIT0)))

    async def client(srv):
        await srv.tools["sandbox_create"]()
        await srv.tools["sandbox_exec"](command="echo", sandbox_id=SBX)

    fake.on_run = client
    codes = [run("mcp"), run("mcp", "--keep"), run("mcp", "--json"), run("mcp", "--format", "json")]
    monkeypatch.delenv("OMEGA_BASE_URL")
    codes.append(run("mcp"))
    assert codes == [0, 0, 0, 0, 2]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert not any(secret in captured.err for secret in SECRETS)


def test_real_mcp_builds_the_server_when_installed(fresh):
    """With a real ``mcp`` (1.x FastMCP or 2.x MCPServer), the schema comes from the parameters and a
    refusal is a tool error with its text."""
    pytest.importorskip("mcp")
    from fi.sandbox_integrations.mcp_server import SandboxTools, _server

    tools = SandboxTools(object(), pinned=SBX)  # pinned refusals send nothing
    srv = _server.build_server(tools)

    async def go():
        listed = await srv.list_tools()
        listed = getattr(listed, "tools", listed)
        try:
            result = await srv.call_tool("sandbox_exec", {"command": "ls", "sandbox_id": OTHER})
        except Exception as error:  # 1.x raises the ToolError out of call_tool
            text = str(error)
        else:  # 2.x returns the error result
            text = str(result)
        return listed, text

    listed, text = _run(go())
    assert sorted(tool.name for tool in listed) == sorted(PINNED)
    exec_tool = next(tool for tool in listed if tool.name == "sandbox_exec")
    schema = getattr(exec_tool, "inputSchema", None) or getattr(exec_tool, "input_schema")
    assert sorted(schema["properties"]) == sorted(ALL_TOOLS["sandbox_exec"])
    assert schema.get("required") == ["command"]
    assert "pinned: " in text


def _run(coro):
    import asyncio

    return asyncio.run(coro)


def test_a_dropped_create_is_reported_without_a_second_create(server, fake, capsys):
    def drop(request):
        raise httpx.ReadError("connection reset", request=request)

    server.on("sandboxes.create", drop)
    texts = []

    async def client(srv):
        with pytest.raises(_fake_mcp.ToolError) as caught:
            await srv.tools["sandbox_create"]()
        texts.append(str(caught.value))

    fake.on_run = client
    assert run("mcp") == 0
    assert names(server) == ["sandboxes.create"]
    assert "sandbox_list" in texts[0]
    assert capsys.readouterr().out == ""
