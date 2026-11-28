"""Keep one GitHub issue open while SDK `dev` no longer pairs with product `dev`.

    python sdkgen/pair_drift_issue.py --pair pair.json --product future-agi --repo future-agi/futureagi-sdk

Run after sdkgen/pair_check.py in .github/workflows/pair-check-drift.yml. pair_check.py writes
pair.json even when it fails; this script reads it and:

- opens the issue (label `pair-check-drift`, a fixed title) when the scoped contract check fails
  on product drift and no such issue is open, naming the product commit range and the operations
  that differ;
- comments on the open issue when the drift it reports changes (the same drift on a newer product
  commit adds nothing);
- closes the open issue when the check passes again.

Only product drift counts: a failure to read the inputs, or a problem in the SDK's own live
coverage table, exits 1 without touching any issue (CI reports those). The token comes from
GITHUB_TOKEN and needs `issues: write`. Standard library only, apart from the SDK's own modules.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

import pair_check
import sync_scoped_contract
import yaml

LABEL = "pair-check-drift"
TITLE = "SDK dev no longer matches the product's scoped contract"
PRODUCT = pair_check.PRODUCT_REPOSITORY
MARKER = re.compile(r"<!-- pair-check-drift product=([0-9a-f]{40}) digest=([0-9a-f]{64}) -->")
# pair_check.py problems that are not product drift: the inputs could not be read, or the SDK's
# own coverage table or extra record is wrong. CI fails on those; no issue is opened for them.
NOT_DRIFT = ("could not read the pairing inputs", "--extra-json", "live coverage:")
MAX_LINES = 40

Request = Callable[[str, str, Any], Any]


def drift_problems(record: dict) -> tuple[list[str], list[str]]:
    """(drift, other): pair_check.py's problems split into product drift and everything else."""
    problems = record.get("problems") or []
    other = [p for p in problems if p.startswith(NOT_DRIFT)]
    return [p for p in problems if p not in other], other


def drifted(product: Path, sha: str) -> tuple[list[str], list[str]]:
    """(catalog operations that differ from the product, product tools of a scope the catalog has
    no entry for), read at `sha` the way pair_check.py reads it."""
    spec = json.loads(pair_check._git(product, "show", f"{sha}:{pair_check.SWAGGER}"))
    manifest = json.loads(pair_check._git(product, "show", f"{sha}:{pair_check.MCP}"))
    tools_yaml = yaml.safe_load(pair_check._git(product, "show", f"{sha}:{pair_check.TOOLS_YAML}"))
    committed = json.loads(pair_check.SLICE.read_text())
    entries = yaml.safe_load(pair_check.CATALOG.read_text())["operations"]
    described = {tool["name"]: tool.get("description") for tool in (tools_yaml or {}).get("tools", [])}
    tools = {tool["name"]: tool for tool in manifest.get("tools", []) if "name" in tool}
    ops: set[str] = set()
    known: dict[str, set[str]] = {scope: set() for scope in sync_scoped_contract.SCOPES}
    for entry in entries:
        scope = sync_scoped_contract.catalog_scope(entry)
        if scope is None:
            continue
        name = ((entry.get("surfaces") or {}).get("mcp") or {}).get("name")
        if name:
            known[scope].add(name)
        if pair_check.compare_projection(spec, committed, [entry], scope):
            ops.add(entry["id"])
        elif scope in sync_scoped_contract.DESCRIBED_SCOPES and described.get(name) != entry.get("description"):
            ops.add(entry["id"])
    new = sorted(
        name for scope in sync_scoped_contract.SCOPES
        for name in sync_scoped_contract.scope_tools(scope, {n: {"group": t.get("group")} for n, t in tools.items()})
        if name in tools and name not in known[scope]
    )
    return sorted(ops), new


def digest(drift: list[str], ops: list[str], new: list[str]) -> str:
    return hashlib.sha256(json.dumps([sorted(drift), ops, new]).encode()).hexdigest()


def synced_from(record: dict) -> dict[str, str]:
    """Per scope, the product commit the committed slice was synced from: where each range starts."""
    sources = record.get("contract_sources") or {}
    starts = {scope: (sources.get(scope) or {}).get("backend_commit") for scope in sync_scoped_contract.SCOPES}
    return {scope: commit for scope, commit in starts.items() if commit}


def _span(start: str | None, sha: str) -> str:
    if start and start != sha:
        return f"`{start[:12]}...{sha[:12]}`: https://github.com/{PRODUCT}/compare/{start}...{sha}"
    return f"`{sha[:12]}`"


def _ranges(record: dict) -> list[str]:
    sha = record["product"]["sha"]
    starts = synced_from(record)
    if len(set(starts.values())) <= 1:
        start = next(iter(starts.values()), None)
        return [f"**Product range** (from the commit the scoped slice was synced from): {_span(start, sha)}"]
    return ["**Product range**, per scope (from the commit each scope was synced from):"] + [
        f"- {scope}: {_span(start, sha)}" for scope, start in sorted(starts.items())
    ]


