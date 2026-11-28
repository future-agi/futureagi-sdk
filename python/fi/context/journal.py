"""POSIX, no-follow filesystem access and recoverable, lock-last transactions.

This serializes cooperating installers. It does not make multi-path writes
atomic for live editors: callers must stop/quiesce readers and other writers.
Journals/backups are private and outside the repository/distributable lock.
"""

from __future__ import annotations

import base64
import errno
import json
import os
import stat
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator, Literal
from uuid import uuid4

from pydantic import Field, field_validator, model_validator

from .lock import (
    MAX_DOCUMENT_BYTES,
    FrozenModel,
    Identity,
    InstallationError,
    Lease,
    SkillIdentity,
    canonical_json,
    collision_key,
    hash_value,
    sha256,
    validate_path,
    validate_paths,
)

SKILLS_OWNERSHIP = ".futureagi/skills/ownership.json"


class SafeProject:
    """All project access is relative to no-follow directory file descriptors."""

    def __init__(self, project: str | Path):
        if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
            raise InstallationError(
                "platform_unsupported",
                "Installation requires POSIX no-follow filesystem operations.",
                7,
            )
        self.path = Path(os.path.abspath(project))
        self.fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
        try:
            for part in self.path.parts[1:]:
                fd = os.open(
                    part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=self.fd
                )
                os.close(self.fd)
                self.fd = fd
        except OSError as exc:
            os.close(self.fd)
            raise InstallationError(
                "destination_forbidden",
                "Project or ancestor is missing, not a directory, or a symlink.",
            ) from exc

    def __enter__(self) -> SafeProject:
        return self

    def __exit__(self, *args: object) -> None:
        os.close(self.fd)

    @staticmethod
    def _check_case(fd: int, name: str) -> None:
        if any(
            entry != name and collision_key(entry) == collision_key(name)
            for entry in os.listdir(fd)
        ):
            raise InstallationError(
                "path_collision", "Destination has a case/Unicode-colliding name."
            )

    @contextmanager
    def parent(self, path: str, *, create: bool = False) -> Iterator[tuple[int, str]]:
        parts = validate_path(path).split("/")
        fd = os.dup(self.fd)
        try:
            for part in parts[:-1]:
                self._check_case(fd, part)
                if create:
                    try:
                        os.mkdir(part, 0o755, dir_fd=fd)
                        os.fsync(fd)
                    except FileExistsError:
                        pass
                next_fd = os.open(
                    part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
                )
                os.close(fd)
                fd = next_fd
            self._check_case(fd, parts[-1])
            yield fd, parts[-1]
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                raise InstallationError(
                    "destination_forbidden",
                    "A destination traverses a symlink or a non-directory.",
                ) from exc
            raise
        finally:
            os.close(fd)

    def read(self, path: str, *, limit: int = MAX_DOCUMENT_BYTES) -> bytes | None:
        try:
            with self.parent(path) as (parent, name):
                try:
                    fd = os.open(
                        name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
                    )
                except FileNotFoundError:
                    return None
                except OSError as exc:
                    if exc.errno == errno.ELOOP:
                        raise InstallationError(
                            "destination_forbidden", "A destination is a symlink."
                        ) from exc
                    raise
                with os.fdopen(fd, "rb") as stream:
                    info = os.fstat(stream.fileno())
                    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                        raise InstallationError(
                            "destination_forbidden",
                            "A destination is not a single-link regular file.",
                        )
                    if info.st_size > limit:
                        raise InstallationError(
                            "file_too_large",
                            "A local file exceeds its safe read limit.",
                            6,
                        )
                    content = stream.read(limit + 1)
                    if len(content) > limit:
                        raise InstallationError(
                            "file_too_large",
                            "A local file exceeds its safe read limit.",
                            6,
                        )
                    return content
        except FileNotFoundError:
            return None

    def files_under(self, path: str) -> set[str]:
        """Inventory one owned root without following links or opening payloads."""
        result: set[str] = set()
        visited = 0

        def walk(fd: int, prefix: str, depth: int) -> None:
            nonlocal visited
            names = os.listdir(fd)
            if len({collision_key(n) for n in names}) != len(names):
                raise InstallationError(
                    "path_collision", "Managed tree has case/Unicode-colliding entries."
                )
            for name in sorted(names):
                visited += 1
                if visited > 10000 or depth > 16:
                    raise InstallationError(
                        "inventory_too_large",
                        "Local managed-tree inventory exceeds its limit.",
                        6,
                    )
                relative = prefix + "/" + name
                validate_path(relative)
                info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    child = os.open(
                        name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
                    )
                    try:
                        walk(child, relative, depth + 1)
                    finally:
                        os.close(child)
                elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                    result.add(relative)
                else:
                    raise InstallationError(
                        "destination_forbidden",
                        "Managed tree contains a symlink, hardlink, or special file.",
                    )

        try:
            with self.parent(path) as (parent, name):
                fd = os.open(
                    name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent
                )
                try:
                    walk(fd, path, 0)
                finally:
                    os.close(fd)
        except FileNotFoundError:
            return set()
        except OSError as exc:
            if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                raise InstallationError(
                    "destination_forbidden", "Managed root is not a real directory."
                ) from exc
            raise
        return result

    def mode(self, path: str) -> int:
        try:
            with self.parent(path) as (parent, name):
                info = os.stat(name, dir_fd=parent, follow_symlinks=False)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise InstallationError(
                        "destination_forbidden", "Unsafe local file type."
                    )
                return stat.S_IMODE(info.st_mode) & 0o777
        except FileNotFoundError:
            return 0o644

    def replace(self, path: str, content: bytes | None, *, mode: int = 0o644) -> None:
        with self.parent(path, create=content is not None) as (parent, name):
            if content is None:
                try:
                    os.unlink(name, dir_fd=parent)
                    os.fsync(parent)
                except FileNotFoundError:
                    pass
                return
            temp = f".fi-{uuid4().hex}.tmp"
            fd = os.open(
                temp,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=parent,
            )
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(content)
                    stream.flush()
                    os.fchmod(stream.fileno(), mode)
                    os.fsync(stream.fileno())
                os.replace(temp, name, src_dir_fd=parent, dst_dir_fd=parent)
                os.fsync(parent)
            finally:
                try:
                    os.unlink(temp, dir_fd=parent)
                except FileNotFoundError:
                    pass


