from __future__ import annotations

import errno
import json
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from fi.context.journal import SafeProject, installation_lock, parse_plan, recover
from fi.context.lock import (
    CONTEXT_LOCK,
    Identity,
    InstallationError,
    Lease,
    Selector,
    SourceBundle,
    canonical_json,
    manifest_digest,
    parse_lock,
)
from fi.context.materialize import apply_plan, plan_install, plan_remove, verify


def uid(number: int) -> str:
    return str(UUID(int=number))


def bundle(
    version=1,
    *,
    root=b"# Team instructions\nUse the approved policy.\n",
    extra=None,
    linked=True,
):
    files = {"AGENTS.md": root, **(extra or {})}
    owned = sorted(files)
    links = []
    if linked:
        child = {
            "SKILL.md": b"---\nname: refunds\ndescription: Use for refund decisions.\n---\nApproved refunds only.\n",
            "references/policy.md": f"Approved policy revision {version}.\n".encode(),
        }
        files.update({"skills/refunds/" + p: b for p, b in child.items()})
        links = [
            {
                "mount": "skills/refunds/",
                "skill_id": uid(3),
                "requested": {"label": "production"},
                "version": version,
                "version_id": uid(30 + version),
                "digest": manifest_digest(child),
            }
        ]
    files[".futureagi/context.json"] = canonical_json(
        {
            "schema": 1,
            "kind": "agent_context",
            "name": "team-policy",
            "description": "Reviewed policy",
            "entrypoint": "AGENTS.md",
            "owned_paths": owned,
            "links": links,
        }
    )
    return SourceBundle(
        identity=Identity(
            origin="https://registry.example.invalid",
            organization_id=uid(1),
            workspace_id=uid(2),
            context_id=uid(4),
            name="team-policy",
            requested=Selector(label="production"),
            version=version,
            version_id=uid(40 + version),
            digest=manifest_digest(files),
        ),
        lease=Lease(
            resolution_id="synthetic-lease",
            resolution_expires_at=(
                datetime.now(timezone.utc) + timedelta(minutes=10)
            ).isoformat(),
        ),
        files=files,
    )


