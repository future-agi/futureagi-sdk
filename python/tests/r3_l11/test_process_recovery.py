"""Actual process death and competing-process journal tests (POSIX)."""

from __future__ import annotations

import multiprocessing
import os
from pathlib import Path

import pytest
from fi.context.journal import SafeProject, parse_plan, recover
from fi.context.lock import CONTEXT_LOCK, InstallationError
from fi.context.materialize import apply_plan, inspect_plan, plan_install, verify
from test_materializer import bundle


def _crash_after_write(raw: bytes) -> None:
    plan = parse_plan(raw)
    original = SafeProject.replace

    def replace(self, path, content, *, mode=0o644):
        original(self, path, content, mode=mode)
        if path == "AGENTS.md":
            os._exit(73)

    SafeProject.replace = replace
    apply_plan(plan, authorize=lambda auth: None, quiescent=True)


def _hold_apply(raw, entered, release, result):
    def authorize(auth):
        entered.set()
        if not release.wait(20):
            raise RuntimeError("Synthetic barrier timed out")

    try:
        apply_plan(parse_plan(raw), authorize=authorize, quiescent=True)
        result.put("installed")
    except InstallationError as exc:
        result.put(exc.code)


@pytest.fixture
def project(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    project = tmp_path / "repo"
    project.mkdir()
    return project


def test_killed_writer_releases_kernel_lock_and_recovers_complete_preimage(project):
    plan = plan_install(bundle(), project=project, profile="codex", allow_preview=True)
    process = multiprocessing.get_context("fork").Process(
        target=_crash_after_write, args=(plan.to_bytes(),)
    )
    process.start()
    try:
        process.join(20)
        assert not process.is_alive()
        assert process.exitcode == 73
        assert not (project / CONTEXT_LOCK).exists()
        assert recover(project, quiescent=True)["state"] == "rolled_back"
        assert not (project / "AGENTS.md").exists()
        apply_plan(plan, authorize=lambda auth: None, quiescent=True)
        assert verify(project=project)["verified"]
    finally:
        if process.is_alive():
            process.terminate()
            process.join(10)
        process.close()


def test_plan_diff_is_explicit_bounded_and_bound_to_reviewed_preimages(project):
    source = bundle(root=b"Synthetic instruction line\n" * 3000)
    prepared = plan_install(
        source, project=project, profile="codex", allow_preview=True
    )
    assert "diffs" not in inspect_plan(prepared)
    review = inspect_plan(prepared, include_diff=True)
    root_diff = next(item for item in review["diffs"] if item["path"] == "AGENTS.md")
    assert root_diff["truncated"]
    assert root_diff["omitted_characters"] > 0
    assert "+Synthetic instruction line" in root_diff["diff"]
    (project / "AGENTS.md").write_bytes(b"Intervening local work")
    with pytest.raises(InstallationError) as failure:
        inspect_plan(prepared, include_diff=True)
    assert failure.value.code == "stale_plan"


def test_private_state_symlink_cannot_create_files_outside_its_home(project, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (Path.home() / ".local").symlink_to(outside, target_is_directory=True)
    prepared = plan_install(
        bundle(), project=project, profile="codex", allow_preview=True
    )
    with pytest.raises(InstallationError):
        apply_plan(prepared, authorize=lambda auth: None, quiescent=True)
    assert list(outside.iterdir()) == []
    assert list(project.iterdir()) == []


def test_competing_process_cannot_apply_during_live_authorization(project):
    plan = plan_install(bundle(), project=project, profile="codex", allow_preview=True)
    context = multiprocessing.get_context("fork")
    entered, release, result = context.Event(), context.Event(), context.Queue()
    process = context.Process(
        target=_hold_apply, args=(plan.to_bytes(), entered, release, result)
    )
    process.start()
    try:
        assert entered.wait(20)
        with pytest.raises(InstallationError) as failure:
            apply_plan(plan, authorize=lambda auth: None, quiescent=True)
        assert failure.value.code == "installation_busy"
        release.set()
        process.join(20)
        assert not process.is_alive()
        assert result.get(timeout=2) == "installed"
        assert verify(project=project)["verified"]
    finally:
        release.set()
        if process.is_alive():
            process.terminate()
            process.join(10)
        process.close()
        result.close()