def encode(content: bytes | None) -> str | None:
    return None if content is None else base64.b64encode(content).decode("ascii")


def decode(content: str | None) -> bytes | None:
    if content is None:
        return None
    try:
        value = base64.b64decode(content, validate=True)
    except ValueError as exc:
        raise InstallationError(
            "plan_invalid", "Plan contains invalid binary encoding.", 6
        ) from exc
    if len(value) > MAX_DOCUMENT_BYTES:
        raise InstallationError(
            "plan_invalid", "Plan content exceeds the byte limit.", 6
        )
    return value


class Change(FrozenModel):
    path: str
    before_sha256: str | None
    after: str | None = Field(repr=False)
    mode: int = Field(default=0o644, ge=0, le=0o777)

    @field_validator("path")
    @classmethod
    def path_valid(cls, value: str) -> str:
        return validate_path(value)

    @field_validator("before_sha256")
    @classmethod
    def before_valid(cls, value: str | None) -> str | None:
        return None if value is None else hash_value(value)

    @field_validator("after")
    @classmethod
    def after_valid(cls, value: str | None) -> str | None:
        decode(value)
        return value

    @property
    def after_bytes(self) -> bytes | None:
        return decode(self.after)

    @property
    def after_sha256(self) -> str | None:
        content = self.after_bytes
        return None if content is None else sha256(content)

    def require_content(self) -> bytes:
        content = self.after_bytes
        if content is None:
            raise InstallationError(
                "plan_invalid", "Required planned content is missing.", 6
            )
        return content


class Authorization(FrozenModel):
    kind: Literal["agent_context", "skill"]
    identity: Identity | SkillIdentity
    lease: Lease

    @model_validator(mode="after")
    def kind_matches_identity(self) -> Authorization:
        if (self.kind == "agent_context") != isinstance(self.identity, Identity):
            raise ValueError("Resource kind and authorization identity differ")
        return self


class InstallPlan(FrozenModel):
    schema_version: Literal[1] = 1
    operation: Literal["install", "update", "restore", "remove"]
    project: str
    lock_path: Literal[".futureagi-context.lock.json", ".futureagi-skills.lock.json"]
    previous_lock: str | None = Field(repr=False)
    changes: list[Change] = Field(min_length=1, max_length=25000)
    authorizations: list[Authorization] = Field(max_length=50)
    preserved: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    plan_digest: str

    @model_validator(mode="after")
    def valid(self) -> InstallPlan:
        validate_paths([c.path for c in self.changes])
        if (
            not os.path.isabs(self.project)
            or os.path.abspath(self.project) != self.project
        ):
            raise ValueError("Plan project must be canonical and absolute")
        if self.changes[-1].path != self.lock_path:
            raise ValueError("Lock must be committed last")
        previous = decode(self.previous_lock)
        if self.changes[-1].before_sha256 != (
            None if previous is None else sha256(previous)
        ):
            raise ValueError("Previous lock preimage mismatch")
        value = self.model_dump(exclude={"plan_digest"})
        if self.plan_digest != "sha256:" + sha256(canonical_json(value)):
            raise ValueError("Plan digest mismatch")
        return self

    def to_bytes(self) -> bytes:
        return canonical_json(self.model_dump())

    def review(self) -> dict[str, object]:
        return {
            "schema": 1,
            "operation": self.operation,
            "plan_digest": self.plan_digest,
            "changes": [
                {
                    "path": c.path,
                    "before_sha256": c.before_sha256,
                    "after_sha256": c.after_sha256,
                    "action": (
                        "unchanged"
                        if c.before_sha256 == c.after_sha256
                        else (
                            "remove"
                            if c.after is None
                            else "add" if c.before_sha256 is None else "replace"
                        )
                    ),
                }
                for c in self.changes
            ],
            "preserved": self.preserved,
            "warnings": self.warnings,
            "delivery": "not_observed",
            "globally_atomic": False,
        }


