"""Read-only, fixed repository inventory for explicit local ownership review.

Inputs are selected local checkouts, not discovery roots or commands. No git,
repository hooks, registry requests or host binaries run. An unavailable target
remains in the inventory; it never silently shrinks the selected population.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from .doctor import doctor
from .lock import InstallationError, canonical_json, sha256


def inventory_repositories(repositories: object) -> dict[str, object]:
    """Inspect 1–100 explicitly selected checkouts, with no mutation or adoption.

    Each input has exactly ``repository_id`` (stable GitHub numeric ID) and
    ``project`` (absolute checkout path). Output omits personal absolute paths
    and instruction text. The digest binds local observations, not a remote Git
    attestation or an authorization to replace/adopt instructions.
    """
    if not isinstance(repositories, list) or not 1 <= len(repositories) <= 100:
        raise InstallationError("invalid_inventory", "Select 1–100 repositories.", 2)
    selected: list[tuple[str, str]] = []
    ids: set[str] = set()
    paths: set[str] = set()
    for row in repositories:
        if not isinstance(row, dict) or set(row) != {"repository_id", "project"}:
            raise InstallationError(
                "invalid_inventory", "Supply repository_id and project only.", 2
            )
        repository_id, project = row["repository_id"], row["project"]
        if (
            not isinstance(repository_id, str)
            or not re.fullmatch(r"[1-9][0-9]{0,19}", repository_id)
            or not isinstance(project, str)
            or not Path(project).is_absolute()
            or "\x00" in project
        ):
            raise InstallationError(
                "invalid_inventory",
                "Use a numeric repository ID and absolute project path.",
                2,
            )
        normalized = os.path.abspath(project)
        if repository_id in ids or normalized in paths:
            raise InstallationError(
                "invalid_inventory",
                "Select every repository and checkout exactly once.",
                2,
            )
        ids.add(repository_id)
        paths.add(normalized)
        selected.append((repository_id, normalized))
    targets = []
    for repository_id, project in sorted(selected):
        try:
            observation = doctor(project=project)
            targets.append(
                {
                    "repository_id": repository_id,
                    "state": "inventoried"
                    if observation["inventory_complete"]
                    else "review_required",
                    "observation": observation,
                    "ownership": "not_authorized",
                }
            )
        except (InstallationError, OSError) as exc:
            # Error strings may contain private paths; retain only bounded codes.
            code = (
                exc.code
                if isinstance(exc, InstallationError)
                else "repository_unavailable"
            )
            targets.append(
                {"repository_id": repository_id, "state": "unavailable", "code": code}
            )
    result = {"schema": 1, "targets": targets, "target_count": len(targets)}
    return {**result, "inventory_digest": "sha256:" + sha256(canonical_json(result))}
