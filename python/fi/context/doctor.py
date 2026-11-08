"""Read-only installation diagnostics; no host binaries or repository code run."""

from __future__ import annotations

import os
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
        for root, directories, files in os.walk(path, followlinks=False):
            directories[:] = sorted(
                name
                for name in directories
                if name not in EXCLUDED and not (Path(root) / name).is_symlink()
            )
            count += len(directories) + len(files)
            if count > 10000:
                findings.append(
                    {
                        "code": "inventory_incomplete",
                        "reason": "Local inventory exceeds 10000 entries.",
                    }
                )
                break
            for name in sorted(set(files) & INSTRUCTION_NAMES):
                relative = (Path(root) / name).relative_to(path).as_posix()
                try:
                    content = filesystem.read(relative)
                    findings.append(
                        {
                            "code": (
                                "additional_instructions"
                                if "/" in relative
                                or name not in {"AGENTS.md", "CLAUDE.md"}
                                else "project_instructions"
                            ),
                            "path": relative,
                            "sha256": None if content is None else sha256(content),
                        }
                    )
                except InstallationError as exc:
                    findings.append({"code": exc.code, "path": relative})
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
        "findings": findings,
        "recovery_required": existing_journal(str(path)),
        "native_qualification": "not_qualified",
        "discovery": "not_observed",
        "delivery": "not_observed",
        "host_configuration": "not_inspected",
        "next_action": "Use pinned native-host diagnostics in a clean, consented session; model self-report is insufficient.",
    }
