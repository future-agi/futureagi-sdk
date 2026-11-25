#!/usr/bin/env python3
"""Pick the future-agi product revision a CI or E2E run pairs the SDK with.

    python .github/scripts/resolve_product_ref.py      (in a workflow step; writes GITHUB_OUTPUT)

Modes, decided by the triggering event:

  pinned   a push to main, a pull request into main, or any dispatch without a
           product-ref: the run tests the release in
           sdkgen/contracts/BACKEND_VERSION (or the dispatched backend-version or
           backend-ref), exactly as before.
  latest   the nightly schedule: the newest published release (:latest).
  paired   pull requests into dev or other branches, pushes to branches other
           than main, and dispatches that name a product-ref: the run pairs with
           one immutable product commit. Candidates, in order: the PR head
           branch, the PR base branch (the pushed branch on a push), dev, main. A
           dispatched product-ref is the only candidate.

Only a candidate branch that does not exist is passed over. One that exists must
resolve to a full 40-hex commit holding every file the pairing needs
(REQUIRED_PATHS), or the run fails: it never pairs with a later candidate
instead. Transport errors fail the same way. Outputs: mode, sha and branch (sha and branch are empty unless
the mode is paired). Standard library only.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, List, Optional, Tuple

REPOSITORY = "https://github.com/future-agi/future-agi.git"
# What the paired jobs read from the product commit: the contract and MCP tool
# list (ci.yml), and the stack definition plus every build input of the
# Standalone image the E2E job builds from source (e2e.yml).
REQUIRED_PATHS = (
    "api_contracts/openapi/swagger.json",
    "futureagi/mcp_server/catalog/tools.generated.json",
    "futureagi/mcp_server/catalog/tools.yaml",
    "docker-compose.yml",
    "e2e/stack/docker-compose.standalone-e2e.yml",
    "e2e/stack/standalone-e2e.env",
    "e2e/stack/backend/Dockerfile",
    "e2e/stack/backend/bootstrap_sql.py",
    "e2e/stack/frontend/Dockerfile",
    "futureagi/Dockerfile.oss",
    "frontend/Dockerfile",
    "fi-collector/Dockerfile",
    "agentcc-gateway/Dockerfile",
    "deploy/standalone/Dockerfile",
    "bin/e2e",
    "bin/lib/build-local.sh",
    "scripts/reclaim-runner-disk.sh",
)
FULL_SHA = re.compile(r"[0-9a-f]{40}")
# probe(ref, explicit) -> (sha, missing paths), or None when the ref does not exist.
Probe = Callable[[str, bool], Optional[Tuple[str, List[str]]]]


class ResolutionError(RuntimeError):
    """No product revision can safely be paired with this run."""


class InvalidRefError(ResolutionError):
    """A candidate is not a supported branch, tag or commit spelling."""


def named_refs(ref: str, explicit: bool) -> Tuple[str, ...]:
    """The fully qualified refs a name may denote. Automatic candidates are branches only."""
    if ref.startswith("refs/heads/") or (explicit and ref.startswith("refs/tags/")):
        return (ref,)
    if ref.startswith("refs/"):
        raise InvalidRefError("product refs must name a branch, tag or full commit SHA")
    return (f"refs/heads/{ref}", f"refs/tags/{ref}") if explicit else (f"refs/heads/{ref}",)


def validate_ref(ref: str, explicit: bool = True) -> None:
    if not ref or len(ref) > 1024 or ref.startswith("-") or any(ord(c) < 32 or c == "\x7f" for c in ref):
        raise InvalidRefError("invalid product ref spelling")
    if explicit and FULL_SHA.fullmatch(ref):
        return
    try:
        result = subprocess.run(
            ["git", "check-ref-format", named_refs(ref, explicit)[0]],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ResolutionError("product ref validation timed out") from exc
    if result.returncode:
        raise InvalidRefError("invalid product ref spelling")


def select_mode(env: dict) -> Tuple[str, str, str, str]:
    """(mode, explicit product ref, head candidate, base candidate) for this event."""
    event = env.get("GITHUB_EVENT_NAME", "")
    explicit = env.get("PRODUCT_REF_INPUT", "").strip()
    release = env.get("BACKEND_VERSION_INPUT", "").strip() or env.get("BACKEND_REF_INPUT", "").strip()
    if explicit and event != "workflow_dispatch":
        raise ResolutionError("product-ref is a dispatch input")
    if event == "workflow_dispatch":
        if explicit and release:
            raise ResolutionError("choose product-ref (paired) or backend-version/backend-ref (pinned), not both")
        if not explicit:
            return "pinned", "", "", ""  # A dispatch keeps the release pin unless it names a product-ref.
        return "paired", explicit, "", ""
    if event == "schedule":
        return "latest", "", "", ""
    if event == "push":
        ref = env.get("GITHUB_REF", "")
        if not ref.startswith("refs/heads/"):
            raise ResolutionError("only branch pushes are paired")
        if ref == "refs/heads/main":
            return "pinned", "", "", ""
        return "paired", "", "", ref[len("refs/heads/"):]
    if event in ("pull_request", "pull_request_target"):
        base = env.get("GITHUB_BASE_REF", "")
        if not base:
            raise ResolutionError("pull request without a base branch")
        if base == "main":
            return "pinned", "", "", ""
        return "paired", "", env.get("GITHUB_HEAD_REF", ""), base
    if event == "merge_group":
        # A queue ref is not a feature branch: use only the queue's target.
        ref = env.get("QUEUE_BASE_REF", "")
        if not ref.startswith("refs/heads/") or ref == "refs/heads/":
            raise InvalidRefError("merge group requires a fully qualified base branch")
        branch = ref[len("refs/heads/"):]
        validate_ref(branch, explicit=False)
        if branch == "main":
            return "pinned", "", "", ""
        return "paired", "", "", branch
    raise ResolutionError(f"unsupported event for product pairing: {event or '(none)'}")


def choose_ref(explicit: str, head: str, base: str, probe: Probe) -> Tuple[str, str]:
    """(sha, candidate). Only a branch that does not exist is passed over; any candidate that
    exists must hold REQUIRED_PATHS, or resolution fails."""
    candidates = [explicit] if explicit else [ref for ref in (head, base, "dev", "main") if ref]
    for candidate in dict.fromkeys(candidates):
        try:
            validate_ref(candidate, explicit=bool(explicit))
        except InvalidRefError:
            if not explicit:
                continue  # An unsupported automatic branch name must not mask dev or main.
            raise
        result = probe(candidate, bool(explicit))  # Transport errors propagate: never a fallback.
        if result is None:
            if explicit:
                raise ResolutionError("requested product ref does not exist")
            continue
        sha, missing = result
        if not FULL_SHA.fullmatch(sha):
            raise ResolutionError("product ref did not resolve to a full commit SHA")
        if explicit and FULL_SHA.fullmatch(explicit) and sha != explicit:
            raise ResolutionError("requested product commit identity mismatch")
        if missing:
            which = "requested product ref" if explicit else f"product branch {candidate}"
            raise ResolutionError(f"{which} lacks required files: " + ", ".join(missing))
        return sha, candidate
    raise ResolutionError("no product branch among the candidates exists")


class GitProbe:
    """ls-remote, then a shallow tree-only fetch of the one commit and an ls-tree of REQUIRED_PATHS."""

    def __init__(self, directory: Path):
        self.directory = directory
        self._git("init", "--quiet")
        self._git("remote", "add", "origin", REPOSITORY)

    def _git(self, *args: str, allow_missing: bool = False) -> subprocess.CompletedProcess:
        try:
            result = subprocess.run(
                ["git", "-C", str(self.directory), *args],
                capture_output=True, text=True, timeout=120, check=False,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            )
        except subprocess.TimeoutExpired as exc:
            raise ResolutionError("product repository operation timed out") from exc
        if result.returncode and not allow_missing:
            # Do not echo transport diagnostics: credential helpers can include secrets.
            raise ResolutionError("product repository operation failed")
        return result

    def __call__(self, ref: str, explicit: bool) -> Optional[Tuple[str, List[str]]]:
        if explicit and FULL_SHA.fullmatch(ref):
            fetch_ref = ref
        else:
            if explicit and re.fullmatch(r"[0-9a-fA-F]{7,40}", ref) and ref != ref.lower():
                raise ResolutionError("use a lowercase full 40-character product commit SHA")
            names = named_refs(ref, explicit)
            advertised = self._git("ls-remote", "--exit-code", "origin", *names, allow_missing=True)
            if advertised.returncode not in (0, 2):
                raise ResolutionError("could not query product refs")
            available = {}
            if advertised.returncode == 0:
                for line in advertised.stdout.splitlines():
                    fields = line.split()
                    if len(fields) == 2:
                        available[fields[1]] = fields[0]
            fetch_ref = next((name for name in names if name in available), None)
            if fetch_ref is None:
                if explicit and re.fullmatch(r"[0-9a-f]{7,39}", ref):
                    raise ResolutionError("use a full 40-character product commit SHA; no branch or tag matches this abbreviation")
                return None
        self._git("fetch", "--quiet", "--depth=1", "--filter=blob:none", "--no-tags", "origin", fetch_ref)
        sha = self._git("rev-parse", "FETCH_HEAD^{commit}").stdout.strip()
        listed = self._git("ls-tree", "-z", sha, "--", *REQUIRED_PATHS).stdout
        found = set()
        for record in listed.split("\0"):
            meta, _, path = record.partition("\t")
            fields = meta.split()
            # Regular or executable files only: a symlink (120000) or tree does not count.
            if len(fields) == 3 and fields[0] in ("100644", "100755") and fields[1] == "blob":
                found.add(path)
        return sha, [path for path in REQUIRED_PATHS if path not in found]


def resolve(env: dict, probe_factory: Optional[Callable[[Path], Probe]] = None) -> Tuple[str, str, str]:
    """(mode, sha, branch) for this run. Pinned and latest runs never touch the network."""
    mode, explicit, head, base = select_mode(env)
    if mode != "paired":
        return mode, "", ""
    with tempfile.TemporaryDirectory(prefix="product-ref-") as directory:
        probe = (probe_factory or GitProbe)(Path(directory))
        sha, selected = choose_ref(explicit, head, base, probe)
    return mode, sha, selected


def main() -> int:
    try:
        mode, sha, branch = resolve(dict(os.environ))
        output = os.environ.get("GITHUB_OUTPUT")
        if not output:
            raise ResolutionError("GITHUB_OUTPUT is required")
        with Path(output).open("a") as handle:
            handle.write(f"mode={mode}\nsha={sha}\nbranch={branch}\n")
        if mode == "paired":
            print(f"product pairing: future-agi {branch} resolved to {sha}")
        else:
            print(f"product pairing: {mode} (the backend release decides the product revision)")
        return 0
    except ResolutionError as exc:
        print(f"::error::{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
