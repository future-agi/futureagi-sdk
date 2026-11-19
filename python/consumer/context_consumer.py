"""Installed-package context/leaf API contract, without backend or model calls.

Run and type-check outside the checkout. Synthetic responses enter at the shared
HTTP transport; the real snapshot and installer code must compose from the wheel.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from fi.context import AsyncContextClient, ContextClient, VerifiedSnapshot
from fi.context.journal import Authorization
from fi.context.materialize import (
    apply_plan,
    from_verified_snapshot,
    plan_install,
    plan_remove,
    verify,
)
from fi.platform import AsyncClient, Client, ContextAuth
from fi.skills import AsyncSkillsClient, SkillsClient
from fi.skills.installer import (
    apply_skill_plan,
    plan_install_skill,
    verify_skills,
)
from fi.skills.installer import (
    from_verified_snapshot as skill_from_verified_snapshot,
)

ORIGIN = "https://context.example.invalid"
RESOURCE = "00000000-0000-4000-8000-000000000001"
VERSION = "00000000-0000-4000-8000-000000000002"
SCOPE = "00000000-0000-4000-8000-000000000003"
LEASE = "synthetic-installation-lease"
EXPIRY = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
DESCRIPTOR = json.dumps(
    {
        "schema": 1,
        "kind": "agent_context",
        "name": "team-policy",
        "description": "Synthetic installation contract",
        "entrypoint": "AGENTS.md",
        "owned_paths": ["AGENTS.md"],
        "links": [],
    },
    sort_keys=True,
    separators=(",", ":"),
)
FILES = {
    "AGENTS.md": "Synthetic standing instructions.\n",
    ".futureagi/context.json": DESCRIPTOR,
}
LEAF_FILES = {
    "SKILL.md": "---\nname: refund\ndescription: Use when checking a synthetic refund.\n---\nCheck the supplied rules.\n"
}


def digest(files: dict[str, str]) -> str:
    pairs = [
        [path, hashlib.sha256(text.encode()).hexdigest()]
        for path, text in sorted(files.items())
    ]
    return (
        "sha256:"
        + hashlib.sha256(json.dumps(pairs, separators=(",", ":")).encode()).hexdigest()
    )


def manifest(*, leaf: bool = False) -> dict[str, object]:
    files = LEAF_FILES if leaf else FILES
    result: dict[str, object] = {
        "resource_id": RESOURCE,
        "kind": "skill" if leaf else "agent_context",
        "entrypoint": "SKILL.md" if leaf else "AGENTS.md",
        "descriptor_path": None if leaf else ".futureagi/context.json",
        "name": "refund" if leaf else "team-policy",
        "version": 1,
        "version_id": VERSION,
        "digest": digest(files),
        "requested": {"label": "production"},
        "resolution_id": LEASE,
        "resolution_expires_at": EXPIRY,
        "file_count": len(files),
        "file_offset": 0,
        "next_file_offset": None,
        "files": [
            {
                "path": path,
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
                "size_bytes": len(text.encode()),
            }
            for path, text in sorted(files.items())
        ],
    }
    if not leaf:
        result.update(entrypoint="AGENTS.md", descriptor_path=".futureagi/context.json")
    return result


def chunk(path: str, *, leaf: bool = False) -> dict[str, object]:
    files = LEAF_FILES if leaf else FILES
    text = files[path]
    return {
        "resource_id": RESOURCE,
        "version_id": VERSION,
        "digest": digest(files),
        "path": path,
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
        "size_bytes": len(text.encode()),
        "total_chars": len(text),
        "offset": 0,
        "next_offset": None,
        "eof": True,
        "text": text,
    }


def handler(request: httpx.Request) -> httpx.Response:
    assert request.headers["Authorization"] == "Context synthetic-context"
    assert "X-Api-Key" not in request.headers and "X-Secret-Key" not in request.headers
    leaf = request.url.path.startswith("/model-hub/skills/consumption/")
    prefix = "/model-hub/skills/consumption/" if leaf else "/model-hub/skills/contexts/"
    if request.url.path == prefix + "resolve/":
        result = manifest(leaf=leaf)
    else:
        assert request.headers["X-Context-Resolution"] == LEASE
        assert request.url.path.startswith(f"{prefix}{RESOURCE}/versions/1/")
        if request.url.path.endswith("access-check/"):
            result = {
                "allowed": True,
                "version_id": VERSION,
                "digest": digest(LEAF_FILES if leaf else FILES),
                "checked_at": EXPIRY,
            }
        else:
            assert request.url.path.endswith("files/")
            result = chunk(request.url.params["path"], leaf=leaf)
    return httpx.Response(200, json={"status": True, "result": result})


def authorize(authorization: Authorization) -> None:
    # Synthetic grant check; real callers must use a live immutable authorizer.
    assert authorization.identity.version_id == VERSION
    assert authorization.lease.resolution_id == LEASE


def main() -> None:
    with Client(
        auth=ContextAuth("synthetic-context"),
        base_url=ORIGIN,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    ) as client:
        contexts = ContextClient(client)
        verified: VerifiedSnapshot = contexts.resolve("team-policy").read_all()
        contexts.check_access(verified.identity, verified.manifest.lease)
        skills = SkillsClient(client)
        leaf = skills.resolve("refund").read_all()
        skills.check_access(leaf.identity, leaf.manifest.lease)
    assert dict(verified.files) == FILES
    source = from_verified_snapshot(
        verified, origin=ORIGIN, organization_id=SCOPE, workspace_id=SCOPE
    )
    with tempfile.TemporaryDirectory() as temporary:
        project = Path(temporary)
        plan = plan_install(
            source, project=project, profile="codex", allow_preview=True
        )
        apply_plan(plan, authorize=authorize, quiescent=True)
        assert verify(project=project)["verified"]
        apply_plan(plan_remove(project=project), authorize=authorize, quiescent=True)
        assert not (project / "AGENTS.md").exists()

    assert dict(leaf.files) == LEAF_FILES
    skill = skill_from_verified_snapshot(
        leaf, origin=ORIGIN, organization_id=SCOPE, workspace_id=SCOPE
    )
    with tempfile.TemporaryDirectory() as temporary:
        project = Path(temporary)
        plan = plan_install_skill(
            skill, project=project, profile="codex", allow_preview=True
        )
        apply_skill_plan(plan, authorize=authorize, quiescent=True)
        assert verify_skills(project=project)["verified"]

    asyncio.run(async_contract())
    print(
        "installed context/skills consumer: sync, async, materialization and verification passed"
    )


async def async_contract() -> None:
    async with AsyncClient(
        auth=ContextAuth("synthetic-context"),
        base_url=ORIGIN,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    ) as client:
        snapshot = await AsyncContextClient(client).resolve("team-policy")
        assert dict((await snapshot.read_all()).files) == FILES
        skills = AsyncSkillsClient(client)
        leaf = await skills.resolve("refund")
        assert dict((await leaf.read_all()).files) == LEAF_FILES
        await skills.check_access(leaf.identity, leaf.manifest.lease)


if __name__ == "__main__":
    main()
