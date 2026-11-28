"""Cumulative standalone-skill installation above the shared journal.

The v1 .futureagi-skills.lock.json shape is unchanged. A separate ownership
receipt supplies the file-level preimages that a legacy download lock lacks.
Legacy ZIP locks alone never authorize overwriting an existing skill directory.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Literal

if TYPE_CHECKING:
    from fi.context.snapshot import VerifiedSnapshot

from pydantic import Field, model_validator

from fi.context.adapters.codex import (
    check_skill_content,
    check_skill_frontmatter,
    check_supporting_path,
)
from fi.context.journal import (
    SKILLS_OWNERSHIP,
    Authorization,
    Change,
    InstallPlan,
    SafeProject,
    create_plan,
    encode,
    parse_plan,
    transact,
)
from fi.context.lock import (
    MAX_BUNDLE_BYTES,
    MAX_FILE_BYTES,
    SKILLS_LOCK,
    FileMeta,
    FrozenModel,
    InstallationError,
    Lease,
    SkillIdentity,
    canonical_json,
    manifest_digest,
    sha256,
    validate_paths,
)
from fi.context.materialize import get_profile


class SkillBundle(FrozenModel):
    identity: SkillIdentity
    lease: Lease
    files: dict[str, bytes]

    @model_validator(mode="after")
    def complete(self) -> SkillBundle:
        validate_paths(list(self.files), source=True)
        if (
            not 1 <= len(self.files) <= 200
            or sum(map(len, self.files.values())) > MAX_BUNDLE_BYTES
        ):
            raise ValueError("Skill exceeds complete-tree limits")
        if manifest_digest(self.files) != self.identity.digest:
            raise ValueError("Skill digest mismatch")
        if not self.files.get("SKILL.md", b"").strip():
            raise ValueError("SKILL.md is required")
        check_skill_frontmatter(self.files["SKILL.md"])
        for path, content in self.files.items():
            check_supporting_path(path)
            if path != "SKILL.md" and path.endswith("/SKILL.md"):
                raise InstallationError(
                    "runtime_incompatible",
                    "Nested skill discovery is not qualified.",
                    7,
                )
            if len(content) > MAX_FILE_BYTES:
                raise ValueError("Skill file too large")
            if any(
                ord(c) < 32 and c not in "\r\n\t" or ord(c) == 127
                for c in content.decode("utf-8")
            ):
                raise ValueError("Skill files must be UTF-8 text")
        return self


class OwnedSkill(FrozenModel):
    identity: SkillIdentity
    files: list[FileMeta] = Field(min_length=1, max_length=200)


class SkillOwnership(FrozenModel):
    schema_version: Literal[1] = Field(default=1, alias="schema")
    profile: Literal["codex", "claude-code"]
    profile_version: Literal["1"] = "1"
    skills: list[OwnedSkill] = Field(max_length=50)

    @model_validator(mode="after")
    def complete(self) -> SkillOwnership:
        names: set[str] = set()
        ids: set[str] = set()
        scopes: set[tuple[str, str, str]] = set()
        for skill in self.skills:
            identity = skill.identity
            if identity.name in names or identity.skill_id in ids:
                raise ValueError("Duplicate skill ownership")
            names.add(identity.name)
            ids.add(identity.skill_id)
            scopes.add(
                (identity.origin, identity.organization_id, identity.workspace_id)
            )
            validate_paths([f.path for f in skill.files], source=True)
            for file in skill.files:
                check_supporting_path(file.path)
            pairs = [
                [f.path, f.sha256] for f in sorted(skill.files, key=lambda f: f.path)
            ]
            if (
                "SKILL.md" not in {f.path for f in skill.files}
                or sum(f.size_bytes for f in skill.files) > MAX_BUNDLE_BYTES
                or "sha256:" + sha256(json.dumps(pairs, separators=(",", ":")).encode())
                != identity.digest
            ):
                raise ValueError("Invalid owned skill inventory")
        if len(scopes) > 1:
            raise ValueError("Mixed ownership scopes")
        return self

    def to_bytes(self) -> bytes:
        value = self.model_dump(by_alias=True)
        for skill, entry in zip(self.skills, value["skills"]):
            entry["identity"]["requested"] = skill.identity.requested.wire()
        return canonical_json(value)

    def legacy_lock(self, origin: str) -> bytes:
        # Exact v1 schema: no new secret, receipt, scope or ownership fields.
        return canonical_json(
            {
                "schema": 1,
                "origin": origin,
                "skills": [
                    {
                        "name": s.identity.name,
                        "version": s.identity.version,
                        "version_id": s.identity.version_id,
                        "digest": s.identity.digest,
                        "label": s.identity.requested.label,
                    }
                    for s in self.skills
                ],
                "skipped": [],
            }
        )


def from_verified_snapshot(
    snapshot: VerifiedSnapshot, *, origin: str, organization_id: str, workspace_id: str
) -> SkillBundle:
    """Consume the exact typed leaf snapshot produced by L10 SkillsClient."""
    from fi.context.lock import Selector

    identity = snapshot.identity
    if identity.kind != "skill":
        raise InstallationError(
            "kind_mismatch",
            "The standalone installer requires a leaf-skill snapshot.",
            6,
        )
    lease = snapshot.manifest.lease
    return SkillBundle(
        identity=SkillIdentity(
            origin=origin,
            organization_id=organization_id,
            workspace_id=workspace_id,
            skill_id=identity.resource_id,
            name=identity.name,
            requested=Selector.model_validate(dict(snapshot.manifest.requested)),
            version=identity.version,
            version_id=identity.version_id,
            digest=identity.digest,
        ),
        lease=Lease(
            resolution_id=lease.resolution_id,
            resolution_expires_at=lease.resolution_expires_at.isoformat(),
        ),
        files={p: text.encode("utf-8") for p, text in snapshot.files.items()},
    )


def _read_ownership(
    filesystem: SafeProject, profile: str | None = None
) -> tuple[SkillOwnership | None, bytes | None, bytes | None]:
    raw = filesystem.read(SKILLS_OWNERSHIP)
    legacy = filesystem.read(SKILLS_LOCK)
    if raw is None:
        if legacy is not None:
            raise InstallationError(
                "ownership_missing",
                "A legacy download lock is not a file-ownership receipt; use an isolated destination.",
            )
        return None, raw, legacy
    try:
        ownership = SkillOwnership.model_validate(json.loads(raw))
        if not ownership.skills or legacy != ownership.legacy_lock(
            ownership.skills[0].identity.origin
        ):
            raise ValueError("Cumulative lock does not match ownership")
        if profile is not None and profile != ownership.profile:
            raise InstallationError(
                "profile_conflict",
                "Remove the existing skill profile before changing hosts.",
            )
        return ownership, raw, legacy
    except (ValueError, TypeError) as exc:
        raise InstallationError(
            "lock_invalid", "Invalid cumulative skill lock or ownership receipt.", 6
        ) from exc


def read_ownership(*, project: str | Path) -> SkillOwnership:
    """Read and validate both cumulative lock and scoped ownership receipt."""
    with SafeProject(project) as filesystem:
        ownership, _, _ = _read_ownership(filesystem)
    if ownership is None:
        raise InstallationError(
            "ownership_missing", "No skill ownership receipt exists.", 6
        )
    return ownership


def retained_identity(raw: bytes, current: SkillIdentity) -> SkillIdentity:
    """Bind a retained v1 lock entry to this project's already owned UUID/scope."""
    value = json.loads(raw)
    if (
        not isinstance(value, dict)
        or set(value) != {"schema", "origin", "skills", "skipped"}
        or type(value["schema"]) is not int
        or value["schema"] != 1
        or value["origin"] != current.origin
        or not isinstance(value["skills"], list)
        or not 1 <= len(value["skills"]) <= 50
        or not isinstance(value["skipped"], list)
    ):
        raise InstallationError(
            "lock_invalid", "Invalid retained skill lock or origin.", 6
        )
    targets = [
        item
        for item in value["skills"]
        if isinstance(item, dict) and item.get("name") == current.name
    ]
    if len(targets) != 1 or set(targets[0]) != {
        "name",
        "version",
        "version_id",
        "digest",
        "label",
    }:
        raise InstallationError(
            "lock_invalid", "Retained lock must identify this skill exactly once.", 6
        )
    target = targets[0]
    return SkillIdentity.model_validate(
        {
            **current.model_dump(),
            "version": target["version"],
            "version_id": target["version_id"],
            "digest": target["digest"],
            "requested": (
                {"label": target["label"]}
                if target["label"] is not None
                else {"version": target["version"]}
            ),
        }
    )