@pytest.fixture
def project(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    path = tmp_path / "repo"
    path.mkdir()
    return path


def plan(source, project, **kwargs):
    return plan_install(
        source,
        project=project,
        profile=kwargs.pop("profile", "codex"),
        allow_preview=True,
        **kwargs,
    )


def apply(value, authorize=lambda auth: None):
    apply_plan(value, authorize=authorize, quiescent=True)


def install(project, **kwargs):
    value = plan(bundle(), project, **kwargs)
    apply(value)
    return value


@pytest.mark.parametrize("profile", ["codex", "claude-code"])
def test_cold_adoption_update_restore_remove_preserves_every_local_byte(
    project, profile
):
    local = b"Local instruction without newline"
    (project / "AGENTS.md").write_bytes(local)
    (project / "CLAUDE.md").write_bytes(b"Existing Claude policy\n")
    with pytest.raises(InstallationError, match="explicit"):
        plan(bundle(), project, profile=profile)
    first = bundle()
    prepared = plan(first, project, profile=profile, adopt_local=True)
    assert not (project / CONTEXT_LOCK).exists()
    assert "synthetic-lease" not in json.dumps(prepared.review())
    apply(parse_plan(prepared.to_bytes()))
    assert verify(project=project)["verified"]
    old_lock = (project / CONTEXT_LOCK).read_bytes()
    assert b"synthetic-lease" not in old_lock
    (project / "AGENTS.md").write_bytes(
        (project / "AGENTS.md").read_bytes() + b"\nNew local exception\n"
    )
    second = bundle(2)
    apply(plan(second, project, profile=profile, operation="update"))
    assert (
        (project / "AGENTS.md")
        .read_bytes()
        .endswith(local + b"\nNew local exception\n")
    )
    apply(plan(first, project, profile=profile, operation="restore"))
    assert parse_lock((project / CONTEXT_LOCK).read_bytes()).version == 1
    apply(plan_remove(project=project))
    assert (project / "AGENTS.md").read_bytes() == local + b"\nNew local exception\n"
    assert (project / "CLAUDE.md").read_bytes() == b"Existing Claude policy\n"
    assert not (project / CONTEXT_LOCK).exists()


def test_native_profile_never_claimed_verified(project):
    with pytest.raises(InstallationError) as exc:
        plan_install(bundle(), project=project, profile="codex")
    assert exc.value.exit_code == 7
    prepared = plan(bundle(), project)
    with pytest.raises(InstallationError) as exc:
        apply_plan(prepared, authorize=lambda auth: None, quiescent=False)
    assert exc.value.code == "quiescence_required"
    assert not (project / "AGENTS.md").exists()


@pytest.mark.parametrize("kind", ["unowned", "dirty", "deleted"])
def test_native_collisions_and_deleted_managed_files_never_overwritten(project, kind):
    native = project / ".agents/skills/refunds/references/policy.md"
    if kind == "unowned":
        native.parent.mkdir(parents=True)
        native.write_bytes(b"Local unrelated policy")
    else:
        install(project)
        if kind == "dirty":
            native.write_bytes(b"Local edited policy")
        else:
            native.unlink()
    with pytest.raises(InstallationError) as exc:
        plan(bundle(2), project)
    assert exc.value.code in ("unmanaged_collision", "local_modifications")
    assert (
        (not native.exists())
        if kind == "deleted"
        else native.read_bytes().startswith(b"Local")
    )


def test_deleted_paths_removed_but_dirty_removal_retained(project):
    install(project)
    native = project / ".agents/skills/refunds/references/policy.md"
    native.write_bytes(b"Retained local work")
    removal = plan_remove(project=project)
    assert native.relative_to(project).as_posix() in removal.preserved
    apply(removal)
    assert native.read_bytes() == b"Retained local work"
    assert not (project / ".agents/skills/refunds/SKILL.md").exists()


def test_removed_dependency_paths_removed_with_new_lock_last(project):
    install(project)
    value = plan(bundle(2, linked=False), project)
    assert value.changes[-1].path == CONTEXT_LOCK
    apply(value)
    assert not (project / ".agents/skills/refunds/SKILL.md").exists()
    assert verify(project=project)["verified"]


@pytest.mark.parametrize(
    "path",
    [
        ".claude/settings.json",
        ".mcp.json",
        ".github/workflows/owned.yml",
        ".git/hooks/pre-commit",
        "package.json",
        "nested/AGENTS.md",
        "CLAUDE.md",
    ],
)
def test_supporting_host_control_files_are_blocked_even_when_absent(project, path):
    with pytest.raises(InstallationError) as exc:
        plan(bundle(extra={path: b"do not execute"}), project)
    assert exc.value.code == "destination_forbidden"
    assert list(project.iterdir()) == []


def test_host_skill_extensions_are_blocked(project):
    source = bundle()
    files = dict(source.files)
    files["skills/refunds/SKILL.md"] = files["skills/refunds/SKILL.md"].replace(
        b"description:", b"hooks: {}\ndescription:"
    )
    descriptor = json.loads(files[".futureagi/context.json"])
    descriptor["links"][0]["digest"] = manifest_digest(
        {
            p[len("skills/refunds/") :]: b
            for p, b in files.items()
            if p.startswith("skills/refunds/")
        }
    )
    files[".futureagi/context.json"] = canonical_json(descriptor)
    source = SourceBundle(
        identity=source.identity.model_copy(update={"digest": manifest_digest(files)}),
        lease=source.lease,
        files=files,
    )
    with pytest.raises(InstallationError) as exc:
        plan(source, project)
    assert exc.value.code == "runtime_incompatible"


@pytest.mark.parametrize("kind", ["file", "directory", "project", "case", "hardlink"])
def test_symlinks_hardlinks_and_case_aliases_refused(project, tmp_path, kind):
    outside = tmp_path / "outside"
    outside.mkdir()
    original = outside / "policy"
    original.write_bytes(b"outside unchanged")
    if kind == "file":
        (project / "AGENTS.md").symlink_to(original)
    elif kind == "directory":
        (project / ".futureagi").symlink_to(outside, target_is_directory=True)
    elif kind == "project":
        alias = tmp_path / "alias"
        alias.symlink_to(project, target_is_directory=True)
        project = alias
    elif kind == "case":
        (project / "agents.MD").write_bytes(b"Case alias")
    else:
        os.link(original, project / "AGENTS.md")
    with pytest.raises(InstallationError):
        plan(bundle(), project, adopt_local=True)
    assert original.read_bytes() == b"outside unchanged"


def test_concurrent_apply_and_preimage_change_are_conflicts(project):
    prepared = plan(bundle(), project)
    with installation_lock(str(project)):
        with pytest.raises(InstallationError) as exc:
            apply(prepared)
        assert exc.value.code == "installation_busy"
    (project / "AGENTS.md").write_bytes(b"Arrived after review")
    with pytest.raises(InstallationError) as exc:
        apply(prepared)
    assert exc.value.code == "stale_plan"
    assert (project / "AGENTS.md").read_bytes() == b"Arrived after review"


def test_authorization_rechecked_after_planning_without_latest_substitution(project):
    source = bundle()
    prepared = plan(source, project)
    seen = []

    def deny(auth):
        seen.append((auth.identity.version_id, auth.lease.resolution_id))
        raise InstallationError("quarantined", "No longer eligible", 3)

    with pytest.raises(InstallationError) as exc:
        apply(prepared, deny)
    assert exc.value.code == "quarantined"
    assert seen == [(source.identity.version_id, "synthetic-lease")]
    assert list(project.iterdir()) == []


def test_edits_during_live_authorization_are_rechecked(project):
    prepared = plan(bundle(), project)

    def authorize(auth):
        (project / "AGENTS.md").write_bytes(b"Concurrent edit")

    with pytest.raises(InstallationError) as exc:
        apply(prepared, authorize)
    assert exc.value.code == "stale_plan"
    assert (project / "AGENTS.md").read_bytes() == b"Concurrent edit"


@pytest.mark.parametrize("fail_after", [1, 3, 8])
def test_disk_full_journal_rolls_back_without_lock_commit(
    project, monkeypatch, fail_after
):
    old = install(project)
    original_lock = (project / CONTEXT_LOCK).read_bytes()
    update = plan(bundle(2), project, operation="update")
    original_replace = SafeProject.replace
    calls = 0

    def fail(self, path, content, *, mode=0o644):
        nonlocal calls
        calls += 1
        if calls == fail_after:
            raise OSError(errno.ENOSPC, "synthetic disk full")
        return original_replace(self, path, content, mode=mode)

    monkeypatch.setattr(SafeProject, "replace", fail)
    with pytest.raises(InstallationError) as exc:
        apply(update)
    assert exc.value.code == "recovery_required"
    assert (project / CONTEXT_LOCK).read_bytes() == original_lock
    monkeypatch.setattr(SafeProject, "replace", original_replace)
    assert recover(project, quiescent=True)["state"] == "rolled_back"
    assert verify(project=project)["verified"]
    assert recover(project, quiescent=True)["state"] == "no_recovery_needed"
    assert old.changes[-1].after_bytes == (project / CONTEXT_LOCK).read_bytes()


def test_process_crash_after_last_lock_write_reconciles_committed(project, monkeypatch):
    prepared = plan(bundle(), project)
    original = SafeProject.replace

    def crash(self, path, content, *, mode=0o644):
        original(self, path, content, mode=mode)
        if path == CONTEXT_LOCK:
            raise SystemExit("synthetic process termination")

    monkeypatch.setattr(SafeProject, "replace", crash)
    with pytest.raises(SystemExit):
        apply(prepared)
    monkeypatch.setattr(SafeProject, "replace", original)
    assert recover(project, quiescent=True)["state"] == "committed"
    assert verify(project=project)["verified"]


def test_recovery_refuses_to_overwrite_post_crash_local_edit(project, monkeypatch):
    prepared = plan(bundle(), project)
    original = SafeProject.replace

    def crash(self, path, content, *, mode=0o644):
        original(self, path, content, mode=mode)
        if path == "AGENTS.md":
            raise SystemExit

    monkeypatch.setattr(SafeProject, "replace", crash)
    with pytest.raises(SystemExit):
        apply(prepared)
    monkeypatch.setattr(SafeProject, "replace", original)
    (project / "AGENTS.md").write_bytes(b"New work after crash")
    with pytest.raises(InstallationError) as exc:
        recover(project, quiescent=True)
    assert exc.value.code == "recovery_conflict"
    assert (project / "AGENTS.md").read_bytes() == b"New work after crash"


def test_corrupt_lock_and_plan_are_integrity_failures(project):
    prepared = install(project)
    raw = json.loads(prepared.to_bytes())
    raw["changes"][0]["path"] = "../escape"
    with pytest.raises(InstallationError):
        parse_plan(json.dumps(raw).encode())
    raw = json.loads((project / CONTEXT_LOCK).read_bytes())
    raw["files"][0]["sha256"] = "f" * 64
    (project / CONTEXT_LOCK).write_text(json.dumps(raw))
    with pytest.raises(InstallationError) as exc:
        verify(project=project)
    assert exc.value.exit_code == 6


def test_lease_expiry_requires_replan_before_any_writes(project):
    source = bundle()
    source = source.model_copy(
        update={
            "lease": Lease(
                resolution_id="expired", resolution_expires_at="2000-01-01T00:00:00Z"
            )
        }
    )
    with pytest.raises(InstallationError) as exc:
        plan(source, project)
    assert exc.value.code == "resolution_expired"
    assert list(project.iterdir()) == []


def test_relative_markdown_links_rewritten_only_to_known_targets(project):
    source = bundle(
        root=b"# Rules\nRead [policy](references/policy.md#limits).\n",
        extra={"references/policy.md": b"# Limits\n"},
    )
    prepared = plan(source, project)
    apply(prepared)
    assert (
        ".futureagi/context/"
        + source.identity.digest[7:]
        + "/references/policy.md#limits"
    ).encode() in (project / "AGENTS.md").read_bytes()
    assert verify(project=project)["verified"]


@pytest.mark.parametrize(
    "root",
    [
        b"Read `references/policy.md`.",
        b"Read [policy](references/missing.md).",
        b'Read [policy](references/policy.md "Title").',
    ],
)
def test_ambiguous_relocation_blocks_instead_of_guessing(project, root):
    with pytest.raises(InstallationError) as exc:
        plan(bundle(root=root, extra={"references/policy.md": b"Policy"}), project)
    assert exc.value.code == "runtime_incompatible"


def test_corrupted_managed_instruction_segment_blocks_update_and_is_preserved_on_remove(
    project,
):
    install(project)
    (project / "AGENTS.md").write_bytes(
        (project / "AGENTS.md")
        .read_bytes()
        .replace(b"approved policy", b"edited policy")
    )
    before = (project / "AGENTS.md").read_bytes()
    with pytest.raises(InstallationError) as exc:
        plan(bundle(2), project)
    assert exc.value.code == "local_modifications"
    removal = plan_remove(project=project)
    assert "AGENTS.md" in removal.preserved
    apply(removal)
    assert (project / "AGENTS.md").read_bytes() == before


def test_unowned_files_arriving_during_authorization_block_apply(project):
    prepared = plan(bundle(), project)
    unexpected = project / ".agents/skills/refunds/unowned.md"

    def authorize(auth):
        unexpected.parent.mkdir(parents=True)
        unexpected.write_bytes(b"Concurrent local file")

    with pytest.raises(InstallationError) as exc:
        apply(prepared, authorize)
    assert exc.value.code == "unmanaged_collision"
    assert unexpected.read_bytes() == b"Concurrent local file"
    assert not (project / CONTEXT_LOCK).exists()


def test_context_verifier_detects_extra_files_and_remove_preserves_them(project):
    install(project)
    extra = project / ".agents/skills/refunds/unowned.md"
    extra.write_bytes(b"Unowned local work")
    result = verify(project=project)
    assert not result["verified"]
    assert {
        "path": ".agents/skills/refunds/unowned.md",
        "state": "unexpected",
    } in result["differences"]
    removal = plan_remove(project=project)
    assert ".agents/skills/refunds/unowned.md" in removal.preserved
    apply(removal)
    assert extra.read_bytes() == b"Unowned local work"


def test_materialization_rewrites_percent_encoded_known_links_without_losing_bytes(
    project,
):
    source = bundle(
        root=b"Read [policy](references/local%20policy.md).",
        extra={"references/local policy.md": "Snow 雪".encode()},
    )
    apply(plan(source, project))
    assert b"references/local%20policy.md" in (project / "AGENTS.md").read_bytes()
    assert verify(project=project)["verified"]


def test_scope_and_profile_changes_do_not_retarget_existing_install(project):
    install(project)
    source = bundle(2)
    source = source.model_copy(
        update={"identity": source.identity.model_copy(update={"workspace_id": uid(9)})}
    )
    with pytest.raises(InstallationError) as exc:
        plan(source, project)
    assert exc.value.code == "scope_conflict"
    with pytest.raises(InstallationError) as exc:
        plan(bundle(2), project, profile="claude-code")
    assert exc.value.code == "profile_conflict"