def create_plan(**kwargs: object) -> InstallPlan:
    return InstallPlan.model_validate(
        {
            **kwargs,
            "plan_digest": "sha256:"
            + sha256(canonical_json({"schema_version": 1, **kwargs})),
        }
    )


def parse_plan(raw: bytes) -> InstallPlan:
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise InstallationError("plan_invalid", "Plan exceeds its size limit.", 6)
    try:
        return InstallPlan.model_validate(json.loads(raw))
    except (ValueError, TypeError) as exc:
        raise InstallationError(
            "plan_invalid", "Invalid or modified install plan.", 6
        ) from exc


def existing_journal(project: str) -> bool:
    root = Path.home() / ".local" / "state" / "futureagi-install"
    path = root / sha256(project.encode()) / "journal.json"
    return path.exists() or path.is_symlink()


def state_directory(project: str) -> Path:
    root = Path.home() / ".local" / "state" / "futureagi-install"
    # Check each ancestor before creating anything; even a missing state directory
    # must never be created through a preexisting .local symlink.
    with SafeProject(Path.home()) as home:
        with home.parent(".local/state/futureagi-install", create=True) as (
            parent,
            name,
        ):
            try:
                os.mkdir(name, 0o700, dir_fd=parent)
            except FileExistsError:
                pass
    for path in (root, root / sha256(project.encode())):
        with SafeProject(path.parent) as parent:
            try:
                os.mkdir(path.name, 0o700, dir_fd=parent.fd)
            except FileExistsError:
                pass
            info = os.stat(path.name, dir_fd=parent.fd, follow_symlinks=False)
            if (
                not stat.S_ISDIR(info.st_mode)
                or info.st_uid != os.getuid()
                or info.st_mode & 0o077
            ):
                raise InstallationError(
                    "state_directory_unsafe",
                    "Installer private state directory has unsafe permissions.",
                    3,
                )
    return root / sha256(project.encode())


@contextmanager
def installation_lock(project: str) -> Iterator[Path]:
    import fcntl

    directory = state_directory(project)
    fd = os.open(directory / "mutex", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode) or os.fstat(fd).st_nlink != 1:
            raise InstallationError(
                "state_directory_unsafe", "Unsafe installation mutex.", 3
            )
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise InstallationError(
                "installation_busy", "Another installer owns this project lock."
            ) from exc
        yield directory
    finally:
        os.close(fd)


def _write_private(path: Path, raw: bytes) -> None:
    temp = path.with_name(f".{uuid4().hex}.tmp")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        temp.unlink(missing_ok=True)


def write_plan(path: Path, plan: InstallPlan) -> None:
    """Write an explicit private plan without overwriting a preexisting file."""
    absolute = Path(os.path.abspath(path))
    with SafeProject(absolute.parent) as parent:
        fd = os.open(
            absolute.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=parent.fd,
        )
        with os.fdopen(fd, "wb") as stream:
            stream.write(plan.to_bytes())
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(parent.fd)


def _matches(content: bytes | None, expected: str | None) -> bool:
    return (None if content is None else sha256(content)) == expected


