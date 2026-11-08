"""Reconcile catalog routing with the supplied Swagger, by stable operation identity.

source.json is a generated projection of the certified Swagger, independent of the
runtime catalog metadata. Missing or ambiguous identities refuse the candidate;
a previous URL is never silently used as a substitute for a removed operation.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

from contract_drift import compare, inventory

METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}
SOURCE = "openapi/catalog/source.json"
CATALOG = "openapi/catalog/operations.json"


def index(doc, wanted=None):
    result = {}
    for path, item in doc.get("paths", {}).items():
        for method, op in item.items():
            if method not in METHODS:
                continue
            oid = op.get("operationId")
            if not oid or (wanted is not None and oid not in wanted):
                continue
            if oid in result:
                raise ValueError(f"duplicate operation identity: {oid}")
            result[oid] = (method.upper(), path, op, item)
    return result


def aliases(catalog):
    result = {}
    for row in catalog["operations"]:
        result.setdefault(row["operation_id"], []).append(row["public"])
    return result


def project(swagger, catalog):
    """Copy admitted operations and their reference closure, not unrelated schemas."""
    available = index(swagger, aliases(catalog))
    result = {k: copy.deepcopy(swagger[k]) for k in ("swagger", "openapi", "info", "basePath", "host", "schemes", "servers", "consumes", "produces") if k in swagger}
    result["paths"] = {}
    for oid in aliases(catalog):
        if oid not in available:
            continue  # retained as removed drift; reconcile refuses application
        method, path, op, item = available[oid]
        target = result["paths"].setdefault(path, {})
        target[method.lower()] = copy.deepcopy(op)
        for key in ("parameters", "servers"):
            if key in item:
                target[key] = copy.deepcopy(item[key])
    seen = set()

    def references(value):
        if isinstance(value, list):
            for child in value:
                references(child)
        if not isinstance(value, dict):
            return
        for key, child in value.items():
            if key != "$ref":
                references(child)
                continue
            if not child.startswith("#/"):
                raise ValueError(f"non-local catalog reference: {child}")
            if child in seen:
                continue
            seen.add(child)
            parts = [p.replace("~1", "/").replace("~0", "~") for p in child[2:].split("/")]
            source, target = swagger, result
            for part in parts:
                source = source[part]
            for part in parts[:-1]:
                target = target.setdefault(part, {})
            target[parts[-1]] = copy.deepcopy(source)
            references(source)
    references(copy.deepcopy(result["paths"]))
    return result


def resolve(doc, value):
    seen = set()
    while "$ref" in value:
        ref = value["$ref"]
        if not ref.startswith("#/") or ref in seen:
            raise ValueError(f"unsupported catalog parameter reference: {ref}")
        seen.add(ref)
        value = doc
        for part in ref[2:].split("/"):
            value = value[part.replace("~1", "/").replace("~0", "~")]
    return value


def reconcile(catalog, source):
    available = index(source)
    result = copy.deepcopy(catalog)
    for row in result["operations"]:
        oid = row["operation_id"]
        if oid not in available:
            raise ValueError(f"missing catalog operation: {oid} ({row['public']})")
        method, path, op, item = available[oid]
        params = [resolve(source, p) for p in item.get("parameters", []) + op.get("parameters", [])]
        # Unwrap/pagination are reviewed public adaptations; source response-schema
        # drift is still recorded even when those adaptations have not changed.
        row.update(method=method, path=path, path_params=re.findall(r"\{([^}]+)\}", path),
                   query=sorted({p["name"] for p in params if p["in"] == "query"}))
    return result


def drift(before, after, catalog):
    names = aliases(catalog)
    return compare(inventory(before, names), inventory(after, names))


def stage(root, swagger, source_digest=None):
    catalog_path = root / CATALOG
    catalog = json.loads(catalog_path.read_text())
    source = project(swagger, catalog)
    old_path = root / SOURCE
    before = json.loads(old_path.read_text()) if old_path.exists() else {"paths": {}}
    changes = drift(before, source, catalog)
    updated = reconcile(catalog, source)
    if source_digest:
        source["x-source-sha256"] = "sha256:" + source_digest
    old_path.write_text(json.dumps(source, indent=2) + "\n")
    catalog_path.write_text(json.dumps(updated, indent=2) + "\n")
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--swagger", type=Path, required=True)
    args = parser.parse_args()
    data = args.swagger.read_bytes()
    changes = stage(args.root, json.loads(data), hashlib.sha256(data).hexdigest())
    print(json.dumps(changes, indent=2))


if __name__ == "__main__":
    main()