def plan_install_skill(
    bundle: SkillBundle,
    *,
    project: str | Path,
    profile: str,
    allow_preview: bool = False,
    operation: Literal["install", "update", "restore"] = "install",
) -> InstallPlan:
    bundle = SkillBundle.model_validate(bundle.model_dump())
    bundle.lease.require_live()
    host = get_profile(profile)
    check_skill_content(bundle.files["SKILL.md"], host)
    if not allow_preview:
        raise InstallationError(
            "profile_unverified",
            "Explicit preview opt-in is required; native delivery is not qualified.",
            7,
        )
    with SafeProject(project) as filesystem:
        ownership, raw, legacy = _read_ownership(filesystem, profile)
        entries = [] if ownership is None else list(ownership.skills)
        if entries:
            prior = entries[0].identity
            if (prior.origin, prior.organization_id, prior.workspace_id) != (
                bundle.identity.origin,
                bundle.identity.organization_id,
                bundle.identity.workspace_id,
            ):
                raise InstallationError(
                    "scope_conflict",
                    "Cumulative skill installs cannot mix origins or scopes.",
                )
        old = next(
            (
                item
                for item in entries
                if item.identity.skill_id == bundle.identity.skill_id
            ),
            None,
        )
        if any(
            item.identity.name == bundle.identity.name and item is not old
            for item in entries
        ):
            raise InstallationError(
                "identity_collision",
                "The skill name belongs to another immutable resource.",
            )
        if old is not None and old.identity.name != bundle.identity.name:
            raise InstallationError(
                "identity_collision", "An immutable skill identity changed its name."
            )
        if operation != "install" and old is None:
            raise InstallationError(
                "ownership_missing",
                "Update/restore requires this skill's ownership receipt.",
            )
        changes: list[Change] = []
        old_files = {} if old is None else {f.path: f for f in old.files}
        root = host.skills_directory + "/" + bundle.identity.name
        if filesystem.files_under(root) - {root + "/" + path for path in old_files}:
            raise InstallationError(
                "unmanaged_collision", "The native skill tree contains unowned files."
            )
        for path in sorted(set(bundle.files) | set(old_files)):
            destination = (
                host.skills_directory + "/" + bundle.identity.name + "/" + path
            )
            before = filesystem.read(destination)
            prior_file = old_files.get(path)
            if prior_file is not None and (
                before is None or sha256(before) != prior_file.sha256
            ):
                raise InstallationError(
                    "local_modifications",
                    "An installed skill file was changed or deleted; preserve/reconcile first.",
                )
            if prior_file is None and before is not None:
                raise InstallationError(
                    "unmanaged_collision",
                    "An unowned file collides with this skill installation.",
                )
            changes.append(
                Change(
                    path=destination,
                    before_sha256=None if before is None else sha256(before),
                    after=encode(bundle.files.get(path)),
                    mode=filesystem.mode(destination),
                )
            )
        replacement = OwnedSkill(
            identity=bundle.identity,
            files=[
                FileMeta(path=p, sha256=sha256(b), size_bytes=len(b))
                for p, b in sorted(bundle.files.items())
            ],
        )
        entries = sorted(
            [s for s in entries if s is not old] + [replacement],
            key=lambda s: s.identity.name,
        )
        new = SkillOwnership(profile=host.id, skills=entries)
        changes.append(
            Change(
                path=SKILLS_OWNERSHIP,
                before_sha256=None if raw is None else sha256(raw),
                after=encode(new.to_bytes()),
            )
        )
        changes.append(
            Change(
                path=SKILLS_LOCK,
                before_sha256=None if legacy is None else sha256(legacy),
                after=encode(new.legacy_lock(bundle.identity.origin)),
            )
        )
        return create_plan(
            operation=operation,
            project=str(filesystem.path),
            lock_path=SKILLS_LOCK,
            previous_lock=encode(legacy),
            changes=[c.model_dump() for c in changes],
            authorizations=[
                Authorization(
                    kind="skill", identity=bundle.identity, lease=bundle.lease
                ).model_dump()
            ],
            preserved=[],
            warnings=[
                "Preview native profile; bytes do not prove discovery or model delivery.",
                "Other installed skills remain in the cumulative lock.",
            ],
        )


