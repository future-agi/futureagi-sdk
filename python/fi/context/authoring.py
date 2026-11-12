"""Create several contexts that share the published skill library, then accept their exact locks together.

Use a user-bound platform Client. Every context keeps its own draft, resolved lock and fingerprint-bound
dependency update; the plan digest binds what the operator saw. Creating the drafts publishes nothing, and
publication and promotion stay separate reviewed steps (see fi.context.release).

CLI: python -m fi.context.authoring plan-create NAME [NAME ...] --description TEXT
         (--root TEXT | --root-file PATH) [--label production] [--pin NAME:SKILL=VERSION ...] --out plan.json
         Creates one draft per name holding the shared standing instructions, previews linking every published
         skill by label (each --pin is the one exception for that context), and prints each context's resolved
         versions, checks, exceptions and one plan digest.
     python -m fi.context.authoring apply-create --plan plan.json --reviewed-plan DIGEST --accept-resolved-versions
         Applies each context's own previewed update, bound to its own fingerprint.
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
from uuid import NAMESPACE_URL, UUID, uuid5

from fi.platform import Client, RequestOptions
from fi.platform._errors import APIConnectionError, APIError

MAX_LINKS = 20
_LABEL = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode()).hexdigest()


def published_skills(client: Client) -> list[dict]:
    """The complete inventory of published leaf skills; an inventory that moves while read is refused."""
    skills: dict[str, dict] = {}
    count = None
    for page in range(1, 1000):
        value = client.request("GET", "/model-hub/skills/", query={"page": page, "page_size": 100, "sort": "name", "order": "asc"})
        if value["page"] != page or (count is not None and count != value["count"]):
            raise ValueError("The skill inventory changed while it was read; plan again")
        count = value["count"]
        for skill in value["results"]:
            if skill["id"] in skills:
                raise ValueError("The skill inventory changed while it was read; plan again")
            skills[skill["id"]] = skill
        if page >= value["total_pages"]:
            break
        if not value["results"]:
            raise ValueError("The complete skill inventory is unavailable")
    if len(skills) != count:
        raise ValueError("The complete skill inventory is unavailable")
    return [s for s in skills.values() if s.get("latest_version") is not None and s.get("kind", "skill") == "skill"]


def plan_create(client: Client, names: list[str], *, description: str, root: str, label: str = "production",
                pins: dict[str, dict[str, int]] | None = None) -> dict:
    """Create one draft per name and preview its links. Nothing is applied, published or promoted."""
    pins = pins or {}
    if not names or len(set(names)) != len(names):
        raise ValueError("Name each context once")
    if not description.strip() or not root.strip():
        raise ValueError("A purpose and standing instructions are required")
    if not _LABEL.fullmatch(label):
        raise ValueError("Use a valid selector label")
    if set(pins) - set(names):
        raise ValueError("A pin names a context that is not being created")
    skills = published_skills(client)
    by_name = {skill["name"]: skill for skill in skills}
    if len(skills) > MAX_LINKS:
        raise ValueError(f"A context holds at most {MAX_LINKS} linked skills; link fewer")
    contexts = []
    for name in names:
        chosen = pins.get(name, {})
        if set(chosen) - set(by_name):
            raise ValueError("A pin names an unpublished skill")
        links = [{"skill_id": by_name[skill]["id"], "selector": {"version": version}} for skill, version in sorted(chosen.items())]
        links += [{"skill_id": skill["id"], "selector": {"label": label}} for skill in skills if skill["name"] not in chosen]
        created = client.request("POST", "/model-hub/skills/contexts/", body={
            "name": name, "description": description, "tags": [], "files": [{"path": "AGENTS.md", "content": root}]},
            options=RequestOptions(idempotency_key=str(uuid5(NAMESPACE_URL, f"create:{_digest([name, description, root])}")), max_retries=0))
        context_id, revision = created["context_id"], created["revision"]
        body = {"revision": revision, "links": links, "refresh_skill_ids": []}
        preview = client.request("POST", f"/model-hub/skills/contexts/{UUID(context_id)}/dependencies/preview/", body=body,
                                 options=RequestOptions(max_retries=0))
        summary = preview["checks"]["summary"]
        contexts.append({
            "context_id": context_id, "name": name, "revision": revision, "links": links,
            "fingerprint": preview["fingerprint"], "candidate_digest": preview["candidate_digest"],
            "resolved": [{"mount": change["mount"], "version": (change.get("after") or {}).get("version"),
                          "selector": (change.get("after") or {}).get("requested")} for change in preview["changes"]],
            "exceptions": [{"skill": skill, "pin": version} for skill, version in sorted(chosen.items())],
            "errors": summary["errors"], "warnings": summary["warnings"],
        })
    return {"schema": 1, "kind": "create", "description": description, "contexts": contexts, "plan_digest": _digest(contexts)}


def apply_create(client: Client, plan: dict, *, reviewed_plan: str, accept_resolved_versions: bool) -> dict:
    if plan.get("schema") != 1 or plan.get("kind") != "create" or _digest(plan["contexts"]) != plan.get("plan_digest"):
        raise ValueError("The plan file was changed after it was previewed")
    if reviewed_plan != plan["plan_digest"]:
        raise ValueError("Review and name the exact plan digest")
    if accept_resolved_versions is not True:
        raise ValueError("Accept the exact resolved versions and selector policies")
    if any(row["errors"] for row in plan["contexts"]):
        raise ValueError("Blocking checks prevent applying; nothing was applied")
    applied = []
    for row in plan["contexts"]:
        base = f"/model-hub/skills/contexts/{UUID(row['context_id'])}/"
        result = client.request("POST", base + "dependencies/apply/", body={
            "revision": row["revision"], "links": row["links"], "refresh_skill_ids": [], "expected_fingerprint": row["fingerprint"]},
            options=RequestOptions(idempotency_key=str(uuid5(NAMESPACE_URL, f"apply:{plan['plan_digest']}:{row['context_id']}")), max_retries=0))
        draft = result if "files" in result else client.request("GET", base + "draft/")
        if draft.get("digest") != row["candidate_digest"]:
            raise ValueError("The applied draft differs from the reviewed candidate")
        applied.append({"context_id": row["context_id"], "revision": draft["revision"], "digest": draft["digest"]})
    return {"plan_digest": plan["plan_digest"], "applied": applied}


def _parse_pins(values: list[str]) -> dict[str, dict[str, int]]:
    pins: dict[str, dict[str, int]] = {}
    for value in values:
        match = re.fullmatch(r"([^:=]+):([^:=]+)=([1-9][0-9]*)", value)
        if not match:
            raise ValueError("Use --pin CONTEXT:SKILL=VERSION")
        pins.setdefault(match[1], {})[match[2]] = int(match[3])
    return pins


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m fi.context.authoring")
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan-create")
    plan.add_argument("names", nargs="+")
    plan.add_argument("--description", required=True)
    source = plan.add_mutually_exclusive_group(required=True)
    source.add_argument("--root")
    source.add_argument("--root-file", type=Path)
    plan.add_argument("--label", default="production")
    plan.add_argument("--pin", action="append", default=[])
    plan.add_argument("--out", required=True, type=Path)
    apply = commands.add_parser("apply-create")
    apply.add_argument("--plan", required=True, type=Path)
    apply.add_argument("--reviewed-plan", required=True)
    apply.add_argument("--accept-resolved-versions", action="store_true")
    args = parser.parse_args(argv)
    try:
        organization = str(UUID(os.environ["FI_ORGANIZATION_ID"]))
        workspace = str(UUID(os.environ["FI_WORKSPACE_ID"]))
        with Client(workspace_id=workspace, default_headers={"X-Organization-Id": organization}) as client:
            if args.command == "plan-create":
                root = args.root if args.root is not None else args.root_file.read_text()
                document = plan_create(client, args.names, description=args.description, root=root, label=args.label,
                                       pins=_parse_pins(args.pin))
                args.out.write_text(json.dumps(document))
                args.out.chmod(0o600)
                result = {"plan_digest": document["plan_digest"], "plan_file": str(args.out),
                          "contexts": [{k: v for k, v in row.items() if k != "links"} for row in document["contexts"]]}
            else:
                raw = args.plan.read_bytes()[: 2 * 1024 * 1024 + 1]
                if len(raw) > 2 * 1024 * 1024:
                    raise ValueError("Plan exceeds the 2 MiB CLI limit")
                result = apply_create(client, json.loads(raw), reviewed_plan=args.reviewed_plan,
                                      accept_resolved_versions=args.accept_resolved_versions)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (APIConnectionError, APIError) as error:
        code = getattr(error, "code", None)
        status = getattr(error, "status_code", None)
        suffix = f" (HTTP {status}" + (f", {code}" if isinstance(code, str) and re.fullmatch(r"[a-z0-9_]{1,64}", code) else "") + ")" if isinstance(status, int) else ""
        print(f"Context authoring request failed{suffix}; inspect the original operation before retrying.", file=sys.stderr)
        return 1
    except (ValueError, KeyError, OSError) as error:
        print(f"Invalid context authoring input or scoped SDK configuration: {error}"
              if isinstance(error, ValueError) else "Invalid context authoring input or scoped SDK configuration.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
