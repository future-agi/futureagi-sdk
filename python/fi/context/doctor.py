"""Read-only installation diagnostics; no host binaries or repository code run."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from .journal import SafeProject
from .lock import CONTEXT_LOCK, InstallationError, sha256
from .materialize import verify

INSTRUCTION_NAMES = {
    "AGENTS.md",
    "AGENTS.override.md",
    "CLAUDE.md",
    "CLAUDE.local.md",
    "GEMINI.md",
}
EXCLUDED = {".git", "node_modules", ".venv", "venv", ".futureagi"}


def doctor(*, project: str | Path) -> dict[str, object]:
    path = Path(os.path.abspath(project))
    findings: list[dict[str, object]] = []
    with SafeProject(path) as filesystem:
        raw = filesystem.read(CONTEXT_LOCK)
        if raw is not None:
            try:
                verification = verify(project=path)
            except InstallationError as exc:
                verification = {"verified": False, "code": exc.code}
        else:
            verification = {"verified": False, "code": "lock_missing"}
        count = 0
        complete = True

        def incomplete(relative: str, reason: str) -> None:
            nonlocal complete
            complete = False
            findings.append(
                {"code": "inventory_incomplete", "path": relative, "reason": reason}
            )

        def walk(fd: int, prefix: str = "", depth: int = 0) -> None:
            nonlocal count
            # Traverse anchored no-follow descriptors. os.walk silently suppresses
            # permission errors and can traverse a directory replaced by a symlink.
            try:
                with os.scandir(fd) as entries:
                    names = []
                    for entry in entries:
                        count += 1
                        if count > 10000:
                            incomplete(prefix, "Local inventory exceeds 10000 entries.")
                            return
                        names.append(entry.name)
                for name in sorted(names):
                    relative = f"{prefix}/{name}" if prefix else name
                    info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                    if stat.S_ISDIR(info.st_mode):
                        if name in EXCLUDED:
                            continue
                        if depth >= 16:
                            incomplete(relative, "Local inventory exceeds 16 levels.")
                            continue
                        try:
                            child = os.open(
                                name,
                                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                dir_fd=fd,
                            )
                        except OSError:
                            incomplete(
                                relative,
                                "Directory unavailable or changed during inventory.",
                            )
                            continue
                        try:
                            walk(child, relative, depth + 1)
                        finally:
                            os.close(child)
                        if count > 10000:
                            return
                    elif stat.S_ISLNK(info.st_mode):
                        # The target may contain effective instructions. Never
                        # silently omit it or read outside the selected repository.
                        incomplete(relative, "Symlink target was not inspected.")
                    elif name in INSTRUCTION_NAMES:
                        try:
                            content = filesystem.read(relative)
                            if content is None:
                                incomplete(
                                    relative,
                                    "Instruction disappeared during inventory.",
                                )
                                continue
                            findings.append(
                                {
                                    "code": (
                                        "additional_instructions"
                                        if "/" in relative
                                        or name not in {"AGENTS.md", "CLAUDE.md"}
                                        else "project_instructions"
                                    ),
                                    "path": relative,
                                    "sha256": sha256(content),
                                }
                            )
                        except (InstallationError, OSError):
                            incomplete(relative, "Instruction cannot be safely read.")
            except OSError:
                incomplete(prefix, "Directory unavailable or changed during inventory.")

        walk(filesystem.fd)
        # Ancestors can change precedence. Record relative distance, never their text
        # or absolute personal paths. Reading a root is not a delivery observation.
        for distance, ancestor in enumerate(path.parents, start=1):
            for name in sorted(INSTRUCTION_NAMES):
                if (ancestor / name).exists() or (ancestor / name).is_symlink():
                    findings.append(
                        {
                            "code": "ancestor_instructions",
                            "ancestor_distance": distance,
                            "name": name,
                        }
                    )
    # Do not create state directories during a read-only doctor command.
    from .journal import existing_journal

    return {
        "schema": 1,
        "verification": verification,
        "lock_sha256": None if raw is None else sha256(raw),
        "inventory_complete": complete,
        "excluded_directories": sorted(EXCLUDED),
        "findings": findings,
        "recovery_required": existing_journal(str(path)),
        "native_qualification": "not_qualified",
        "discovery": "not_observed",
        "delivery": "not_observed",
        "host_configuration": "not_inspected",
        "next_action": "Use pinned native-host diagnostics in a clean, consented session; model self-report is insufficient.",
    }
