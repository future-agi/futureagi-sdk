#!/usr/bin/env python3
"""One installed-consumer matrix entry point (Python 3.10+, Docker on a clean VM).

python3 -I scripts/journeys/run.py --manifest candidate/manifest-entry.json \
  --wheel candidate/build-1/futureagi.whl --tarball candidate/build-1/sdk.tgz \
  --policy policy.json --binding binding.json --out /absolute/new/output --cells N00,N01

The artifact manifest uses the candidate pipeline's {label, export_commit,
artifacts:[{kind:'wheel'|'npm',file,first:'sha256:...',second:'sha256:...'}]}.
No builds or publishing occur here. Historical input must be labelled historical.
A binding is {source:'stub'|'release-manifest', served:[], admitted:[]}. Stub results NEVER
qualify a release. Runtime traffic is loopback-only; real backends are not bound.
Use --emit-legs PATH for the merge input (it does not edit the shared journey file).
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artifacts import absence_checks, digest, inspect
from catalog import SURFACES, legs
from consumer import Consumers
from matrix import build, table
from ts_inventory import EXPECTED


def effective_policy(raw):
    for name in SURFACES:
        if name not in raw["states"] or any(raw["states"][name].get(lang) not in ("ON", "OFF") for lang in ("py", "ts")):
            raise ValueError("Explicit ON/OFF required per language for " + name)
    raw["surfaces"] = {}
    for name, (modules, accessors, aliases, calls) in SURFACES.items():
        ts_accessors = [".".join(part.split("_")[0] + "".join(p.title() for p in part.split("_")[1:]) for part in a.split(".")) for a in accessors]
        subpaths = [name.replace("_", "-")]
        if name == "gateway":
            subpaths = ["gateway", "gateway/testing", "gateway/express", "gateway/nextjs", "gateway/react"]
        root_exports = {"gateway": ["AgentCC", "AsyncAgentCC"], "runs": ["Run"],
                        "sandboxes": ["Sandbox"], "deployments": ["Deployment"], "evals": ["Evaluator"],
                        "webhooks": ["Webhooks", "AsyncWebhooks"], "agents": ["Agent"]}.get(name, [])
        raw["surfaces"][name] = {"py_modules": modules, "py_accessors": accessors, "ts_accessors": ts_accessors,
                                 "ts_subpaths": subpaths, "root_exports": root_exports,
                                 "docs_tokens": ["fi." + m for m in modules] + ["@future-agi/sdk/" + m for m in subpaths]
                                 + ["client." + m for m in accessors + ts_accessors]}
    if not raw.get("python_entries") or not raw.get("node_entries"):
        raise ValueError("Documented entry-point inventory is required")
    calls = {"py": [], "ts": []}
    for name, (_, _, _, paths) in SURFACES.items():
        if not paths:
            continue
        for lang, path in zip(("py", "ts"), paths):
            if raw["states"][name][lang] == "ON":
                calls[lang].append({"path": path, "args": [{}] if name == "evals" else []})
    # A certified namespace can override a probe's call shape without changing harness code.
    # Only member paths and JSON positional arguments are accepted, never executable snippets.
    for lang, rows in raw.get("config_call_overrides", {}).items():
        if lang not in calls:
            raise ValueError("Unknown language")
        by_path = {r["path"]: r for r in rows}
        calls[lang] = [by_path.get(r["path"], r) for r in calls[lang]]
    raw["config_calls"] = calls
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for flag in ("manifest", "wheel", "tarball", "policy", "binding", "out"):
        parser.add_argument("--" + flag, type=Path)
    parser.add_argument("--ts-inventory", type=Path, default=EXPECTED,
                        help='Reviewed emitted-file snapshot; candidate layout drift fails closed')
    parser.add_argument("--cells", default="N00,N01")
    parser.add_argument("--emit-legs", type=Path)
    args = parser.parse_args()
    if args.emit_legs:
        args.emit_legs.parent.mkdir(parents=True, exist_ok=True)
        args.emit_legs.write_text(json.dumps({"journey": "J24", "schema": 1, "binding_status": "stub-until-manifest-binding", "legs": legs()}, indent=2) + "\n")
        if args.manifest is None:
            return 0
    if any(getattr(args, name) is None for name in ("manifest", "wheel", "tarball", "policy", "binding", "out")):
        parser.error("All candidate, policy, binding and output paths are required")
    selected = args.cells.split(",")
    if any(cell not in {f"N{i:02}" for i in range(20)} for cell in selected):
        parser.error("Unknown matrix cell")
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    manifest = json.loads(args.manifest.read_text())
    policy = effective_policy(json.loads(args.policy.read_text()))
    binding = json.loads(args.binding.read_text())
    if binding.get("source") not in ("stub", "release-manifest") or any(not isinstance(binding.get(k), list) or any(not isinstance(x, str) for x in binding[k]) for k in ("served", "admitted")):
        raise ValueError("Explicit served/admitted binding required")
    inventory = inspect(args.wheel, args.tarball, manifest)
    policy_path = args.out / "effective-policy.json"
    policy_path.write_text(json.dumps(policy, indent=2) + "\n")
    expected = json.loads(args.ts_inventory.read_text())
    archive = {lang: absence_checks(inventory, policy, lang, expected) for lang in ("py", "ts")}
    (args.out / 'archive-checks.json').write_text(json.dumps(archive, indent=2) + '\n')
    probes = {}
    network = {"denied_count": 0, "install": {}, "runtime": {}}
    images = {}
    errors = ['TypeScript emitted inventory drift'] if any(
        c['name'] == 'install.typescript-inventory' and c['state'] != 'PASS' for c in archive['ts']) else []
    consumers = Consumers(Path(__file__).resolve().parent, args.out)
    try:
        with consumers:
            profiles = ("base", "evals", "tracing") if "N00" in selected else ("base",)
            work = [("py", version, extra) for version in ("3.10", "3.12") for extra in profiles]
            work += [("ts", version, "base") for version in ("20", "22")]
            for lang, version, extra in work:
                label = f"py-{version}-{extra}" if lang == "py" else f"ts-{version}"
                try:
                    if lang == "py":
                        _, result = consumers.python(version, extra, args.wheel.resolve(), policy_path, "N01" in selected)
                    else:
                        _, result = consumers.node(version, args.tarball.resolve(), policy_path, "N01" in selected)
                except Exception as exc:
                    result = {"checks": [{"name": "install.consumer", "state": "FAIL", "reason": type(exc).__name__}], "network": {"denied_count": 0}}
                probes[label] = result
                (args.out / "probes.json").write_text(json.dumps(probes, indent=2) + "\n")
            network["install"] = consumers.proxy.result()
            images = consumers.images
    except Exception as exc:
        errors.append(type(exc).__name__)
    finally:
        network["install"] = consumers.proxy.result()
        images = consumers.images
    for label, probe in probes.items():
        network["runtime"][label] = probe["network"]
    network["container"] = consumers.observations
    network["complete"] = bool(consumers.observations) and all(result["complete"] for result in consumers.observations.values())
    if not network["complete"]:
        errors.append("Container network accounting incomplete")
    network["denied_count"] = (network["install"].get("denied_count", 0)
                               + sum(r["denied_count"] for r in network["runtime"].values())
                               + sum(r["denied_count"] for r in network["container"].values()))
    rows = build(binding, policy, probes, archive, selected, network)
    report = {"schema": 1, "journey": "J24", "candidate": manifest, "binding": binding,
              "inputs": {"policy": digest(args.policy), "binding": digest(args.binding), "manifest": digest(args.manifest),
                         "typescript_inventory": digest(args.ts_inventory)},
              "proof_kind": "installed-artifact-loopback-fixture", "release_qualified": False,
              "runtime_images": images, "network": network, "cells": rows, "errors": errors}
    report["status"] = "FAIL" if errors or network["denied_count"] or any(r["state"] == "FAIL" for r in rows) else "NOT-EVALUATED" if any(r["state"] == "NOT-EVALUATED" for r in rows) else "PASS"
    (args.out / "matrix.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.out / "matrix.txt").write_text(table(rows))
    print(table(rows), end="")
    return int(report["status"] == "FAIL")


if __name__ == "__main__":
    sys.exit(main())
