"""Agent management, run operations and the optional code preview compose together."""
import argparse
import asyncio

import pytest

from fi import AsyncFutureAGIClient, FutureAGIClient
from fi.agents import cli
from fi.agents.runs import _cli as runs_cli


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("order", [(cli, runs_cli), (runs_cli, cli)])
def test_command_plugins_share_one_group(monkeypatch, enabled, order):
    if enabled:
        monkeypatch.setenv("FI_AGENT_CODE_ENABLED", "1")
    else:
        monkeypatch.delenv("FI_AGENT_CODE_ENABLED", raising=False)
    parser = argparse.ArgumentParser()
    groups = parser.add_subparsers(dest="group", required=True)
    for plugin in order:
        plugin.register(groups)
    assert set(groups.choices) == {"agents"}
    agents = groups.choices["agents"]
    commands = next(a for a in agents._actions if isinstance(a, argparse._SubParsersAction))
    code = {"validate", "plan", "apply", "export", "import"}
    assert set(commands.choices) == {"runs"} | (code if enabled else set())
    assert parser.parse_args(["agents", "runs", "list"]).func is runs_cli.execute


def check_namespaces(client):
    agents = client.agents
    assert agents is client.agents
    assert agents._client is client
    for name in ("create", "get", "list", "draft", "releases", "revisions", "retire"):
        assert callable(getattr(agents, name))
    assert agents.schedules is not None
    assert agents.code is not None
    assert callable(agents.runs.create)
    assert callable(agents.runs.get)
    assert callable(agents.ratings.summary)
    assert callable(client.environments.list)


def test_sync_namespaces_and_option_copies_are_composed_without_requests():
    with FutureAGIClient(base_url="http://127.0.0.1:1") as client:
        check_namespaces(client)
        with client.with_options(timeout=2) as copy:
            check_namespaces(copy)


def test_async_namespaces_and_option_copies_are_composed_without_requests():
    async def run():
        async with AsyncFutureAGIClient(base_url="http://127.0.0.1:1") as client:
            check_namespaces(client)
            async with client.with_options(timeout=2) as copy:
                check_namespaces(copy)
    asyncio.run(run())