def _bullets(items: list[str]) -> str:
    shown = [f"- `{item}`" for item in items[:MAX_LINES]]
    if len(items) > MAX_LINES:
        shown.append(f"- … and {len(items) - MAX_LINES} more (see the run's pair.json)")
    return "\n".join(shown) or "- none"


def report_body(record: dict, drift: list[str], ops: list[str], new: list[str], run_url: str) -> str:
    sha = record["product"]["sha"]
    branch = record["product"].get("resolved_branch") or "explicit"
    return "\n".join([
        f"`sdkgen/pair_check.py` on `dev` fails against `{PRODUCT}@{sha}` ({branch}).",
        "",
        *_ranges(record),
        "",
        "**Operations that differ from the product:**",
        _bullets(ops),
        "",
        "**Product tools in a scoped group with no SDK catalog entry:**",
        _bullets(new),
        "",
        "**Check output:**",
        _bullets(drift),
        "",
        "Re-sync with `sdkgen/sync_scoped_contract.py` (see `sdkgen/README.md`), regenerate, and update the "
        "live suite. This issue closes itself when the check passes on `dev` again.",
        "",
        f"Run: {run_url}",
        f"<!-- pair-check-drift product={sha} digest={digest(drift, ops, new)} -->",
    ])


class GitHub:
    """The few issue endpoints this script uses, over urllib."""

    def __init__(self, token: str, api: str = "https://api.github.com"):
        self.token, self.api = token, api.rstrip("/")

    def __call__(self, method: str, path: str, body: Any = None) -> Any:
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(
            f"{self.api}{path}", data=data, method=method,
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise RuntimeError(f"GitHub {method} {path} answered {exc.code}") from None
        return json.loads(raw) if raw else {}


def _open_issue(request: Request, repo: str) -> dict | None:
    issues = request("GET", f"/repos/{repo}/issues?state=open&labels={LABEL}&per_page=100") or []
    mine = [i for i in issues if "pull_request" not in i and i.get("title") == TITLE]
    return min(mine, key=lambda i: i["number"]) if mine else None


def _last_digest(request: Request, repo: str, issue: dict) -> str | None:
    texts = [issue.get("body") or ""]
    page = 1
    while True:
        comments = request("GET", f"/repos/{repo}/issues/{issue['number']}/comments?per_page=100&page={page}") or []
        texts += [c.get("body") or "" for c in comments]
        if len(comments) < 100:
            break
        page += 1
    found = [m.group(2) for text in texts for m in MARKER.finditer(text)]
    return found[-1] if found else None


def _ensure_label(request: Request, repo: str) -> None:
    if request("GET", f"/repos/{repo}/labels/{LABEL}") is None:
        request("POST", f"/repos/{repo}/labels", {
            "name": LABEL, "color": "d93f0b",
            "description": "SDK dev's scoped contract no longer matches product dev",
        })


def reconcile(request: Request, repo: str, record: dict, ops: list[str], new: list[str], run_url: str) -> str:
    """Make the issue state match the record. Returns what it did."""
    drift, _ = drift_problems(record)
    issue = _open_issue(request, repo)
    sha = record["product"]["sha"]
    if not drift:
        if issue is None:
            return "clean"
        request("POST", f"/repos/{repo}/issues/{issue['number']}/comments", {
            "body": f"`sdkgen/pair_check.py` passes on `dev` against `{PRODUCT}@{sha}` again. Closing.\n\nRun: {run_url}",
        })
        request("PATCH", f"/repos/{repo}/issues/{issue['number']}", {"state": "closed", "state_reason": "completed"})
        return f"closed #{issue['number']}"
    body = report_body(record, drift, ops, new, run_url)
    if issue is None:
        _ensure_label(request, repo)
        created = request("POST", f"/repos/{repo}/issues", {"title": TITLE, "body": body, "labels": [LABEL]})
        return f"opened #{created['number']}"
    if _last_digest(request, repo, issue) == digest(drift, ops, new):
        return f"unchanged #{issue['number']}"
    request("POST", f"/repos/{repo}/issues/{issue['number']}/comments", {"body": "The drift changed.\n\n" + body})
    return f"commented #{issue['number']}"


def main(argv: list[str] | None = None, request: Request | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pair", type=Path, required=True, help="pair.json from sdkgen/pair_check.py")
    parser.add_argument("--product", type=Path, required=True, help="the product checkout pair_check.py read")
    parser.add_argument("--repo", required=True, help="owner/name of the SDK repository")
    parser.add_argument("--run-url", default="", help="the workflow run, linked from the issue")
    args = parser.parse_args(argv)
    record = json.loads(args.pair.read_text())
    drift, other = drift_problems(record)
    for problem in other:
        print(f"pair drift: not product drift, no issue: {problem}", file=sys.stderr)
    if other and not drift:
        return 1
    ops, new = drifted(args.product, record["product"]["sha"]) if drift else ([], [])
    if request is None:
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            print("pair drift: GITHUB_TOKEN is not set", file=sys.stderr)
            return 1
        request = GitHub(token)
    print(f"pair drift: {reconcile(request, args.repo, record, ops, new, args.run_url)}")
    return 1 if other else 0


if __name__ == "__main__":
    sys.exit(main())
