"""FutureAGISandboxClient against a real sandbox deployment and the real Agents SDK (openai-agents 0.24).

Opt-in only: it runs when ``FI_E2E_REQUIRED=1`` and the sandbox environment are set (``OMEGA_BASE_URL``
plus ``FI_API_KEY`` and ``FI_SECRET_KEY``, or ``FUTUREAGI_OMEGA_API_KEY``) and when ``agents.sandbox`` is
installed (``futureagi[sandbox-openai-agents]``). ``FI_SANDBOX_TEMPLATE`` picks the template (the
deployment's default otherwise). Every sandbox it makes is deleted at the end. The ``SandboxAgent`` run
also needs a model: it runs only when ``OPENAI_API_KEY`` is set.
"""

from __future__ import annotations

import asyncio
import io
import os
from pathlib import Path

import pytest

if os.environ.get("FI_E2E_REQUIRED") != "1":
    pytest.skip("live sandbox tests require explicit opt-in: set FI_E2E_REQUIRED=1", allow_module_level=True)
if not os.environ.get("OMEGA_BASE_URL") or not (
    os.environ.get("FUTUREAGI_OMEGA_API_KEY")
    or (os.environ.get("FI_API_KEY") and os.environ.get("FI_SECRET_KEY"))
):
    pytest.skip(
        "live sandbox tests need OMEGA_BASE_URL and FI_API_KEY + FI_SECRET_KEY or FUTUREAGI_OMEGA_API_KEY",
        allow_module_level=True,
    )

pytest.importorskip("agents.sandbox")

from agents.sandbox.snapshot import LocalSnapshotSpec  # noqa: E402

from fi.sandbox_integrations.openai_agents import (  # noqa: E402
    FutureAGISandboxClient,
    FutureAGISandboxClientOptions,
)

TEMPLATE = os.environ.get("FI_SANDBOX_TEMPLATE") or None


def options(name: str, **fields) -> FutureAGISandboxClientOptions:
    return FutureAGISandboxClientOptions(name=name, template=TEMPLATE, idle_ttl_seconds=900, **fields)


async def _session_round_trip() -> None:
    client = FutureAGISandboxClient()
    first = await client.create(options=options("agents-sdk-live-a"))
    second = None
    try:
        await first.start()
        here = await first.exec("pwd", shell=False)
        assert here.exit_code == 0 and here.stdout.strip() == b"/workspace"
        result = await first.exec("python3", "-c", "print(1)", shell=False)
        assert result.exit_code == 0 and result.stdout.strip() == b"1"
        await first.write(Path("notes/hello.txt"), io.BytesIO(b"hello from the agents sdk"))
        assert (await first.read(Path("notes/hello.txt"))).read() == b"hello from the agents sdk"
        archive = await first.persist_workspace()
        second = await client.create(options=options("agents-sdk-live-b"))
        await second.start()
        await second.hydrate_workspace(archive)
        assert (await second.read(Path("notes/hello.txt"))).read() == b"hello from the agents sdk"
        assert await second.running() is True
    finally:
        await client.delete(first)
        if second is not None:
            await client.delete(second)


def test_session_exec_files_persist_hydrate_delete():
    asyncio.run(_session_round_trip())


async def _subfolder_root() -> None:
    client = FutureAGISandboxClient()
    session = await client.create(options=options("agents-sdk-live-c", workdir="/workspace/proj"))
    try:
        await session.start()
        here = await session.exec("pwd", shell=False)
        assert here.exit_code == 0 and here.stdout.strip() == b"/workspace/proj"
        await session.write(Path("notes/hi.txt"), io.BytesIO(b"hi"))
        shown = await session.exec("cat", "notes/hi.txt", shell=False)
        assert shown.exit_code == 0 and shown.stdout == b"hi"
    finally:
        await client.delete(session)


def test_commands_run_in_a_subfolder_root():
    asyncio.run(_subfolder_root())


@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="the SandboxAgent run needs a model key")
def test_sandbox_agent_run(tmp_path):
    from agents import RunConfig, Runner
    from agents.sandbox import SandboxAgent, SandboxRunConfig

    agent = SandboxAgent(
        name="sandbox-check",
        instructions="Run the shell command the user gives and reply with its output only.",
    )
    config = RunConfig(
        sandbox=SandboxRunConfig(
            client=FutureAGISandboxClient(),
            options=options("agents-sdk-live-run"),
            snapshot=LocalSnapshotSpec(base_path=tmp_path),
        )
    )
    result = asyncio.run(Runner.run(agent, 'python3 -c "print(6 * 7)"', run_config=config))
    assert "42" in str(result.final_output)
