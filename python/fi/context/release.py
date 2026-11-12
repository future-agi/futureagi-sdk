"""Publish and request release for a whole set of context drafts, one reviewed decision per step.

Use a user-bound platform Client. Every context keeps its own saved draft, comparison,
review fingerprint, publication and operation key; the plan digest binds exactly what the
operator saw. Publication never moves a label and a release request never moves one either:
a different authorized person still reviews and releases each exact parent.

CLI: python -m fi.context.release plan-publish CONTEXT_ID [CONTEXT_ID ...] --out plan.json
         Reads each saved draft's complete comparison and prints every changed file, the
         accepted dependency lock, the reviewed publication head, the static-check summary
         and one plan digest.
     python -m fi.context.release publish-set --plan plan.json --reviewed-plan DIGEST
         --reviewed-changes [--acknowledge-warnings] [--note TEXT]
         Records the reviewed head, then publishes, for each context separately.
     python -m fi.context.release plan-release CONTEXT_ID [CONTEXT_ID ...] --version N
         [--label production] --out plan.json
         Previews each exact label move and prints its current -> proposed pointer.
     python -m fi.context.release request-set --plan plan.json --reviewed-plan DIGEST
         --reviewer USER_ID --confirm-request-only
         Sends one independent review request per context; nothing is released.
Credentials use FI_API_KEY/FI_SECRET_KEY plus FI_ORGANIZATION_ID/FI_WORKSPACE_ID.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from uuid import UUID, uuid5, NAMESPACE_URL

from fi.platform import Client, RequestOptions
from fi.platform._errors import APIConnectionError, APIError

_LABEL = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode()).hexdigest()


def _base(context_id: str) -> str:
    return f"/model-hub/skills/contexts/{UUID(context_id)}/"


def _check_plan(plan: dict, kind: str, key: str) -> None:
    if plan.get("schema") != 1 or plan.get("kind") != kind or _digest(plan[key]) != plan.get("plan_digest"):
        raise ValueError("The plan file was changed after it was previewed")


def read_comparison(client: Client, context_id: str, revision: int) -> dict:
    """Every page of the draft's comparison with its content origin and publication head."""
    snapshot = None
    origin: list[dict] = []
    head: list[dict] = []
    for page in range(1, 101):
        value = client.request("POST", _base(context_id) + "release/review/",
                               body={"operation": "publish", "revision": revision, "page": page},
                               options=RequestOptions(max_retries=0))
        if snapshot and snapshot["review_fingerprint"] != value["review_fingerprint"]:
            raise ValueError("The comparison changed while it was read; plan again")
        snapshot = value
        origin += value["changes"]["files"]
        head += value["head_changes"]["files"]
        if page >= max(value["changes"]["total_pages"], value["head_changes"]["total_pages"]):
            break
    if (snapshot is None or snapshot["candidate"]["revision"] != revision
            or not snapshot.get("head_review") or snapshot["head_review"]["draft_revision"] != revision
            or snapshot["head_review"]["candidate_digest"] != snapshot["candidate"]["digest"]):
        raise ValueError("The saved draft no longer matches this review")
    return {"snapshot": snapshot, "origin": origin, "head": head}


def _changed(files: list[dict]) -> list[dict]:
    return [{"path": f["path"], "status": f["status"], "from_sha256": f.get("from_sha256"),
             "to_sha256": f.get("to_sha256")} for f in files if f["status"] != "unchanged"]


def plan_publish(client: Client, context_ids: list[str]) -> dict:
    """Read every saved draft and its comparison. Nothing is acknowledged or published."""
    if not context_ids or len(set(context_ids)) != len(context_ids):
        raise ValueError("Name each context once")
    contexts = []
    for context_id in context_ids:
        draft = client.request("GET", _base(context_id) + "draft/")
        found = read_comparison(client, context_id, draft["revision"])
        review = found["snapshot"]["head_review"]
        summary = found["snapshot"]["checks"]["summary"]
        contexts.append({
            "context_id": context_id, "revision": draft["revision"],
            "candidate_digest": review["candidate_digest"], "base_version": review["base_version"],
            "expected_head_version": review["expected_head_version"], "head_digest": review.get("head_digest"),
            "review_fingerprint": review["review_fingerprint"],
            "accepted_lock": [{"mount": link["mount"], "version": link["version"], "version_id": link["version_id"],
                               "digest": link["digest"], "requested": link.get("requested")}
                              for link in (draft.get("resolved_lock") or {}).get("links", [])],
            "changed_from_origin": _changed(found["origin"]), "changed_from_head": _changed(found["head"]),
            "errors": summary["errors"], "warnings": summary["warnings"],
        })
    return {"schema": 1, "kind": "publish", "contexts": contexts, "plan_digest": _digest(contexts)}