def plan_remove_skill(*, project: str | Path, name: str) -> InstallPlan:
    with SafeProject(project) as filesystem:
        ownership, raw, legacy = _read_ownership(filesystem)
        if ownership is None or raw is None or legacy is None:
            raise InstallationError(
                "ownership_missing", "No skill ownership receipt exists."
            )
        target = next(
            (skill for skill in ownership.skills if skill.identity.name == name), None
        )
        if target is None:
            raise InstallationError(
                "ownership_missing", "This skill is not owned by the installer."
            )
        changes: list[Change] = []
        preserved: list[str] = []
        host = get_profile(ownership.profile)
        root = host.skills_directory + "/" + name
        preserved.extend(
            sorted(
                filesystem.files_under(root)
                - {root + "/" + f.path for f in target.files}
            )
        )
        for file in target.files:
            path = host.skills_directory + "/" + name + "/" + file.path
            before = filesystem.read(path)
            if before is None:
                continue
            dirty = sha256(before) != file.sha256
            if dirty:
                preserved.append(path)
            changes.append(
                Change(
                    path=path,
                    before_sha256=sha256(before),
                    after=encode(before) if dirty else None,
                    mode=filesystem.mode(path),
                )
            )
        remaining = ownership.model_copy(
            update={"skills": [s for s in ownership.skills if s is not target]}
        )
        changes.append(
            Change(
                path=SKILLS_OWNERSHIP,
                before_sha256=sha256(raw),
                after=encode(remaining.to_bytes()) if remaining.skills else None,
            )
        )
        changes.append(
            Change(
                path=SKILLS_LOCK,
                before_sha256=sha256(legacy),
                after=(
                    encode(remaining.legacy_lock(target.identity.origin))
                    if remaining.skills
                    else None
                ),
            )
        )
        return create_plan(
            operation="remove",
            project=str(filesystem.path),
            lock_path=SKILLS_LOCK,
            previous_lock=encode(legacy),
            changes=[c.model_dump() for c in changes],
            authorizations=[],
            preserved=preserved,
            warnings=[
                "Modified/unowned files remain. Removal does not revoke credentials."
            ],
        )


