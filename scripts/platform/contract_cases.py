"""Generate transport-contract cases from specs, not from the generated runtime tables.

Run with --check in CI. Both language runners consume the same deterministic JSON.
A missing wrapped operation is an error, never silently dropped from the test set.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from contract_offerings import declaration, public_inventory

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path("tests/fixtures/contracts/operations.json")
METHODS = ("get", "post", "put", "patch", "delete", "head", "options")
STATUSES = {400: "BadRequestError", 401: "AuthenticationError", 402: "PaymentRequiredError",
            403: "PermissionDeniedError", 404: "NotFoundError", 409: "ConflictError",
            410: "FutureAGIAPIError", 413: "PayloadTooLargeError", 418: "FutureAGIAPIError",
            422: "UnprocessableEntityError", 429: "RateLimitError", 500: "ServerError",
            502: "ServerError", 503: "ServerError", 504: "ServerError"}
# Canonical management envelope codes; unknown/new codes retain status-based typing.
FA_CODES = {"invalid": 400, "not_authenticated": 401, "payment_required": 402,
            "permission_denied": 403, "not_found": 404, "conflict": 409, "gone": 410,
            "request_too_large": 413, "export_too_large": 413, "rate_limited": 429,
            "server_error": 500, "service_unavailable": 503, "timeout": 504,
            "error": 400, "required": 400, "items_too_large": 413,
            "user_filter_requires_cursor": 400, "score_project_mismatch": 400,
            "dataset_limit_check_failed": 503, "filter_value_inventory_too_broad": 400}


def read(root, path):
    return json.loads((root / path).read_text())


def snake(value):
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value).replace("-", "_").lower()


def camel(value):
    parts = re.split(r"[_-]", value)
    return parts[0] + "".join(x[:1].upper() + x[1:] for x in parts[1:])


def operations(doc):
    return [(method.upper(), path, op, item) for path, item in doc["paths"].items()
            for method, op in item.items() if method in METHODS]


def resolve(doc, node):
    seen = set()
    while isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if ref in seen or not ref.startswith("#/"):
            raise ValueError(f"unsupported reference {ref}")
        seen.add(ref)
        node = doc
        for part in ref[2:].split("/"):
            node = node[part.replace("~1", "/").replace("~0", "~")]
    return node


def case(doc, method, path, op, name, adapter):
    keyed = op.get("x-omega-idempotent") is True
    durable = op.get("x-omega-idempotency", {}).get("durable")
    retry = ("keyed-not-durable" if durable is False else "keyed") if keyed else (
        "http-idempotent" if method in ("GET", "PUT", "DELETE", "HEAD", "OPTIONS") else "unsafe")
    stream = op.get("x-omega-stream")
    if stream:
        union = resolve(doc, {"$ref": stream["events"]})
        stream = {**stream, "known_events": list(union["discriminator"]["mapping"])}
    body = resolve(doc, op.get("requestBody", {}))
    content_type = next(iter(body.get("content", {})), None)
    from contract_samples import examples
    return dict(id=f"{adapter}:{name}", adapter=adapter, name=name, method=method, path=path,
                path_params=re.findall(r"\{([^}]+)\}", path), idempotent=keyed, retry=retry,
                content_type=content_type, stream=stream, pagination=op.get("x-omega-pagination"),
                operation_id=op.get("operationId"), namespace=name.split(".")[0],
                success_status=next((int(s) for s in op.get("responses", {}) if str(s).isdigit() and str(s).startswith("2")), 200),
                **examples(doc, op))


def catalog_cases(catalog, source):
    from catalog_contracts import index, reconcile
    updated = reconcile(catalog, source)
    expected = json.loads(json.dumps(catalog))
    for entry in expected["operations"]:
        entry["query"] = sorted(entry["query"])
    if updated != expected:
        raise ValueError("catalog metadata drift: reconcile with the certified Swagger first")
    available = index(source)
    rows = []
    for entry in catalog["operations"]:
        method, path, op, _ = available[entry["operation_id"]]
        row = case(source, method, path, op, entry["id"], "catalog")
        row["catalog"] = entry
        row["namespace"] = entry["public"].split(".")[0]
        row["wrapper"] = {"py": "client." + entry["public"],
                          "ts": "client." + ".".join(camel(p) for p in entry["public"].split("."))}
        rows.append(row)
    return rows


def management_cases(doc, mapping):
    """A supplied management generator must also emit the public call inventory.

    Each wrapped entry uses operation_id + methods, with py/ts public paths and a
    contract invocation fixture: py={args:[], kwargs:{}}, ts={args:[]}. These are
    inputs only: HTTP expectations always come from the independently pinned spec.
    Missing wrappers, fixtures or language adapters fail closed rather than fall
    back to a lower-level executor or count untested management methods as covered.
    """
    from catalog_contracts import index
    from management_contracts import normalize
    mapping = normalize(doc, mapping)
    available = index(doc)
    covered, rows, public_paths = set(), [], {"py": set(), "ts": set()}
    for name, entry in mapping["operations"].items():
        oid = entry["operation_id"]
        if oid not in available:
            raise ValueError(f"unknown management operation: {oid}")
        covered.add(oid)
        if entry.get("unwrapped"):
            continue
        if not entry.get("methods"):
            raise ValueError(f"management public methods missing: {name}")
        method, path, op, _ = available[oid]
        for wrapper in entry["methods"]:
            invocation = wrapper.get("contract", {})
            for language in ("py", "ts"):
                if not wrapper.get(language):
                    missing = wrapper.get("not_offered", {}).get(language)
                    if not missing:
                        raise ValueError(f"management {language} public wrapper/contract missing: {name}")
                    declaration({"owner": name.split(".")[0], **missing})
                    continue
                if not isinstance(invocation.get(language, {}).get("args"), list):
                    raise ValueError(f"management {language} public wrapper/contract missing: {name}")
                if wrapper[language] in public_paths[language]:
                    raise ValueError(f"duplicate management public path: {wrapper[language]}")
                public_paths[language].add(wrapper[language])
            if not wrapper.get("py") and not wrapper.get("ts"):
                raise ValueError(f"management method has no public language: {name}")
            if wrapper.get("py") and not isinstance(invocation["py"].get("kwargs"), dict):
                raise ValueError(f"management Python kwargs missing: {name}")
            row = case(doc, method, path, op, name, "management")
            row["id"] += ":" + (wrapper.get("py") or wrapper["ts"])
            row["wrapper"], row["invocation"] = wrapper, invocation
            descriptor = op.get("x-sdk-management", {})
            row["path_values"] = descriptor.get("fixed_path", {})
            row["public_page"] = descriptor.get("page", False)
            rows.append(row)
    if set(available) - covered:
        raise ValueError("unmapped management operations: " + ", ".join(sorted(set(available) - covered)))
    return rows


def generate(root=ROOT):
    rows, inputs = [], {}
    def source(path):
        inputs[path] = "sha256:" + hashlib.sha256((root / path).read_bytes()).hexdigest()
        return read(root, path)
    ee = source("openapi/platform/generated/futureagi-platform.openapi.json")
    mapping = source("openapi/platform/wrapper-map.json")
    public_inputs = source("openapi/contract-inputs.json")
    from composed_contracts import connector_features, feature_absences
    features = connector_features(source)
    scoped = {}
    for method, path, op, _ in operations(ee):
        sdk = op["x-omega-sdk"]
        name = sdk["family"] + "." + sdk["method"]
        scoped[name] = case(ee, method, path, op, name, "platform")
    for name, entry in mapping["operations"].items():
        if "unwrapped" in entry:
            continue
        if name.startswith("platform.credentials.") and not features["credential_reads"]:
            continue
        row = scoped[name]  # missing wrapped operations fail here
        row["wrappers"] = entry["methods"]
        roots = {w[lang].split(".")[0] for w in entry["methods"] for lang in ("py", "ts") if w.get(lang)} - {"client"}
        fixtures = {**public_inputs["handle_fixtures"], **entry.get("handle_fixtures", {})}
        row["handle_fixtures"] = {root: fixtures[root] for root in roots if root in fixtures}
        rows.append(row)
    lifecycle = "openapi/sdk/lifecycle-source.openapi.json"
    if (root / lifecycle).exists():
        source(lifecycle)
        source("openapi/sdk/lifecycle-source.json")
        for name in ("release-gate", "trial-stability", "metadata-slices"):
            pin = f"openapi/sdk/{name}-source.json"
            if (root / pin).exists():
                source(pin)
    fa = source("openapi/sdk/generated/futureagi-sdk.openapi.json")
    fa_map = source("openapi/sdk/wrapper-map.json")
    index = {op["operationId"]: (method, path, op) for method, path, op, _ in operations(fa)}
    for ns, methods in fa_map.items():
        for public, operation_id in methods.items():
            method, path, op = index[operation_id]
            row = case(fa, method, path, op, ns + "." + public, "core")
            row["py_operation"] = snake(operation_id)
            row["ts_operation"] = camel(operation_id)
            public_ns = {"annotationQueueItems": "annotationQueues.items",
                         "annotationQueueDiscussion": "annotationQueues.discussion",
                         "annotationQueueReview": "annotationQueues.review",
                         "experiments": "experimentsV2"}.get(ns, ns)
            row["wrapper"] = {"py": "client." + ".".join(snake(p) for p in (public_ns + "." + public).split(".")),
                              "ts": "client." + public_ns + "." + public}
            row["envelope_adapter"] = ns.split(".")[0] in ("prompts", "knowledgeBases", "scores")
            row["unwrap_result"] = row["envelope_adapter"] and row["name"] != "scores.forSource"
            if row["name"] == "prompts.getByName":
                row["invocation"] = {"py": {"args": ["fixture"], "kwargs": {"version": "v1"}},
                                     "ts": {"args": ["fixture", {"version": "v1"}]}}
            rows.append(row)
    from composed_contracts import catalog_source, mapped_cases, tracing_cases
    catalog_doc = catalog_source(source("openapi/catalog/source.json"), source("openapi/catalog/models-source.json"))
    rows.extend(catalog_cases(source("openapi/catalog/operations.json"), catalog_doc))
    rows.extend(mapped_cases(source, case, operations, features))
    rows.extend(tracing_cases(source, case, operations))
    mgmt = "openapi/fa-mgmt/generated/spec.json"
    if (root / mgmt).exists():
        rows.extend(management_cases(source(mgmt), source("openapi/fa-mgmt/wrapper-map.json")))
    offerings_path = "openapi/contract-offerings.json"
    offerings = source(offerings_path) if (root / offerings_path).exists() else {}
    modules = offerings.get("modules", {})
    if not (root / mgmt).exists():
        declaration(modules.get("management"))
    elif modules.get("management"):
        raise ValueError("stale management NOT-OFFERED declaration")
    rows.sort(key=lambda r: r["id"])
    schedules, excluded = public_inventory(rows, mapping.get("not_offered", {}), offerings)
    console_groups = ("platform.agents", "platform.environments", "platform.schedules", "platform.approvals", "platform.ratings", "runs")
    hidden = [group in mapping.get("not_offered", {}) for group in console_groups]
    if any(hidden) and not all(hidden):
        raise ValueError("Console hide must declare every Console namespace")
    if all(hidden):
        for row in rows:
            if row["adapter"] == "platform" and any(row["name"].startswith(group + ".") for group in console_groups):
                row["public_absence"] = {"py": ["client.agents", "client.environments"], "ts": ["client.agents", "client.environments"]}
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate contract case identities")
    return {"version": 2, "inputs": inputs, "status_classes": {str(k): v for k, v in STATUSES.items()}, "fa_codes": FA_CODES,
            "modules": modules, "module_absences": public_inputs["module_absences"],
            "namespace_absences": public_inputs["namespace_absences"],
            "feature_absences": feature_absences(features),
            "public_cases": schedules, "not_offered": excluded, "operations": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--ledger", type=Path)
    args = parser.parse_args()
    from wrapper_admission import read_ledger, excluded_operation
    excluded, notice = read_ledger(args.ledger or args.root / "openapi/admission-ledger.json")
    print(notice)
    target = args.out or args.root / OUTPUT
    cases = generate(args.root)
    conflicts = [r["id"] for r in cases["operations"] if excluded_operation(r["name"], r, excluded)]
    if conflicts:
        raise SystemExit("public operations excluded by admission ledger: " + ", ".join(conflicts))
    text = json.dumps(cases, indent=2) + "\n"
    if args.check:
        if not target.exists() or target.read_text() != text:
            raise SystemExit("contract cases are stale; regenerate with scripts/platform/contract_cases.py")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    print(f"contract cases: {len(json.loads(text)['operations'])} wrapped operations")


if __name__ == "__main__":
    main()
