"""Pinned real backend conformance; not native customer-application qualification."""

from __future__ import annotations

import pytest
from deepagents.backends import StateBackend
from fi.context.adapters.deepagents import MEMORY_SOURCE, SKILLS_SOURCE, mount_context
from fi.context.snapshot import ManifestCollector, VerifiedSnapshot
from langchain.tools import ToolRuntime
from test_snapshots import LEASE, VERSION, Fixture


def mounted():
    fixture = Fixture()
    collector = ManifestCollector(fixture.page(), kind="agent_context")
    collector.add(fixture.page(25))
    verified = VerifiedSnapshot(collector.finish(), fixture.files)
    state = {"files": {}}
    runtime = ToolRuntime(
        state=state,
        context=None,
        config={},
        stream_writer=lambda _: None,
        tool_call_id=None,
        store=None,
    )
    checks = []

    def authorize(identity, lease):
        assert identity.version_id == VERSION and lease.resolution_id == LEASE
        checks.append(identity)

    backend = mount_context(
        verified, default=StateBackend(runtime), authorize=authorize
    )
    return fixture, backend, state, checks


def test_real_composite_mount_preserves_writable_state():
    fixture, backend, state, checks = mounted()
    assert (
        backend.download_files([MEMORY_SOURCE])[0].content
        == fixture.files["AGENTS.md"].encode()
    )
    assert any(
        item["path"] == SKILLS_SOURCE + "refund/"
        for item in backend.ls_info(SKILLS_SOURCE)
    )
    assert "Refund rules" in backend.read(SKILLS_SOURCE + "refund/SKILL.md")
    assert backend.grep_raw("Refund", SKILLS_SOURCE)
    assert backend.glob_info("**/SKILL.md", SKILLS_SOURCE)
    for path in (
        "/conversation_history/thread.txt",
        "/large_tool_results/result.txt",
        "/private_memory/task.txt",
    ):
        result = backend.write(path, "writable task state")
        assert not result.error
        state["files"].update(result.files_update)
        assert backend.download_files([path])[0].content == b"writable task state"
    assert backend.write(MEMORY_SOURCE, "overwrite").error
    assert backend.edit(MEMORY_SOURCE, "Boundary", "wrong", True).error
    assert (
        backend.upload_files([(MEMORY_SOURCE, b"overwrite")])[0].error
        == "permission_denied"
    )
    assert (
        backend.download_files([MEMORY_SOURCE])[0].content
        == fixture.files["AGENTS.md"].encode()
    )
    assert len(checks) >= 6


@pytest.mark.asyncio
async def test_async_real_backend_and_live_denial():
    fixture, backend, _, checks = mounted()
    assert (await backend.adownload_files([MEMORY_SOURCE]))[0].content == fixture.files[
        "AGENTS.md"
    ].encode()
    assert await backend.als_info(SKILLS_SOURCE)
    assert (await backend.awrite(MEMORY_SOURCE, "overwrite")).error
    assert (await backend.aedit(MEMORY_SOURCE, "Boundary", "wrong", True)).error
    assert (await backend.aupload_files([(MEMORY_SOURCE, b"wrong")]))[
        0
    ].error == "permission_denied"
    assert len(checks) >= 2


def test_revocation_or_outage_never_returns_cached_content():
    fixture = Fixture()
    collector = ManifestCollector(fixture.page(), kind="agent_context")
    collector.add(fixture.page(25))
    verified = VerifiedSnapshot(collector.finish(), fixture.files)

    def denied(identity, lease):
        raise PermissionError("Synthetic access revocation")

    runtime = ToolRuntime(
        state={"files": {}},
        context=None,
        config={},
        stream_writer=lambda _: None,
        tool_call_id=None,
        store=None,
    )
    backend = mount_context(verified, default=StateBackend(runtime), authorize=denied)
    for operation in (
        lambda: backend.download_files([MEMORY_SOURCE]),
        lambda: backend.read(MEMORY_SOURCE),
        lambda: backend.ls_info(SKILLS_SOURCE),
        lambda: backend.glob_info("**/*", "/fi_context/"),
        lambda: backend.grep_raw("Boundary", "/fi_context/"),
    ):
        with pytest.raises(PermissionError):
            operation()
