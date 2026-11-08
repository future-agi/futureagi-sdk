"""Non-destructive project context plans, application, removal and byte verification."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Literal

if TYPE_CHECKING:
    from .snapshot import VerifiedSnapshot

from pydantic import Field, field_validator

from .adapters.claude_code import IMPORT
from .adapters.claude_code import PROFILE as CLAUDE_PROFILE
from .adapters.codex import (
    PROFILE as CODEX_PROFILE,
)
from .adapters.codex import (
    Profile,
    check_skill_frontmatter,
    check_supporting_path,
    managed_block,
    preserve_local,
    project_entrypoint,
    split_managed,
)
from .journal import (
    Authorization,
    Change,
    InstallPlan,
    SafeProject,
    create_plan,
    decode,
    encode,
    parse_plan,
    transact,
)
from .lock import (
    CONTEXT_LOCK,
    ContextLock,
    FileMeta,
    FrozenModel,
    Identity,
    InstallationError,
    Materialization,
    MaterializedFile,
    Selector,
    SourceBundle,
    canonical_json,
    digest_value,
    manifest_digest,
    materialization_digest,
    parse_lock,
    sha256,
    uuid_value,
    validate_paths,
)


class LockedLink(FrozenModel):
    mount: str
    skill_id: str
    requested: Selector
    version: int = Field(ge=1)
    version_id: str
    digest: str

    _ids = field_validator("skill_id", "version_id")(uuid_value)
    _digest = field_validator("digest")(digest_value)


class Descriptor(FrozenModel):
    schema_version: Literal[1] = Field(alias="schema")
    kind: Literal["agent_context"]
    name: str
    description: str = Field(min_length=1, max_length=1024)
    entrypoint: Literal["AGENTS.md"]
    owned_paths: list[str]
    links: list[LockedLink] = Field(max_length=20)


def from_verified_snapshot(
    snapshot: VerifiedSnapshot, *, origin: str, organization_id: str, workspace_id: str
) -> SourceBundle:
    """Consume L10's VerifiedSnapshot without another resolver or HTTP client."""
    from .lock import Lease

    if snapshot.identity.kind != "agent_context":
        raise InstallationError(
            "kind_mismatch",
            "A context installer requires an agent-context snapshot.",
            6,
        )
    identity = snapshot.identity
    lease = snapshot.manifest.lease
    return SourceBundle(
        identity=Identity(
            origin=origin,
            organization_id=organization_id,
            workspace_id=workspace_id,
            context_id=identity.resource_id,
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


def get_profile(name: str) -> Profile:
    if name == "codex":
        return CODEX_PROFILE
    if name == "claude-code":
        return CLAUDE_PROFILE
    raise InstallationError(
        "profile_unsupported",
        "Only project-scoped codex and claude-code preview profiles are available.",
        7,
    )


def generation_path(digest: str) -> str:
    digest_value(digest)
    return ".futureagi/context/" + digest[7:]


def validate_bundle(bundle: SourceBundle) -> Descriptor:
    """Validate exact compiled closure, descriptor, and portable native controls."""
    try:
        raw = bundle.files[".futureagi/context.json"]
        value = json.loads(raw)
        descriptor = Descriptor.model_validate(value)
        if canonical_json(value) != raw or descriptor.name != bundle.identity.name:
            raise ValueError("Noncanonical descriptor or name mismatch")
        if descriptor.owned_paths != sorted(
            descriptor.owned_paths
        ) or descriptor.links != sorted(descriptor.links, key=lambda link: link.mount):
            raise ValueError("Unsorted descriptor")
        validate_paths(descriptor.owned_paths, source=True)
        if "AGENTS.md" not in descriptor.owned_paths:
            raise ValueError("Missing owned root")
        allowed = set(descriptor.owned_paths) | {".futureagi/context.json"}
        for path in descriptor.owned_paths:
            if path != "AGENTS.md":
                check_supporting_path(path)
                if path.startswith(("skills/", ".futureagi/")):
                    raise ValueError("Reserved authored path")
        skill_ids: set[str] = set()
        mounts: set[str] = set()
        for link in descriptor.links:
            mount = link.mount.removesuffix("/")
            if (
                not re.fullmatch(r"skills/[a-z0-9]+(?:-[a-z0-9]+)*/", link.mount)
                or link.skill_id in skill_ids
                or mount in mounts
            ):
                raise ValueError("Invalid or duplicate linked mount")
            skill_ids.add(link.skill_id)
            mounts.add(mount)
            child = {
                p[len(mount) + 1 :]: b
                for p, b in bundle.files.items()
                if p.startswith(mount + "/")
            }
            if "SKILL.md" not in child or manifest_digest(child) != link.digest:
                raise ValueError("Linked skill inventory/digest mismatch")
            check_skill_frontmatter(child["SKILL.md"])
            for path in child:
                check_supporting_path(path)
                if path != "SKILL.md" and path.endswith("/SKILL.md"):
                    raise InstallationError(
                        "runtime_incompatible",
                        "Nested skill discovery is not supported.",
                        7,
                    )
            allowed.update(mount + "/" + p for p in child)
        if allowed != set(bundle.files):
            raise ValueError("Incomplete or extra descriptor inventory")
        return descriptor
    except (ValueError, KeyError, TypeError) as exc:
        raise InstallationError(
            "integrity_failure",
            "Compiled context descriptor or dependency closure is invalid.",
            6,
        ) from exc


def _projected(
    bundle: SourceBundle, profile: Profile
) -> dict[str, tuple[bytes, str, Literal["copy", "entrypoint", "import"]]]:
    validate_bundle(bundle)
    generation = generation_path(bundle.identity.digest)
    outputs: dict[str, tuple[bytes, str, Literal["copy", "entrypoint", "import"]]] = {
        generation + "/" + path: (content, path, "copy")
        for path, content in bundle.files.items()
    }
    for path, content in bundle.files.items():
        if path.startswith("skills/"):
            outputs[profile.skills_directory + "/" + path[len("skills/") :]] = (
                content,
                path,
                "copy",
            )
    root = project_entrypoint(
        bundle.files["AGENTS.md"],
        set(bundle.files),
        generation,
        profile.skills_directory,
    )
    outputs["AGENTS.md"] = (
        managed_block(bundle.identity.context_id, root),
        "AGENTS.md",
        "entrypoint",
    )
    if profile.import_file:
        outputs[profile.import_file] = (
            managed_block(bundle.identity.context_id, IMPORT),
            "AGENTS.md",
            "import",
        )
    validate_paths(list(outputs))
    return outputs


def validate_lock_layout(lock: ContextLock) -> None:
    profile = get_profile(lock.materialization.profile)
    generation = generation_path(lock.digest)
    expected: dict[str, tuple[str, str]] = {
        generation + "/" + f.path: (f.path, "copy") for f in lock.files
    }
    for file in lock.files:
        if file.path.startswith("skills/"):
            expected[profile.skills_directory + "/" + file.path[len("skills/") :]] = (
                file.path,
                "copy",
            )
    expected["AGENTS.md"] = ("AGENTS.md", "entrypoint")
    if profile.import_file:
        expected[profile.import_file] = ("AGENTS.md", "import")
    if set(expected) != {f.destination for f in lock.materialization.files}:
        raise InstallationError(
            "lock_invalid",
            "Lock ownership is not the exact profile output inventory.",
            6,
        )
    for output in lock.materialization.files:
        if expected[output.destination] != (output.source_path, output.transformation):
            raise InstallationError(
                "lock_invalid",
                "Lock destination/transformation is outside the profile.",
                6,
            )
        if output.transformation == "copy" and output.sha256 != output.source_sha256:
            raise InstallationError(
                "lock_invalid",
                "A copied output differs from canonical source bytes.",
                6,
            )


def managed_roots(lock: ContextLock) -> set[str]:
    profile = get_profile(lock.materialization.profile)
    roots = {generation_path(lock.digest)}
    roots.update(
        profile.skills_directory + "/" + f.path.split("/")[1]
        for f in lock.files
        if f.path.startswith("skills/")
    )
    return roots


def _retained_bundle(
    project: SafeProject, lock: ContextLock, authorization: Authorization
) -> SourceBundle:
    files: dict[str, bytes] = {}
    for file in lock.files:
        content = project.read(generation_path(lock.digest) + "/" + file.path)
        if (
            content is None
            or len(content) != file.size_bytes
            or sha256(content) != file.sha256
        ):
            raise InstallationError(
                "local_modifications",
                "Canonical managed files are missing or changed; preserve/reconcile before updating.",
            )
        files[file.path] = content
    return SourceBundle(
        identity=Identity.model_validate(
            {k: v for k, v in lock.model_dump().items() if k in Identity.model_fields}
        ),
        lease=authorization.lease,
        files=files,
    )


def _old_blocks(
    project: SafeProject, lock: ContextLock, auth: Authorization
) -> dict[str, bytes]:
    validate_lock_layout(lock)
    outputs = _projected(
        _retained_bundle(project, lock, auth), get_profile(lock.materialization.profile)
    )
    return {
        path: content
        for path, (content, _, transform) in outputs.items()
        if transform != "copy"
    }


def plan_install(
    bundle: SourceBundle,
    *,
    project: str | Path,
    profile: str,
    adopt_local: bool = False,
    allow_preview: bool = False,
    operation: Literal["install", "update", "restore"] = "install",
) -> InstallPlan:
    """Plan exactly one resolved snapshot. No repository file is changed here."""
    # Frozen models can still contain mutable dict/list values; revalidate at entry.
    bundle = SourceBundle.model_validate(bundle.model_dump())
    bundle.lease.require_live()
    host = get_profile(profile)
    if not allow_preview:
        raise InstallationError(
            "profile_unverified",
            "Native discovery is not qualified. Explicitly opt into the preview profile; installation is not delivery evidence.",
            7,
        )
    desired = _projected(bundle, host)
    authorization = Authorization(
        kind="agent_context", identity=bundle.identity, lease=bundle.lease
    )
    with SafeProject(project) as filesystem:
        previous_raw = filesystem.read(CONTEXT_LOCK)
        previous = parse_lock(previous_raw) if previous_raw is not None else None
        if operation != "install" and previous is None:
            raise InstallationError(
                "lock_missing", "Update/restore requires the current ownership lock."
            )
        old_files: dict[str, MaterializedFile] = {}
        old_blocks: dict[str, bytes] = {}
        if previous is not None:
            if (
                previous.origin,
                previous.organization_id,
                previous.workspace_id,
                previous.context_id,
            ) != (
                bundle.identity.origin,
                bundle.identity.organization_id,
                bundle.identity.workspace_id,
                bundle.identity.context_id,
            ):
                raise InstallationError(
                    "scope_conflict",
                    "An existing installation belongs to a different origin/scope/context.",
                )
            if previous.materialization.profile != profile:
                raise InstallationError(
                    "profile_conflict",
                    "Remove the old profile explicitly before changing hosts.",
                )
            old_files = {f.destination: f for f in previous.materialization.files}
            old_blocks = _old_blocks(filesystem, previous, authorization)
        roots = {generation_path(bundle.identity.digest)}
        roots.update(
            host.skills_directory + "/" + path.split("/")[1]
            for path in bundle.files
            if path.startswith("skills/")
        )
        if previous is not None:
            roots.update(managed_roots(previous))
        for root in roots:
            if filesystem.files_under(root) - set(old_files):
                raise InstallationError(
                    "unmanaged_collision",
                    "A managed destination tree contains unowned files; preserve/reconcile them before installation.",
                )
        changes: list[Change] = []
        managed: list[MaterializedFile] = []
        local = b""
        root_block = desired["AGENTS.md"][0]
        content: bytes | None
        for path in sorted(set(desired) | set(old_files)):
            before = filesystem.read(path)
            old = old_files.get(path)
            ownership: Literal["managed", "adopted"] = "managed"
            if old is not None:
                ownership = old.ownership
                if before is None:
                    raise InstallationError(
                        "local_modifications",
                        "A managed path was deleted; no silent recreation is allowed.",
                    )
                if old.transformation == "copy":
                    if sha256(before) != old.sha256:
                        raise InstallationError(
                            "local_modifications",
                            "A managed file was edited; preserve/reconcile it before updating.",
                        )
                else:
                    prefix, block, suffix = split_managed(
                        before, bundle.identity.context_id
                    )
                    if block != old_blocks[path]:
                        raise InstallationError(
                            "local_modifications",
                            "Managed instructions changed; automatic merging is not supported.",
                        )
            if path in desired:
                content, source, transform = desired[path]
                if transform == "copy":
                    if before is not None and old is None:
                        raise InstallationError(
                            "unmanaged_collision",
                            "A desired output already exists without ownership, even if its bytes match.",
                        )
                elif old is not None and before is not None:
                    prefix, _, suffix = split_managed(
                        before, bundle.identity.context_id
                    )
                    content = prefix + content + suffix
                    if path == "AGENTS.md":
                        local = prefix + suffix
                else:
                    content, preserved, adopted = preserve_local(
                        before, content, adopt=adopt_local
                    )
                    ownership = "adopted" if adopted else "managed"
                    if path == "AGENTS.md":
                        local = preserved
                managed.append(
                    MaterializedFile(
                        destination=path,
                        sha256=sha256(content),
                        source_path=source,
                        source_sha256=sha256(bundle.files[source]),
                        ownership=ownership,
                        transformation=transform,
                    )
                )
            else:
                content = None
            changes.append(
                Change(
                    path=path,
                    before_sha256=None if before is None else sha256(before),
                    after=encode(content),
                    mode=filesystem.mode(path),
                )
            )
        materialization = Materialization(
            profile=host.id,
            profile_version="1",
            materialization_digest="sha256:" + "0" * 64,
            files=managed,
            managed_entrypoint_base_sha256=sha256(root_block),
            local_segment_sha256=sha256(local),
        )
        materialization = materialization.model_copy(
            update={
                "materialization_digest": materialization_digest(
                    bundle.identity.digest, materialization
                )
            }
        )
        lock = ContextLock(
            **bundle.identity.model_dump(),
            descriptor_sha256=sha256(bundle.files[".futureagi/context.json"]),
            files=[
                FileMeta(path=p, sha256=sha256(b), size_bytes=len(b))
                for p, b in sorted(bundle.files.items())
            ],
            materialization=materialization,
        )
        changes.append(
            Change(
                path=CONTEXT_LOCK,
                before_sha256=None if previous_raw is None else sha256(previous_raw),
                after=encode(lock.to_bytes()),
            )
        )
        plan = create_plan(
            operation=operation,
            project=str(filesystem.path),
            lock_path=CONTEXT_LOCK,
            previous_lock=encode(previous_raw),
            changes=[c.model_dump() for c in changes],
            authorizations=[authorization.model_dump()],
            preserved=[],
            warnings=[
                "Preview profile: native discovery and model delivery are not observed.",
                "Stop clients and writers before applying; multi-path writes are not globally atomic.",
                "Existing local and nested instructions remain additional effective context.",
            ],
        )
        if len(plan.to_bytes()) > 16 * 1024 * 1024:
            raise InstallationError(
                "plan_too_large", "Plan exceeds the bounded staging limit.", 6
            )
        return plan


def plan_remove(*, project: str | Path) -> InstallPlan:
    """Remove only unchanged managed bytes/segments; retain all local exceptions."""
    with SafeProject(project) as filesystem:
        raw = filesystem.read(CONTEXT_LOCK)
        if raw is None:
            raise InstallationError("lock_missing", "No context ownership lock exists.")
        lock = parse_lock(raw)
        validate_lock_layout(lock)
        changes: list[Change] = []
        owned = {f.destination for f in lock.materialization.files}
        preserved: list[str] = sorted(
            set().union(*(filesystem.files_under(root) for root in managed_roots(lock)))
            - owned
        )
        for file in sorted(lock.materialization.files, key=lambda f: f.destination):
            content = filesystem.read(file.destination)
            after = content
            if content is None:
                continue
            if file.transformation == "copy":
                if sha256(content) == file.sha256:
                    after = None
                else:
                    preserved.append(file.destination)
            else:
                try:
                    prefix, block, suffix = split_managed(content, lock.context_id)
                    expected = (
                        lock.materialization.managed_entrypoint_base_sha256
                        if file.transformation == "entrypoint"
                        else sha256(managed_block(lock.context_id, IMPORT))
                    )
                    if sha256(block) != expected:
                        raise InstallationError(
                            "local_modifications", "Managed segment changed."
                        )
                    after = prefix + suffix
                    if not after and file.ownership == "managed":
                        after = None
                except InstallationError:
                    preserved.append(file.destination)
            changes.append(
                Change(
                    path=file.destination,
                    before_sha256=sha256(content),
                    after=encode(after),
                    mode=filesystem.mode(file.destination),
                )
            )
        changes.append(Change(path=CONTEXT_LOCK, before_sha256=sha256(raw), after=None))
        return create_plan(
            operation="remove",
            project=str(filesystem.path),
            lock_path=CONTEXT_LOCK,
            previous_lock=encode(raw),
            changes=[c.model_dump() for c in changes],
            authorizations=[],
            preserved=preserved,
            warnings=[
                "Modified/unowned files are retained. Credentials are not revoked by removal.",
                "Empty directories may remain; no unowned directories are removed.",
            ],
        )


def _validate_context_plan(plan: InstallPlan) -> SourceBundle | None:
    previous_raw = decode(plan.previous_lock)
    old = parse_lock(previous_raw) if previous_raw is not None else None
    if old is not None:
        validate_lock_layout(old)
    new_raw = plan.changes[-1].after_bytes
    new = parse_lock(new_raw) if new_raw is not None else None
    if new is not None:
        validate_lock_layout(new)
    if plan.operation == "remove":
        if old is None or new is not None or plan.authorizations:
            raise InstallationError(
                "plan_invalid", "Invalid removal ownership or authorization.", 6
            )
    elif new is None or len(plan.authorizations) != 1:
        raise InstallationError(
            "plan_invalid", "Installation requires its exact source and lease.", 6
        )
    allowed = {CONTEXT_LOCK}
    for lock in (old, new):
        if lock is not None:
            allowed.update(f.destination for f in lock.materialization.files)
    changes = {c.path: c for c in plan.changes}
    if not set(changes).issubset(allowed):
        raise InstallationError(
            "destination_forbidden",
            "Plan includes a destination not owned by its profile.",
            6,
        )
    if new is not None:
        auth = plan.authorizations[0]
        if (
            not isinstance(auth.identity, Identity)
            or auth.kind != "agent_context"
            or auth.identity.model_dump()
            != {k: v for k, v in new.model_dump().items() if k in Identity.model_fields}
        ):
            raise InstallationError(
                "plan_invalid", "Authorization and installed identity differ.", 6
            )
        files: dict[str, bytes] = {}
        for meta in new.files:
            path = generation_path(new.digest) + "/" + meta.path
            if path not in changes or changes[path].after_bytes is None:
                raise InstallationError(
                    "plan_invalid", "Missing canonical plan content.", 6
                )
            files[meta.path] = changes[path].require_content()
        bundle = SourceBundle(identity=auth.identity, lease=auth.lease, files=files)
        expected = _projected(bundle, get_profile(new.materialization.profile))
        for output in new.materialization.files:
            change = changes.get(output.destination)
            if change is None or change.after_sha256 != output.sha256:
                raise InstallationError(
                    "plan_invalid", "Plan output differs from its ownership lock.", 6
                )
            if output.transformation != "copy":
                _, block, _ = split_managed(change.require_content(), new.context_id)
                if block != expected[output.destination][0]:
                    raise InstallationError(
                        "plan_invalid",
                        "Managed instruction bytes differ from the source projection.",
                        6,
                    )
        return bundle
    return None


def apply_plan(
    plan: InstallPlan, *, authorize: Callable[[Authorization], None], quiescent: bool
) -> None:
    plan = parse_plan(plan.to_bytes())
    if plan.lock_path != CONTEXT_LOCK:
        raise InstallationError(
            "plan_invalid", "Use the standalone-skill installer for a skill plan.", 6
        )
    bundle = _validate_context_plan(plan)

    # Recompute the plan from current source/ownership, not just a caller's digest.
    # This also prevents a hand-edited removal plan from deleting a dirty file.
    def recheck() -> None:
        if plan.operation == "remove":
            current = plan_remove(project=plan.project)
        else:
            new = parse_lock(plan.changes[-1].require_content())
            if bundle is None:
                raise InstallationError(
                    "plan_invalid", "Missing installation source.", 6
                )
            current = plan_install(
                bundle,
                project=plan.project,
                profile=new.materialization.profile,
                adopt_local=True,
                allow_preview=True,
                operation=plan.operation,
            )
        if current.plan_digest != plan.plan_digest:
            raise InstallationError(
                "stale_plan",
                "The reviewed plan no longer matches current ownership/preimages.",
            )

    transact(plan, authorize=authorize, recheck=recheck, quiescent=quiescent)


def inspect_plan(plan: InstallPlan, *, include_diff: bool = False) -> dict[str, object]:
    """Inspect exact preimage-bound text locally, without credentials or execution.

    Diff output is opt-in because it contains source/local text. Each preview is
    bounded and explicitly reports truncation; hashes always cover complete bytes.
    """
    import difflib

    plan = parse_plan(plan.to_bytes())
    result = plan.review()
    if not include_diff:
        return result
    previews: list[dict[str, object]] = []
    with SafeProject(plan.project) as filesystem:
        for change in plan.changes:
            before = filesystem.read(change.path)
            if (None if before is None else sha256(before)) != change.before_sha256:
                raise InstallationError(
                    "stale_plan",
                    "Local preimages changed; inspect a newly reviewed plan.",
                )
            after = change.after_bytes
            if before == after:
                continue
            difference = "".join(
                difflib.unified_diff(
                    (before or b"").decode("utf-8").splitlines(keepends=True),
                    (after or b"").decode("utf-8").splitlines(keepends=True),
                    fromfile="before/" + change.path,
                    tofile="after/" + change.path,
                )
            )
            preview = difference[:32768]
            previews.append(
                {
                    "path": change.path,
                    "diff": preview,
                    "truncated": len(preview) != len(difference),
                    "omitted_characters": len(difference) - len(preview),
                }
            )
    result["diffs"] = previews
    return result


def verify(
    *, project: str | Path, lock: ContextLock | None = None
) -> dict[str, object]:
    """Read-only checked-in byte verification. No project code or network runs."""
    with SafeProject(project) as filesystem:
        if lock is None:
            raw = filesystem.read(CONTEXT_LOCK)
            if raw is None:
                raise InstallationError("lock_missing", "No context lock exists.", 6)
            lock = parse_lock(raw)
        validate_lock_layout(lock)
        owned = {f.destination for f in lock.materialization.files}
        extras = (
            set().union(*(filesystem.files_under(root) for root in managed_roots(lock)))
            - owned
        )
        differences = [{"path": path, "state": "unexpected"} for path in sorted(extras)]
        for file in lock.materialization.files:
            content = filesystem.read(file.destination)
            if content is None or sha256(content) != file.sha256:
                differences.append(
                    {
                        "path": file.destination,
                        "state": "missing" if content is None else "changed",
                    }
                )
        return {
            "schema": 1,
            "verified": not differences,
            "differences": differences,
            "version_id": lock.version_id,
            "digest": lock.digest,
            "materialization_digest": lock.materialization.materialization_digest,
            "scope": "checked_in_bytes_only",
            "authorization": "not_checked",
            "discovery": "not_observed",
            "delivery": "not_observed",
        }
