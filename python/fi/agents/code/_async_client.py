"""Default-off authored agent definitions using the shared async platform transport."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ..definition import (
    diff,
    digest,
    integer,
    invalid,
    object_,
    project,
    text,
    validate,
)
from ..files import MISSING, locked, read_json, write_json

LOCK_SCHEMA = "futureagi-agent-lock/v1"


def require_enabled() -> None:
    if os.environ.get("FI_AGENT_CODE_ENABLED") != "1":
        invalid(
            "Agent-as-code is disabled. This preview requires FI_AGENT_CODE_ENABLED=1.",
            "agent_code_disabled",
        )


class AsyncAgentCode:
    """Manage authored definitions only; apply never starts, releases or runs an agent.

    File mutations require a POSIX host. Locks fail immediately on contention and a
    pending journal prevents blindly retrying an ambiguous server write.
    """

    def __init__(self, client: Any) -> None:
        self.client = client

    def validate(self, document: Any) -> dict:
        """Validate locally without network or file access; backend references are not checked."""
        require_enabled()
        return validate(document)

    def _target(self) -> dict:
        require_enabled()
        origin = self.client._platform.shared.origin()
        headers = {k.lower(): v for k, v in origin.headers.items()}
        org = headers.get("x-organization-id") or headers.get("x-omega-org")
        workspace = headers.get("x-workspace-id") or headers.get("x-omega-workspace")
        if not org or not workspace:
            invalid(
                "Agent-as-code requires explicit organization_id and workspace_id selectors.",
                "agent_target_required",
            )
        return {"origin": origin.base, "organizationId": org, "workspaceId": workspace}

    async def _call(self, operation: str, **kwargs: Any) -> Any:
        return await self.client._platform.call(
            "platform.agents." + operation, **kwargs
        )

    async def _read(self, agent_id: str) -> tuple:
        return project(await self._call("get", path={"id": agent_id}), agent_id)

    def _lock(self, path: str | Path, target: dict) -> Any:
        state = read_json(path, missing=True)
        if state is MISSING:
            return None
        if not isinstance(state, dict):
            invalid(
                "Malformed agent lockfile; expected a JSON object.",
                "agent_lock_invalid",
            )
        object_(
            state,
            {"schemaVersion", "target", "status"},
            {"agentId", "version", "definition", "digest"},
        )
        if state["schemaVersion"] != LOCK_SCHEMA or state["target"] != target:
            invalid(
                "Lockfile belongs to a different backend, organization or workspace. Use a new lockfile; --force cannot retarget it.",
                "agent_target_mismatch",
            )
        if state["status"] == "pending":
            invalid(
                "Previous apply has an unresolved outcome. Inspect the Console and import its agent ID using a NEW lockfile; do not retry creation or discard this journal.",
                "agent_apply_pending",
            )
        if state["status"] != "applied" or set(state) != {
            "schemaVersion",
            "target",
            "status",
            "agentId",
            "version",
            "definition",
            "digest",
        }:
            invalid("Malformed agent lockfile.", "agent_lock_invalid")
        text(state["agentId"], 256)
        integer(state["version"])
        if (
            validate(state["definition"]) != state["definition"]
            or digest(state["definition"]) != state["digest"]
        ):
            invalid(
                "Lockfile definition or digest is inconsistent.", "agent_lock_invalid"
            )
        return state

    async def _plan(self, document: Any, lock_path: str | Path) -> tuple:
        desired = self.validate(document)
        target = self._target()
        state = self._lock(lock_path, target)
        if state is None:
            roster = await self._call("roster")
            if (
                not isinstance(roster, dict)
                or roster.get("schemaVersion") != "omega-workforce/v1"
                or not isinstance(roster.get("agents"), list)
            ):
                invalid("Malformed agent roster.", "agent_response_invalid")
            if any(
                a.get("name") == desired["spec"]["name"]
                for a in roster["agents"]
                if isinstance(a, dict)
            ):
                invalid(
                    "An agent with this name already exists. Export/import its explicit ID and lock it before applying.",
                    "agent_untracked",
                )
            return (
                {
                    "action": "create",
                    "agentId": None,
                    "expectedVersion": None,
                    "drift": [],
                    "changes": diff({}, desired["spec"]),
                    "target": target,
                },
                desired,
                None,
            )
        aid, version, current = await self._read(state["agentId"])
        drift = diff(state["definition"]["spec"], current["spec"])
        if version != state["version"]:
            drift.insert(
                0,
                {
                    "op": "replace",
                    "path": "/version",
                    "old": state["version"],
                    "value": version,
                },
            )
        changes = diff(current["spec"], desired["spec"])
        for field in ("modelId", "toolPolicy"):
            if field in current["spec"] and field not in desired["spec"]:
                invalid(
                    f"The backend cannot clear {field} by omission. Preserve it or set an explicit value.",
                    "agent_reset_unsupported",
                )
        return (
            {
                "action": "update" if changes else "noop",
                "agentId": aid,
                "expectedVersion": version,
                "drift": drift,
                "changes": changes,
                "target": target,
            },
            desired,
            current,
        )

    async def plan(self, document: Any, *, lockfile: str | Path) -> dict:
        """Return exact ordered changes and drift without writing files or remote state."""
        return (await self._plan(document, lockfile))[0]

    @staticmethod
    def _state(target: dict, aid: str, version: int, definition: dict) -> dict:
        return {
            "schemaVersion": LOCK_SCHEMA,
            "target": target,
            "status": "applied",
            "agentId": aid,
            "version": version,
            "definition": definition,
            "digest": digest(definition),
        }

    async def apply(
        self, document: Any, *, lockfile: str | Path, force: bool = False
    ) -> dict:
        """Save authored changes with compare-and-set and an atomic local outcome journal."""
        require_enabled()
        if type(force) is not bool:
            invalid("force must be a boolean.")
        with locked(lockfile):
            plan, desired, current = await self._plan(document, lockfile)
            if plan["drift"] and not force:
                invalid(
                    "Remote agent drift detected since the last apply/import. No changes made. Run plan, review the drift, then use --force to overwrite that observed version.",
                    "agent_drift",
                )
            if plan["action"] == "noop":
                if plan["drift"]:
                    write_json(
                        lockfile,
                        self._state(
                            plan["target"],
                            plan["agentId"],
                            plan["expectedVersion"],
                            desired,
                        ),
                        replace=True,
                    )
                return {**plan, "changed": False}
            pending = {
                "schemaVersion": LOCK_SCHEMA,
                "target": plan["target"],
                "status": "pending",
            }
            if plan["agentId"]:
                pending["agentId"] = plan["agentId"]
            write_json(lockfile, pending, replace=True)
            if plan["action"] == "create":
                response = await self._call("create", body=desired["spec"], retries=0)
            else:
                before, after = current["spec"], desired["spec"]
                patch = {
                    k: v for k, v in after.items() if k not in before or before[k] != v
                }
                if "environmentId" in patch or "environmentRevision" in patch:
                    patch.update(
                        environmentId=after["environmentId"],
                        environmentRevision=after["environmentRevision"],
                    )
                elif "environmentId" in before and "environmentId" not in after:
                    patch.update(environmentId=None, environmentRevision=None)
                response = await self._call(
                    "update",
                    path={"id": plan["agentId"]},
                    body={**patch, "expectedVersion": plan["expectedVersion"]},
                    retries=0,
                )
            aid, version, saved = project(response, plan["agentId"])
            if saved != desired or (
                plan["action"] == "update" and version != plan["expectedVersion"] + 1
            ):
                invalid(
                    "Server saved a different definition or version; pending journal retained. Inspect the Console before importing the server state.",
                    "agent_response_mismatch",
                )
            write_json(
                lockfile, self._state(plan["target"], aid, version, saved), replace=True
            )
            return {**plan, "agentId": aid, "version": version, "changed": True}

    async def export(self, agent_id: str) -> dict:
        """Export authored data only; no files, secrets, runs or credentials are included."""
        self._target()
        return (await self._read(agent_id))[2]

    async def import_definition(
        self, document: Any, *, lockfile: str | Path, agent_id: str | None = None
    ) -> dict:
        """Create from a portable definition or bind an explicit ID on exact equality."""
        if agent_id is None:
            return await self.apply(document, lockfile=lockfile)
        desired = self.validate(document)
        with locked(lockfile):
            target = self._target()
            if read_json(lockfile, missing=True) is not MISSING:
                invalid(
                    "Importing an existing ID requires a NEW lockfile.",
                    "agent_lock_exists",
                )
            aid, version, current = await self._read(agent_id)
            if current != desired:
                invalid(
                    "Import does not match the server definition. Export the current definition first; nothing was changed.",
                    "agent_import_mismatch",
                )
            write_json(lockfile, self._state(target, aid, version, current))
            return {
                "action": "import",
                "agentId": aid,
                "version": version,
                "changed": False,
                "changes": [],
            }