def apply_skill_plan(
    plan: InstallPlan, *, authorize: Callable[[Authorization], None], quiescent: bool
) -> None:
    plan = parse_plan(plan.to_bytes())
    if plan.lock_path != SKILLS_LOCK:
        raise InstallationError(
            "plan_invalid", "This is not a standalone skill plan.", 6
        )
    with SafeProject(plan.project) as filesystem:
        old, _, _ = _read_ownership(filesystem)
    receipt_change = next((c for c in plan.changes if c.path == SKILLS_OWNERSHIP), None)
    if receipt_change is None:
        raise InstallationError(
            "plan_invalid", "Skill plan has no ownership receipt.", 6
        )
    receipt = receipt_change.after_bytes
    new = (
        SkillOwnership.model_validate(json.loads(receipt))
        if receipt is not None
        else None
    )
    if plan.operation == "remove":
        if old is None or plan.authorizations:
            raise InstallationError("plan_invalid", "Invalid skill removal plan.", 6)
        remaining = set() if new is None else {s.identity.skill_id for s in new.skills}
        removed = [s for s in old.skills if s.identity.skill_id not in remaining]
        if len(removed) != 1:
            raise InstallationError(
                "plan_invalid", "A removal must identify exactly one owned skill.", 6
            )
        current = plan_remove_skill(project=plan.project, name=removed[0].identity.name)
    else:
        if (
            new is None
            or len(plan.authorizations) != 1
            or plan.authorizations[0].kind != "skill"
        ):
            raise InstallationError(
                "plan_invalid", "Skill install requires its exact lease.", 6
            )
        auth = plan.authorizations[0]
        if not isinstance(auth.identity, SkillIdentity):
            raise InstallationError("plan_invalid", "Wrong source kind.", 6)
        source = next((s for s in new.skills if s.identity == auth.identity), None)
        if source is None:
            raise InstallationError(
                "plan_invalid", "Skill source and receipt identities differ.", 6
            )
        prefix = (
            get_profile(new.profile).skills_directory + "/" + source.identity.name + "/"
        )
        changes = {c.path: c for c in plan.changes}
        files: dict[str, bytes] = {}
        for file in source.files:
            change = changes.get(prefix + file.path)
            if change is None or change.after_bytes is None:
                raise InstallationError(
                    "plan_invalid", "Incomplete planned skill content.", 6
                )
            files[file.path] = change.after_bytes
        bundle = SkillBundle(identity=source.identity, lease=auth.lease, files=files)
        current = plan_install_skill(
            bundle,
            project=plan.project,
            profile=new.profile,
            allow_preview=True,
            operation=plan.operation,
        )
    if plan.plan_digest != current.plan_digest:
        raise InstallationError(
            "stale_plan",
            "Skill plan no longer matches current file/ownership preimages.",
        )

    def recheck() -> None:
        if plan.operation == "remove":
            checked = plan_remove_skill(
                project=plan.project, name=removed[0].identity.name
            )
        else:
            if new is None:
                raise InstallationError(
                    "plan_invalid", "Missing new skill ownership.", 6
                )
            checked = plan_install_skill(
                bundle,
                project=plan.project,
                profile=new.profile,
                allow_preview=True,
                operation=plan.operation,
            )
        if checked.plan_digest != plan.plan_digest:
            raise InstallationError(
                "stale_plan",
                "The skill inventory changed during authorization; replan.",
            )

    transact(plan, authorize=authorize, recheck=recheck, quiescent=quiescent)


def verify_skills(*, project: str | Path) -> dict[str, object]:
    with SafeProject(project) as filesystem:
        ownership, _, _ = _read_ownership(filesystem)
        if ownership is None:
            raise InstallationError(
                "ownership_missing", "No cumulative skill ownership receipt exists.", 6
            )
        differences: list[dict[str, str]] = []
        prefix = get_profile(ownership.profile).skills_directory
        for skill in ownership.skills:
            root = prefix + "/" + skill.identity.name
            extras = filesystem.files_under(root) - {
                root + "/" + f.path for f in skill.files
            }
            differences.extend(
                {"path": path, "state": "unexpected"} for path in sorted(extras)
            )
            for file in skill.files:
                path = prefix + "/" + skill.identity.name + "/" + file.path
                content = filesystem.read(path)
                if content is None or sha256(content) != file.sha256:
                    differences.append(
                        {
                            "path": path,
                            "state": "missing" if content is None else "changed",
                        }
                    )
        return {
            "schema": 1,
            "verified": not differences,
            "differences": differences,
            "skills": len(ownership.skills),
            "scope": "checked_in_bytes_only",
            "authorization": "not_checked",
            "discovery": "not_observed",
            "delivery": "not_observed",
        }
