"""Exact local-plan export and public campaign transport.

This module does not enable campaigns, execute Git, merge PRs or infer delivery.
Local diffs are uploaded only by an explicit ``record_plan`` call. Registry
credentials and resolution leases never enter the campaign review document.
"""

from __future__ import annotations

import json
from uuid import UUID

from fi.platform import Client, RequestOptions

from .journal import InstallPlan, decode, parse_plan
from .lock import CONTEXT_LOCK, InstallationError, canonical_json, parse_lock, sha256
from .materialize import _validate_context_plan, inspect_plan, plan_install

ROOT = "/model-hub/skills/contexts/campaigns/"


def target_plan(
    plan: InstallPlan,
    *,
    repository_id: str,
    base_commit: str,
    binding_revision: int,
    campaign_revision: int,
) -> dict[str, object]:
    """Export a reviewed install/update/restore into the frozen campaign contract.

    The base commit is an explicit caller observation; this function does not
    attest that the checkout belongs to that GitHub repository. The eventual Git
    executor must independently check repository identity, base and all preimages
    before writing. Local paths/leases are omitted and no file is changed.
    """
    import re

    if (
        not isinstance(repository_id, str)
        or not re.fullmatch(r"[1-9][0-9]{0,19}", repository_id)
        or not isinstance(base_commit, str)
        or not re.fullmatch(r"[0-9a-f]{40}", base_commit)
        or any(
            type(value) is not int or value < 1
            for value in (binding_revision, campaign_revision)
        )
    ):
        raise InstallationError(
            "invalid_campaign",
            "An exact repository ID, base and revisions are required.",
            2,
        )
    plan = parse_plan(plan.to_bytes())
    if plan.lock_path != CONTEXT_LOCK or plan.operation == "remove":
        raise InstallationError(
            "invalid_campaign", "Campaigns require an exact desired context release.", 2
        )
    source = _validate_context_plan(plan)
    desired = parse_lock(plan.changes[-1].require_content())
    # Export has the same ownership/preimage checks as apply, including unowned
    # files arriving in a native skill tree and retained local segments. A
    # self-consistent edited lock/digest is not an authority to erase local work.
    current = plan_install(
        source,
        project=plan.project,
        profile=desired.materialization.profile,
        adopt_local=True,
        allow_preview=True,
        operation=plan.operation,
    )
    if current.plan_digest != plan.plan_digest:
        raise InstallationError(
            "stale_plan", "Current ownership/preimages differ from the reviewed plan.", 6
        )
    previous_raw = decode(plan.previous_lock)
    previous = parse_lock(previous_raw) if previous_raw is not None else None
    ownership = {}
    for lock in (previous, desired):
        if lock:
            ownership.update(
                {row.destination: row.ownership for row in lock.materialization.files}
            )
    # inspect_plan independently checks all current local preimages; no stale
    # diff is exported after the operator edits local instructions.
    inspected = inspect_plan(plan, include_diff=True)
    previews = {row["path"]: row["diff"] for row in inspected["diffs"]}
    changes = []
    for change in plan.changes:
        if change.before_sha256 == change.after_sha256:
            continue
        preview = previews[change.path]
        if len(preview) > 8192:
            preview = (
                preview[:8120]
                + "\n[Preview truncated; review full local diff before authorization.]"
            )
        changes.append(
            {
                "path": change.path,
                "action": "remove"
                if change.after is None
                else "add"
                if change.before_sha256 is None
                else "replace",
                "before_sha256": change.before_sha256,
                "after_sha256": change.after_sha256,
                "ownership": ownership.get(change.path, "managed"),
                "diff_preview": preview,
            }
        )
    result = {
        "campaign_revision": campaign_revision,
        "binding_revision": binding_revision,
        "repository_id": repository_id,
        "base_commit": base_commit,
        "previous_lock_digest": None
        if previous_raw is None
        else "sha256:" + sha256(previous_raw),
        "desired_version_id": desired.version_id,
        "materialization_digest": desired.materialization.materialization_digest,
        "changes": changes,
        "local_review_required": any(row["ownership"] == "adopted" for row in changes),
        "blockers": [],
    }
    result["plan_digest"] = "sha256:" + sha256(
        canonical_json(
            {key: value for key, value in result.items() if key != "campaign_revision"}
        )
    )
    if (
        len(changes) > 500
        or len(json.dumps(result, ensure_ascii=False).encode("utf-8")) > 65536
    ):
        raise InstallationError(
            "payload_too_large",
            "The exact campaign review exceeds its bounded contract.",
            6,
        )
    return result