def transact(
    plan: InstallPlan,
    *,
    authorize: Callable[[Authorization], None],
    recheck: Callable[[], None],
    quiescent: bool,
) -> None:
    """Internal journal executor; callers validate profile/lock ownership first."""
    if not quiescent:
        raise InstallationError(
            "quiescence_required",
            "Stop clients and other writers, then explicitly acknowledge quiescence.",
            3,
        )
    with installation_lock(plan.project) as directory, SafeProject(
        plan.project
    ) as project:
        journal = directory / "journal.json"
        if journal.exists() or journal.is_symlink():
            raise InstallationError(
                "recovery_required",
                "An incomplete installation must be recovered first.",
            )
        before = []
        for change in plan.changes:
            current = project.read(change.path)
            if not _matches(current, change.before_sha256):
                raise InstallationError(
                    "stale_plan", "Local preimages changed; review a new plan."
                )
            before.append(
                {
                    "path": change.path,
                    "content": encode(current),
                    "mode": project.mode(change.path),
                }
            )
        for auth in plan.authorizations:
            auth.lease.require_live()
            authorize(auth)
            auth.lease.require_live()
        # Network latency cannot let a plan silently overwrite intervening edits.
        for change in plan.changes:
            if not _matches(project.read(change.path), change.before_sha256):
                raise InstallationError(
                    "stale_plan", "Files changed during authorization; replan."
                )
        # Inventory/ownership must also be rechecked under the cooperative lock.
        recheck()
        # One durable, fully staged journal before any repository mutation.
        journal_bytes = canonical_json(
            {"schema": 1, "plan": plan.model_dump(), "before": before}
        )
        if len(journal_bytes) > MAX_DOCUMENT_BYTES:
            raise InstallationError(
                "plan_too_large",
                "Staged bytes and backups exceed the recovery journal limit.",
                6,
            )
        _write_private(journal, journal_bytes)
        try:
            for change in plan.changes:
                for auth in plan.authorizations:
                    auth.lease.require_live()
                if not _matches(project.read(change.path), change.before_sha256):
                    raise InstallationError(
                        "stale_plan",
                        "A file changed during apply; recover before replanning.",
                    )
                if change.after_sha256 != change.before_sha256:
                    project.replace(change.path, change.after_bytes, mode=change.mode)
                if not _matches(project.read(change.path), change.after_sha256):
                    raise InstallationError(
                        "integrity_failure", "Installed bytes do not match the plan.", 6
                    )
            journal.unlink()
        except (OSError, InstallationError) as exc:
            raise InstallationError(
                "recovery_required",
                "Installation is incomplete. Retained backups require explicit recovery.",
            ) from exc


def recover(project_path: str | Path, *, quiescent: bool) -> dict[str, object]:
    """Rollback an incomplete local write without a registry request or overwrite.

    If the lock and every planned output committed, finish journal cleanup instead.
    Unknown/edited bytes prevent *all* rollback writes until explicitly reconciled.
    """
    if not quiescent:
        raise InstallationError(
            "quiescence_required", "Recovery requires stopped clients and writers.", 3
        )
    path = os.path.abspath(project_path)
    with installation_lock(path) as directory, SafeProject(path) as project:
        journal_path = directory / "journal.json"
        if not journal_path.exists() and not journal_path.is_symlink():
            return {"schema": 1, "state": "no_recovery_needed"}
        with SafeProject(directory) as private:
            raw = private.read("journal.json")
        if raw is None:
            raise InstallationError("journal_invalid", "Missing recovery journal.", 6)
        try:
            value = json.loads(raw)
            plan = InstallPlan.model_validate(value["plan"])
            backups = value["before"]
            if plan.project != path or len(backups) != len(plan.changes):
                raise ValueError("Wrong recovery project or inventory")
            for change, backup in zip(plan.changes, backups):
                if backup["path"] != change.path or not _matches(
                    decode(backup["content"]), change.before_sha256
                ):
                    raise ValueError("Backup integrity mismatch")
                if type(backup["mode"]) is not int or not 0 <= backup["mode"] <= 0o777:
                    raise ValueError("Invalid backup mode")
        except (KeyError, TypeError, ValueError) as exc:
            raise InstallationError(
                "journal_invalid", "Recovery journal failed integrity validation.", 6
            ) from exc
        current = [project.read(c.path) for c in plan.changes]
        for change, content in zip(plan.changes, current):
            if not _matches(content, change.before_sha256) and not _matches(
                content, change.after_sha256
            ):
                raise InstallationError(
                    "recovery_conflict",
                    "Local changes intersect the journal; preserve them before recovery.",
                )
        committed = all(
            _matches(content, c.after_sha256)
            for content, c in zip(current, plan.changes)
        )
        if not committed:
            for change, backup in reversed(list(zip(plan.changes, backups))):
                content = project.read(change.path)
                if _matches(content, change.before_sha256):
                    continue
                if not _matches(content, change.after_sha256):
                    raise InstallationError(
                        "recovery_conflict", "A file changed during recovery."
                    )
                project.replace(
                    change.path, decode(backup["content"]), mode=backup["mode"]
                )
        journal_path.unlink()
        return {
            "schema": 1,
            "state": "committed" if committed else "rolled_back",
            "delivery": "not_observed",
        }