def publish_set(client: Client, plan: dict, *, reviewed_plan: str, reviewed_changes: bool,
                acknowledge_warnings: bool, note: str = "") -> dict:
    _check_plan(plan, "publish", "contexts")
    if reviewed_plan != plan["plan_digest"]:
        raise ValueError("Review and name the exact plan digest")
    if reviewed_changes is not True:
        raise ValueError("State that the complete comparison and publication head were reviewed")
    for row in plan["contexts"]:
        if row["errors"]:
            raise ValueError("Blocking checks prevent publication; nothing was published")
        if row["warnings"] and acknowledge_warnings is not True:
            raise ValueError("Acknowledge the static warnings for these exact candidates")
    published = []
    for row in plan["contexts"]:
        base = _base(row["context_id"])
        # Recheck the live review: a candidate or head that moved since review is never published.
        live = read_comparison(client, row["context_id"], row["revision"])["snapshot"]["head_review"]
        if (live["review_fingerprint"], live["candidate_digest"], live["expected_head_version"]) != (
                row["review_fingerprint"], row["candidate_digest"], row["expected_head_version"]):
            raise ValueError("The draft or publication head changed after review; plan again")
        acknowledgment = {"revision": row["revision"], "expected_digest": row["candidate_digest"],
                          "expected_head_version": row["expected_head_version"], "review_fingerprint": row["review_fingerprint"]}
        saved = client.request("POST", base + "draft/acknowledge-head/", body=acknowledgment,
                               options=RequestOptions(max_retries=0))
        if saved.get("digest") != row["candidate_digest"] or saved.get("expected_head_version") != row["expected_head_version"]:
            raise ValueError("The acknowledged head differs from the reviewed one")
        result = client.request("POST", base + "draft/publish/", body={
            **acknowledgment, "revision": saved["revision"], "review_fingerprint": saved["review_fingerprint"],
            "base_version": saved["base_version"], "note": note, "acknowledge_warnings": bool(row["warnings"])},
            options=RequestOptions(idempotency_key=str(uuid5(NAMESPACE_URL, f"{plan['plan_digest']}:{row['context_id']}")),
                                   max_retries=0))
        version = result["version"]
        published.append({"context_id": row["context_id"], "version": version.get("version", version.get("number")),
                          "digest": version.get("digest")})
    return {"plan_digest": plan["plan_digest"], "published": published}


def plan_release(client: Client, context_ids: list[str], *, version: int, label: str = "production") -> dict:
    """Preview each exact label move. Nothing is requested or moved."""
    if not context_ids or len(set(context_ids)) != len(context_ids):
        raise ValueError("Name each context once")
    if not _LABEL.fullmatch(label):
        raise ValueError("Use a valid release label")
    contexts = []
    for context_id in context_ids:
        manifest = client.request("GET", _base(context_id) + f"versions/{int(version)}/inspection/")["manifest"]
        preview = client.request("POST", "/model-hub/skills/release-requests/preview/", body={
            "resource_id": str(UUID(context_id)), "kind": "agent_context",
            "candidate_version_id": manifest["version_id"], "label": label, "evidence": []},
            options=RequestOptions(max_retries=0))
        packet = preview["packet"]
        if packet["candidate_version_id"] != manifest["version_id"] or packet["candidate_digest"] != manifest["digest"]:
            raise ValueError("The preview names a different release than the one requested")
        contexts.append({"context_id": context_id, "version": int(version), "label": label,
                         "candidate_digest": packet["candidate_digest"],
                         "from_version": packet["transition"]["expected_version"], "to_version": packet["transition"]["version"],
                         "release_revision": packet["transition"]["expected_release_revision"],
                         "security_revision": packet["transition"]["expected_security_revision"],
                         "fingerprint": preview["fingerprint"], "packet": packet})
    return {"schema": 1, "kind": "release", "contexts": contexts, "plan_digest": _digest(contexts)}


