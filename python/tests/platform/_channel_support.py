"""What the channel tests share: the fake channel server as a fixture, and sandbox handles (sync and
async) that talk to it over loopback with a fake credential."""

from __future__ import annotations

import pytest
from fi.sandbox import AsyncSandbox, AsyncSandboxes, Sandbox, Sandboxes
from fi.sandbox._connection import AsyncSandboxConnection, SandboxConnection

from ._channel_fake import BEARER, SBX, FakeChannel

__all__ = ["BEARER", "SBX", "FakeChannel", "channel_fixture", "sync_sandbox", "async_sandbox", "env_for"]


def env_for(server: FakeChannel) -> dict:
    return {"OMEGA_BASE_URL": server.base_url, "FUTUREAGI_OMEGA_API_KEY": BEARER}


@pytest.fixture(name="channel")
def channel_fixture(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "sub").mkdir()
    with FakeChannel(root) as server:
        yield server


def sync_sandbox(server: FakeChannel, sandbox_id: str = SBX):
    core = SandboxConnection(environ=env_for(server)).core()
    return Sandbox(Sandboxes(core), {"id": sandbox_id}), core


def async_sandbox(server: FakeChannel, sandbox_id: str = SBX):
    core = AsyncSandboxConnection(environ=env_for(server)).core()
    return AsyncSandbox(AsyncSandboxes(core), {"id": sandbox_id}), core