class CampaignClient:
    """Frozen human-bound API on the caller's configured platform transport.

    Construct the platform Client with the existing user-bound credentials and
    organization/workspace scope. The server's feature switch and current admin
    checks remain authoritative; no request enables them or assumes approval.
    """

    def __init__(self, client: Client):
        self.client = client

    @staticmethod
    def _path(campaign_id: str, binding_id: str | None = None) -> str:
        path = ROOT + str(UUID(campaign_id)) + "/"
        if binding_id is not None:
            path += "targets/" + str(UUID(binding_id)) + "/"
        return path

    def create(
        self,
        *,
        name: str,
        targets: list[dict[str, object]],
        idempotency_key: str,
        parent_campaign_id: str | None = None,
    ) -> object:
        return self.client.request(
            "POST",
            ROOT,
            body={
                "name": name,
                "targets": targets,
                "parent_campaign_id": parent_campaign_id,
            },
            options=RequestOptions(idempotency_key=str(UUID(idempotency_key))),
        )

    def get(self, campaign_id: str) -> object:
        return self.client.request("GET", self._path(campaign_id))

    def targets(self, campaign_id: str, *, page: int = 1) -> object:
        return self.client.request(
            "GET", self._path(campaign_id) + "targets/", query={"page": page}
        )

    def record_plan(
        self, campaign_id: str, binding_id: str, plan: dict[str, object]
    ) -> object:
        return self.client.request(
            "PUT", self._path(campaign_id, binding_id) + "plan/", body=plan
        )

    def authorize(
        self,
        campaign_id: str,
        *,
        revision: int,
        expected_manifest_digest: str,
        decisions: list[dict[str, object]],
        acknowledge_repository_writes: bool,
    ) -> object:
        return self.client.request(
            "POST",
            self._path(campaign_id) + "authorize/",
            body={
                "revision": revision,
                "expected_manifest_digest": expected_manifest_digest,
                "decisions": decisions,
                "acknowledge_repository_writes": acknowledge_repository_writes,
            },
        )

    def claim(
        self,
        campaign_id: str,
        binding_id: str,
        *,
        plan_digest: str,
        idempotency_key: str,
    ) -> object:
        return self.client.request(
            "POST",
            self._path(campaign_id, binding_id) + "claim/",
            body={"plan_digest": plan_digest},
            options=RequestOptions(idempotency_key=str(UUID(idempotency_key))),
        )

    def record_attempt(
        self, campaign_id: str, binding_id: str, receipt: dict[str, object]
    ) -> object:
        return self.client.request(
            "POST", self._path(campaign_id, binding_id) + "attempts/", body=receipt
        )

    def observations(self, campaign_id: str, binding_id: str) -> object:
        return self.client.request(
            "GET", self._path(campaign_id, binding_id) + "observations/"
        )

    def change_status(
        self, campaign_id: str, *, action: str, revision: int, reason: str
    ) -> object:
        if action not in {"pause", "resume", "cancel"}:
            raise ValueError("Use pause, resume or cancel")
        return self.client.request(
            "POST",
            self._path(campaign_id) + action + "/",
            body={"revision": revision, "reason": reason},
        )

    def preview_reverse(self, campaign_id: str, *, revision: int) -> object:
        return self.client.request(
            "POST",
            self._path(campaign_id) + "rollback/preview/",
            body={"revision": revision},
        )