def request_set(client: Client, plan: dict, *, reviewed_plan: str, reviewer: str, confirm_request_only: bool,
                author_id: str | None = None) -> dict:
    _check_plan(plan, "release", "contexts")
    if reviewed_plan != plan["plan_digest"]:
        raise ValueError("Review and name the exact plan digest")
    if confirm_request_only is not True:
        raise ValueError("Confirm that this only requests independent review and moves no label")
    reviewer = str(UUID(reviewer))
    if author_id and reviewer.lower() == str(UUID(author_id)).lower():
        raise ValueError("Choose an independent reviewer, not yourself")
    requests = []
    for row in plan["contexts"]:
        sent = client.request("POST", "/model-hub/skills/release-requests/", body={
            "packet": row["packet"], "expected_fingerprint": row["fingerprint"], "recipient_ids": [reviewer]},
            options=RequestOptions(idempotency_key=str(uuid5(NAMESPACE_URL, f"{plan['plan_digest']}:{row['context_id']}:{reviewer}")),
                                   max_retries=0))
        requests.append({"context_id": row["context_id"], "request_id": sent["id"], "status": sent.get("status")})
    return {"plan_digest": plan["plan_digest"], "requests": requests}


def _summary(plan: dict) -> dict:
    rows = []
    for row in plan["contexts"]:
        rows.append({k: v for k, v in row.items() if k not in {"packet"}})
    return {"plan_digest": plan["plan_digest"], "contexts": rows}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m fi.context.release")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("plan-publish", "plan-release"):
        sub = commands.add_parser(name)
        sub.add_argument("context_ids", nargs="+")
        sub.add_argument("--out", required=True, type=Path)
        if name == "plan-release":
            sub.add_argument("--version", required=True, type=int)
            sub.add_argument("--label", default="production")
    publish = commands.add_parser("publish-set")
    publish.add_argument("--plan", required=True, type=Path)
    publish.add_argument("--reviewed-plan", required=True)
    publish.add_argument("--reviewed-changes", action="store_true")
    publish.add_argument("--acknowledge-warnings", action="store_true")
    publish.add_argument("--note", default="")
    request = commands.add_parser("request-set")
    request.add_argument("--plan", required=True, type=Path)
    request.add_argument("--reviewed-plan", required=True)
    request.add_argument("--reviewer", required=True)
    request.add_argument("--confirm-request-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        organization = str(UUID(os.environ["FI_ORGANIZATION_ID"]))
        workspace = str(UUID(os.environ["FI_WORKSPACE_ID"]))
        with Client(workspace_id=workspace, default_headers={"X-Organization-Id": organization}) as client:
            if args.command in {"plan-publish", "plan-release"}:
                for context_id in args.context_ids:
                    UUID(context_id)
                plan = (plan_publish(client, args.context_ids) if args.command == "plan-publish"
                        else plan_release(client, args.context_ids, version=args.version, label=args.label))
                args.out.write_text(json.dumps(plan))
                args.out.chmod(0o600)
                result = {**_summary(plan), "plan_file": str(args.out)}
            else:
                raw = args.plan.read_bytes()[: 2 * 1024 * 1024 + 1]
                if len(raw) > 2 * 1024 * 1024:
                    raise ValueError("Plan exceeds the 2 MiB CLI limit")
                document = json.loads(raw)
                if args.command == "publish-set":
                    result = publish_set(client, document, reviewed_plan=args.reviewed_plan,
                                         reviewed_changes=args.reviewed_changes,
                                         acknowledge_warnings=args.acknowledge_warnings, note=args.note)
                else:
                    result = request_set(client, document, reviewed_plan=args.reviewed_plan, reviewer=args.reviewer,
                                         confirm_request_only=args.confirm_request_only)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (APIConnectionError, APIError) as error:
        code = getattr(error, "code", None)
        status = getattr(error, "status_code", None)
        suffix = f" (HTTP {status}" + (f", {code}" if isinstance(code, str) and re.fullmatch(r"[a-z0-9_]{1,64}", code) else "") + ")" if isinstance(status, int) else ""
        print(f"Context release request failed{suffix}; inspect the original operation before retrying.", file=sys.stderr)
        return 1
    except (ValueError, KeyError, OSError) as error:
        print(f"Invalid context release input or scoped SDK configuration: {error}"
              if isinstance(error, ValueError) else "Invalid context release input or scoped SDK configuration.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
