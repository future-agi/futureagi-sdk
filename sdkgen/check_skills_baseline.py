"""Check that a scoped Skills sync leaves every other public operation unchanged.

Run against a checkout containing the SDK commit recorded in swagger.json under x-contract-sources.other.
Checks public generator inputs and emitted operation records; never opens implementation files.

    python sdkgen/check_skills_baseline.py                                    # against x-contract-sources.other
    python sdkgen/check_skills_baseline.py --paired SDK_COMMIT --product-commit PRODUCT_COMMIT

Product-side pairing re-syncs only the Skills scope (sync_scoped_contract.py --scopes skills) over
the paired SDK commit. --paired compares everything that is not Skills, including every other
x-contract-sources record, byte for byte with that commit instead, and requires the Skills record
to name the product commit synced in the same run (its scope check ran in that sync).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

import sync_contract
import yaml
from generator.catalog import load
from sync_scoped_contract import SCOPES

ROOT = Path(__file__).resolve().parents[1]
SKILL_IDS = SCOPES["skills"]["id_prefixes"]
SKILL_PATH = SCOPES["skills"]["path_prefix"]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--paired", metavar="SDK_COMMIT", help="compare with this SDK commit, not x-contract-sources.other")
    parser.add_argument("--product-commit", help="with --paired: the product commit the Skills scope was synced from")
    args = parser.parse_args(argv)
    if bool(args.paired) != bool(args.product_commit):
        raise SystemExit("--paired and --product-commit go together")
    contracts = ROOT / "sdkgen/contracts"
    after = json.loads((contracts / "swagger.json").read_bytes())
    if "x-contract-sources" not in after and "x-source-sha256" in after:
        if args.paired:
            raise SystemExit("--paired needs a scoped slice")
        print("Release slice; no scoped baseline to compare")
        return
    metadata = after["x-contract-sources"]["other"]
    commit = args.paired or metadata["sdk_commit"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SystemExit("invalid SDK baseline commit")

    def baseline(path):
        return subprocess.check_output(["git", "-C", str(ROOT), "show", f"{commit}:{path}"])

    def equal(before, after, name):
        if before != after:
            raise SystemExit(f"changed non-Skills {name}")

    catalog = "sdkgen/catalog/operations.yaml"
    original = yaml.safe_load(baseline(catalog))["operations"]
    original = [op for op in original if not op["id"].startswith(SKILL_IDS)]
    selected = yaml.safe_load((ROOT / catalog).read_bytes())["operations"]
    surviving = [op for op in selected if not op["id"].startswith(SKILL_IDS)]
    equal(original, surviving, "catalog entries or ordering")

    raw = baseline("sdkgen/contracts/swagger.json")
    digest = hashlib.sha256(raw).hexdigest()
    before = json.loads(raw)
    if args.paired:
        if not re.fullmatch(r"[0-9a-f]{40}", args.product_commit):
            raise SystemExit("invalid product commit")
        # Only the Skills record may change; sql, epoch and other stay as the paired commit ships them.
        pinned = before.get("x-contract-sources") or {}
        recorded = after["x-contract-sources"]
        equal(set(pinned), set(recorded), "x-contract-sources scopes")
        for name in sorted(set(pinned) - {"skills"}):
            equal(pinned[name], recorded[name], f"x-contract-sources.{name}")
        if recorded.get("skills", {}).get("backend_commit") != args.product_commit:
            raise SystemExit("the Skills scope was not synced from this product commit in this run")
    # Compare the generated id -> tool mapping, not just a tool count. A new SDK
    # baseline can add tools, but a scoped sync cannot rename or reassign them.
    expected_names = {op["id"]: mcp.get("name", op["id"].replace(".", "_")) for op in original
                      if isinstance(mcp := op["surfaces"].get("mcp"), dict)}
    # load() applies catalog fixes in memory. Keep the raw schemas for the checks below.
    ops = load(copy.deepcopy(after), {"operations": selected})
    names = {op.id: op.surfaces["mcp"]["name"] for op in ops
             if "mcp" in op.surfaces and not op.id.startswith(SKILL_IDS)}
    equal(expected_names, names, "MCP mappings")
    print(f"{len(names)} non-Skills MCP mappings match {commit}")
    if not args.paired:  # the paired commit is not `other`; its records were compared above
        equal(digest, metadata["slice_sha256"], "baseline slice digest")
    paths, definitions = sync_contract.project(before, original)
    other_paths = {p: v for p, v in after["paths"].items() if not p.startswith(SKILL_PATH)}
    equal(paths, other_paths, "public paths/parameters/responses")
    equal(definitions, {k: after["definitions"].get(k) for k in definitions},
          "public schema definitions")
    equal(before.get("security", []), after.get("security", []), "default auth")
    for k, v in before.get("securityDefinitions", {}).items():
        equal(v, after["securityDefinitions"].get(k), f"auth scheme {k}")

    for language, path in (("Python", "python/fi/platform/_operations.py"),
                           ("TypeScript", "typescript/futureagi/src/platform/_operations.ts")):
        def records(data):
            rows = []
            for line in data.splitlines():
                m = re.match(rb"(?:export const )?OP_[A-Z0-9_]+(?:: Operation)? = .*?['\"]id['\"]: ['\"]([^'\"]+)", line)
                if m and not m.group(1).decode().startswith(SKILL_IDS):
                    rows.append(line)
            return rows
        previous = records(baseline(path))
        expected = sum(e["surfaces"].get("sdk") is not False for e in original)
        equal(expected, len(previous), f"{language} baseline record count")
        equal(previous, records((ROOT / path).read_bytes()), f"{language} generated operation records or ordering")
        print(f"{language}: {len(previous)} non-Skills records byte-identical to {commit}")
    print(f"{len(original)} catalog entries, {len(paths)} paths, {len(definitions)} definitions unchanged")


if __name__ == "__main__":
    main()
