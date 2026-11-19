#!/usr/bin/env python3
"""Repin the three contracts and regenerate in an isolated staging directory.

Required inputs are local files: the union customer OpenAPI and .sha256, the
certified composed FA Swagger, and the admin schema plus its digest. No backend
or registry is queried for a contract. Generators may install their pinned tools.
Run on a build worker. --check proves byte-for-byte no-op without changing the
checkout. --apply copies only a completely generated candidate into the checkout;
all changed namespaces remain NOT-EVALUATED until their suites pass.

The optional FA certificate is a JSON object with sha256 and certified:true.
--fa-management-generator names the management module's repository-relative script
and receives FA Swagger, admin schema, and staged repository as its arguments.
It must emit openapi/fa-mgmt/generated/spec.json and
openapi/fa-mgmt/wrapper-map.json (the management generator's operations list,
normalized into public invocations by management_contracts.normalize).
Generated management runtimes live under python/fi/generated/platform/fa_management and
typescript/futureagi/src/generated/fa-management. The absence of that module is
reported, never represented as management coverage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from contract_drift import compare, inventory
from catalog_contracts import CATALOG, SOURCE as CATALOG_SOURCE, drift as catalog_drift, project, reconcile
from contract_cases import management_cases

ROOT = Path(__file__).resolve().parents[2]
SOURCES = "openapi/contract-sources.json"
OUTPUTS = ("openapi/platform", "openapi/sdk/generated", "openapi/catalog", "openapi/fa-mgmt",
           "python/fi/generated/platform", "python/fi/generated/openapi_client",
           "typescript/futureagi/src/generated/platform", "typescript/futureagi/src/generated/openapi",
           "typescript/futureagi/src/generated/catalog", "typescript/futureagi/src/generated/fa-management",
           "tests/fixtures/contracts")
MANAGEMENT_SPEC = "openapi/fa-mgmt/generated/spec.json"
MANAGEMENT_MAP = "openapi/fa-mgmt/wrapper-map.json"


def merge_drift(report, changes):
    for namespace, change in changes.items():
        group = report["namespaces"].setdefault(namespace, {
            "verdict": "NOT-EVALUATED", "added": [], "removed": [], "changed": []})
        for kind in ("added", "removed", "changed"):
            group[kind] = sorted(set(group[kind]) | set(change[kind]))


def management_inventory(root):
    if not (root / MANAGEMENT_SPEC).exists():
        return {}
    doc, mapping = read(root / MANAGEMENT_SPEC), read(root / MANAGEMENT_MAP)
    management_cases(doc, mapping)  # validate coverage before accepting any inventory
    from management_contracts import normalize
    mapping = normalize(doc, mapping)
    aliases = {}
    for name, entry in mapping["operations"].items():
        if not entry.get("unwrapped"):
            aliases.setdefault(entry["operation_id"], []).append(name)
    return inventory(doc, aliases) if aliases else {}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected(value):
    text = value.read_text() if isinstance(value, Path) else value
    match = re.fullmatch(r"(?:sha256:)?([a-fA-F0-9]{64})(?:\s+[^\n]+)?\s*", text.strip())
    if not match:
        raise ValueError("expected a SHA256 digest or checksum-file line")
    return match[1].lower()


def checked(path, checksum):
    actual = digest(path)
    if actual != expected(checksum):
        raise ValueError(f"contract digest mismatch: {path.name}")
    return actual


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def files(root):
    paths = [root / path for path in ("openapi/contract-offerings.json", "openapi/sdk/lifecycle-source.openapi.json")
             if (root / path).exists()]
    paths += [p for prefix in OUTPUTS for p in (root / prefix).rglob("*")
             if p.is_file() and not {"__pycache__", "__tests__", ".ruff_cache"}.intersection(p.parts)]
    return {str(p.relative_to(root)): digest(p) for p in paths}


def run(root, *command):
    subprocess.run(command, cwd=root, check=True)


def repin(args):
    root = args.root.resolve()
    ee_hash = checked(args.ee_openapi, args.ee_sha256)
    gateway_hash = checked(args.gateway_schema, args.gateway_sha256)
    fa_hash = digest(args.fa_swagger)
    if args.fa_certificate:
        cert = read(args.fa_certificate)
        if cert.get("certified") is not True or expected(cert.get("sha256", "")) != fa_hash:
            raise ValueError("FA certification does not bind these Swagger bytes")
    ee, fa = read(args.ee_openapi), read(args.fa_swagger)
    if not ee.get("openapi") or not ee.get("paths"):
        raise ValueError("EE input must be a customer OpenAPI document")
    if not (fa.get("swagger") or fa.get("openapi")) or not fa.get("paths"):
        raise ValueError("FA input must be a composed Swagger/OpenAPI document")
    gateway = read(args.gateway_schema)
    if not isinstance(gateway, dict) or not (gateway.get("$schema") or gateway.get("properties")):
        raise ValueError("gateway input must be an admin JSON schema")
    pins = {"version": 1, "ee": {"sha256": ee_hash}, "fa": {"sha256": fa_hash}, "gateway": {"sha256": gateway_hash}}
    report = {"inputs": pins, "certification": "verified" if args.fa_certificate else "not supplied; input certification remains caller-owned",
              "namespaces": {}, "generated_drift": [], "management": "NOT-OFFERED: generator not integrated", "status": "BLOCKED"}
    previous_pins = read(root / SOURCES) if (root / SOURCES).exists() else {}
    if previous_pins.get("gateway", {}).get("sha256") != gateway_hash:
        report["namespaces"]["gateway"] = {"verdict": "NOT-EVALUATED", "added": [], "removed": [],
            "changed": ["admin_schema"], "reason": "admin schema digest changed or has no recorded baseline"}
    old_files = files(root)
    old_ee = read(root / "openapi/platform/generated/futureagi-platform.openapi.json")
    old_fa = read(root / "openapi/sdk/generated/futureagi-sdk.openapi.json")
    aliases = {}
    for ns, methods in read(root / "openapi/sdk/wrapper-map.json").items():
        for method, oid in methods.items():
            aliases.setdefault(oid, []).append(ns + "." + method)
    try:
        with tempfile.TemporaryDirectory(prefix="contract-repin-") as tmp:
            stage = Path(tmp)
            for folder in ("scripts", "openapi", "python/fi/generated", "typescript/futureagi/src/generated"):
                shutil.copytree(root / folder, stage / folder, ignore=shutil.ignore_patterns("__pycache__", "node_modules"))
            # Swagger 2 omits write-only metadata; the core generator reads the
            # independently pinned queue serializer snapshot to restore it.
            snapshot = Path("tests/fixtures/server-contracts/annotation-queue-create.json")
            if (root / snapshot).exists():
                (stage / snapshot).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root / snapshot, stage / snapshot)
            from lifecycle_contracts import PROJECTION, stage as lifecycle_stage
            if getattr(args, "fa_lifecycle_swagger", None):
                lifecycle_stage(stage, args.fa_lifecycle_swagger, getattr(args, "fa_extension_swagger", ()))
            if (stage / PROJECTION).exists():
                projection = read(stage / PROJECTION)
                pins["lifecycle"] = {"sha256": projection["x-source-sha256"],
                                     "extensions": projection.get("x-extension-sources", {}),
                                     "projection": "sha256:" + digest(stage / PROJECTION)}
            catalog = read(root / CATALOG)
            prior_catalog_source = read(root / CATALOG_SOURCE) if (root / CATALOG_SOURCE).exists() else {"paths": {}}
            catalog_source = project(fa, catalog)
            # Report removal/change even if reconciliation or a later core generator refuses.
            merge_drift(report, catalog_drift(prior_catalog_source, catalog_source, catalog))
            catalog_source["x-source-sha256"] = "sha256:" + fa_hash
            write(stage / CATALOG_SOURCE, catalog_source)
            write(stage / CATALOG, reconcile(catalog, catalog_source))
            old_management = management_inventory(root)
            scoped = stage / "openapi/platform/generated/futureagi-platform.openapi.json"
            run(stage, "node", "scripts/platform/scope-filter.mjs", str(args.ee_openapi), str(scoped),
                str(stage / "openapi/platform/generated/futureagi-platform.operations.txt"))
            merge_drift(report, compare(inventory(old_ee), inventory(read(scoped))))
            source = read(stage / "openapi/platform/source.json")
            source["sha256"] = ee_hash
            source["scoped"]["sha256"] = digest(scoped)
            if args.ee_revision:
                source["commit"] = args.ee_revision
            write(stage / "openapi/platform/source.json", source)
            mapping = read(stage / "openapi/platform/wrapper-map.json")
            mapping["contract_sha256"] = ee_hash
            write(stage / "openapi/platform/wrapper-map.json", mapping)
            # Capture FA drift even if the wrapper-completeness gate refuses generation.
            try:
                run(stage, "bash", "scripts/generate-oss-sdk.sh", str(args.fa_swagger))
            finally:
                candidate = stage / "openapi/sdk/generated/futureagi-sdk.openapi.json"
                merge_drift(report, compare(inventory(old_fa, aliases), inventory(read(candidate), aliases)))
            run(stage, "bash", "scripts/generate-platform-sdk.sh")
            run(stage, "python3", "scripts/generate-catalog-namespaces.py")
            if args.fa_management_generator:
                relative = Path(args.fa_management_generator)
                if relative.is_absolute() or ".." in relative.parts or not (stage / relative).is_file():
                    raise ValueError("management generator must be an existing repository-relative script")
                run(stage, "bash", str(relative), str(args.fa_swagger), str(args.gateway_schema), str(stage))
                if not (stage / MANAGEMENT_SPEC).exists() or not (stage / MANAGEMENT_MAP).exists():
                    raise ValueError("management generator must emit the scoped spec and public wrapper-map.json")
                merge_drift(report, compare(old_management, management_inventory(stage)))
                report["management"] = "regenerated with Python sync/async and TypeScript public contract cases; tests owed"
            elif (root / "openapi/fa-mgmt").exists():
                raise ValueError("FA management exists but no generator was supplied")
            else:
                from contract_offerings import declaration
                unavailable = declaration(read(stage / "openapi/contract-offerings.json")["modules"]["management"])
                report["management"] = unavailable
            if args.fa_management_generator:
                offerings_path = stage / "openapi/contract-offerings.json"
                if offerings_path.exists():
                    offerings = read(offerings_path)
                    offerings.get("modules", {}).pop("management", None)
                    write(offerings_path, offerings)
            run(stage, "python3", "scripts/platform/wrapper_map.py", "--contract", str(args.ee_openapi),
                "--ledger", str(root / "openapi/admission-ledger.json"))
            run(stage, "python3", "scripts/platform/contract_cases.py", "--ledger", str(root / "openapi/admission-ledger.json"))
            write(stage / SOURCES, pins)
            new_files = files(stage)
            drift = sorted(p for p in set(old_files) | set(new_files) if old_files.get(p) != new_files.get(p))
            report["generated_drift"] = drift
            pin_drift = not (root / SOURCES).exists() or read(root / SOURCES) != pins
            report["pin_drift"] = pin_drift
            if args.check:
                report["status"] = "NO-OP" if not drift and not pin_drift else "DRIFT"
            else:
                # Nothing in the checkout was touched before every generator and gate succeeded.
                for name in drift:
                    target = root / name
                    if name in new_files:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(stage / name, target)
                    else:
                        target.unlink()
                write(root / SOURCES, pins)
                report["status"] = "APPLIED; namespace tests owed"
    except Exception as exc:
        report["error"] = str(exc)
        raise
    finally:
        write(args.report, report)
        for namespace, drift in sorted(report["namespaces"].items()):
            print(f"{namespace}: NOT-EVALUATED ({len(drift['added'])} added, {len(drift['removed'])} removed, {len(drift['changed'])} changed)")
    return 0 if report["status"] != "DRIFT" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--ee-openapi", type=Path, required=True)
    parser.add_argument("--ee-sha256", type=Path, required=True)
    parser.add_argument("--ee-revision", required=True)
    parser.add_argument("--fa-swagger", type=Path, required=True)
    parser.add_argument("--fa-certificate", type=Path)
    parser.add_argument("--fa-lifecycle-swagger", type=Path, help="upstream Swagger at the recorded lifecycle-source revision")
    parser.add_argument("--fa-extension-swagger", type=Path, action="append", default=[],
                        help="recorded lifecycle amendment named <pin-name>.json; repeat for each source")
    parser.add_argument("--gateway-schema", type=Path, required=True)
    parser.add_argument("--gateway-sha256", required=True)
    parser.add_argument("--fa-management-generator")
    parser.add_argument("--report", type=Path, default=Path("out/repin.json"))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    for name in ("ee_openapi", "ee_sha256", "fa_swagger", "gateway_schema", "report"):
        setattr(args, name, getattr(args, name).resolve())
    if args.fa_certificate:
        args.fa_certificate = args.fa_certificate.resolve()
    if args.fa_lifecycle_swagger:
        args.fa_lifecycle_swagger = args.fa_lifecycle_swagger.resolve()
    args.fa_extension_swagger = [path.resolve() for path in args.fa_extension_swagger]
    try:
        return repin(args)
    except (ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"repin refused: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
