"""Sync scoped operation groups from one immutable product commit without upgrading the rest.

    python sdkgen/sync_scoped_contract.py /path/to/product PRODUCT_COMMIT BASELINE_SDK_COMMIT [--scopes NAME ...]

Each scope in SCOPES names a set of product MCP tools. The catalog operations in those
groups (including scoped SDK-only routes) take their contract from the product's OpenAPI
at PRODUCT_COMMIT; every other operation
keeps the bytes of the SDK slice committed at BASELINE_SDK_COMMIT. Both inputs are read by
Git object ID, not from a working tree. contracts/swagger.json records both sources in
`x-contract-sources`; the normal release sync (sync_contract.py) supersedes this mixed-source
slice, and BACKEND_VERSION is not a claim that the pinned image serves the scoped operations.

Before writing, every scoped MCP mapping is checked against the product tool it names:
the scope's tool set, group, access and open-world hints, method, path and operationId, the
placement, requiredness and wire schema of each input, page caps, response unwrapping, and,
for the scopes in DESCRIBED_SCOPES, the description byte for byte (check_mcp_descriptions.py).

`--scopes` re-syncs only the named scopes; the default is every scope. Every other scope is
pinned: its paths, definitions, catalog entries and x-contract-sources record stay exactly as
the baseline slice (then a previously synced scoped slice) has them, and none of it is checked
against the product. Product-side pairing uses this to own only the scope it ships, so a product
change to another scope can only show up in the SDK's own pairing checks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import check_mcp_descriptions
import sync_contract
import yaml
from generator.catalog import Op, load, resolve

SWAGGER = "api_contracts/openapi/swagger.json"
MCP = "futureagi/mcp_server/catalog/tools.generated.json"
TOOLS_YAML = check_mcp_descriptions.TOOLS_YAML

# A scope is a set of product MCP tools: a fixed list, or every tool of one product MCP group.
# `path_prefix` ties a scope's catalog ids to its routes; `idempotent_is_get` is the SQL rule
# that only its reads are idempotent (epoch's add_evidence_import_cases is an idempotent POST).
SCOPES: dict[str, dict] = {
    "sql": {
        "tools": {"run_sql", "get_sql_result", "cancel_sql", "get_sql_catalog"},
        "id_prefixes": ("sql.",),
        "path_prefix": "/tracer/sql-query/",
        "idempotent_is_get": True,
    },
    "epoch": {"product_group": "epoch"},
    "skills": {
        "product_group": "skills",
        "path_prefix": "/model-hub/skills/",
        "id_prefixes": ("skills.", "contexts.", "skill_consumption.", "context_credentials."),
        "include_sdk_only": True,
    },
}
DESCRIBED_SCOPES = ("epoch",)  # catalog descriptions copied from product tools.yaml


def _blob(repo: Path, commit: str, path: str) -> bytes:
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("contract sources require full commit hashes")
    return subprocess.check_output(["git", "-C", str(repo), "show", f"{commit}:{path}"])


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


_SCHEMA_KEYS = ("type", "format", "enum", "minimum", "maximum", "minLength", "maxLength", "default")


def _wire_schema(schema: dict) -> dict:
    """Keep only input constraints that must agree across OpenAPI and MCP.

    OpenAPI marks a nullable input `x-nullable: true`; the product's MCP generator writes the
    same input as `anyOf: [schema, {type: null}]` (mcp_server/tool_generation.py _json_schema).
    Both read as the inner schema plus `nullable: true`."""
    any_of = schema.get("anyOf")
    if isinstance(any_of, list) and len(any_of) == 2 and {"type": "null"} in any_of:
        inner = next(child for child in any_of if child != {"type": "null"})
        return {**_wire_schema(inner), "nullable": True}
    result = {key: schema[key] for key in _SCHEMA_KEYS if key in schema}
    if "items" in schema:
        result["items"] = _wire_schema(schema["items"])
    if schema.get("x-nullable"):
        result["nullable"] = True
    return result


def _check_mcp_parameters(op: Op, tool: dict, *, max_page_size: dict | None = None) -> None:
    """Compare a scoped tool's input placement, requiredness and schemas to OpenAPI."""
    expected = {loc: sorted(p.name for p in op.params_in(loc)) for loc in ("path", "query", "body")}
    actual = tool["request"]["parameters"]
    if {loc: sorted(names) for loc, names in actual.items()} != expected:
        raise ValueError(f"scoped MCP parameter placement mismatch: {op.id}")
    schema = tool["inputSchema"]
    params = {p.name: p for p in op.params}
    if set(schema["properties"]) != set(params):
        raise ValueError(f"scoped MCP input properties mismatch: {op.id}")
    if sorted(schema.get("required", [])) != sorted(p.name for p in op.params if p.required):
        raise ValueError(f"scoped MCP required parameters mismatch: {op.id}")
    for name, param in params.items():
        expected_schema = _wire_schema(param.schema)
        if max_page_size and name in max_page_size:
            expected_schema["maximum"] = max_page_size[name]
        if _wire_schema(schema["properties"][name]) != expected_schema:
            raise ValueError(f"scoped MCP input schema mismatch: {op.id}.{name}")


def _access(hints: dict) -> str:
    if hints["readOnlyHint"]:
        return "read"
    return "destructive" if hints["destructiveHint"] else "write"


def _manifest_tools(manifest: dict, source_raw: bytes) -> dict[str, dict]:
    """The product tools by name, after checking the manifest is internally consistent.

    Older manifests bind the OpenAPI bytes (source_contract_sha256); newer ones fingerprint the
    tool names (tool_names_sha256). Either is checked when present, and the per-tool checks below
    bind each scoped tool to the OpenAPI operation of the same commit."""
    rows = manifest.get("tools") if isinstance(manifest, dict) else None
    if not isinstance(rows, list) or not all(
        isinstance(t, dict) and isinstance(t.get("name"), str) and t["name"].strip() for t in rows
    ):
        raise ValueError("invalid product MCP manifest")
    tools = {t["name"]: t for t in rows}
    if len(tools) != len(rows) or len(tools) != manifest.get("tool_count"):
        raise ValueError("invalid product MCP manifest")
    if "source_contract_sha256" in manifest and manifest["source_contract_sha256"] != _sha256(source_raw):
        raise ValueError("product MCP and OpenAPI hashes disagree")
    if "tool_names_sha256" in manifest:
        names = "\n".join(sorted(tools)).encode()
        if manifest["tool_names_sha256"] != _sha256(names):
            raise ValueError("product MCP tool-name fingerprint disagrees with its tools")
    elif "source_contract_sha256" not in manifest:
        raise ValueError("product MCP manifest has no fingerprint")
    return tools


def scope_tools(name: str, tools: dict[str, dict]) -> set[str]:
    scope = SCOPES[name]
    if "tools" in scope:
        return set(scope["tools"])
    return {tool for tool, spec in tools.items() if spec["group"] == scope["product_group"]}


def _scope_of(entry: dict, scoped: dict[str, set[str]]) -> str | None:
    mapping = entry.get("surfaces", {}).get("mcp")
    if mapping in (None, False):
        return None
    name = mapping.get("name") or entry["id"].replace(".", "_")
    hits = [scope for scope, names in scoped.items() if name in names]
    return hits[0] if hits else None


def _check_tool(spec: dict, entry: dict, op: Op, tool: dict, scope: dict) -> None:
    mapping = op.surfaces["mcp"]
    operation_id = spec["paths"][op.path][op.method.lower()]["operationId"]
    hints = tool["annotations"]
    if (mapping["group"] != tool["group"] or mapping["access"] != _access(hints)
            or bool(mapping.get("open_world", False)) != bool(hints["openWorldHint"])):
        raise ValueError(f"scoped MCP exposure mismatch: {entry['id']}")
    if scope.get("idempotent_is_get") and hints["idempotentHint"] != (op.method == "GET"):
        raise ValueError(f"scoped MCP exposure mismatch: {entry['id']}")
    # MCP unwraps `result` when the body has one; the SDK unwraps a declared {status, result}.
    # The two agree when both unwrap, or when the SDK does not and no success body has `result`.
    unwrap = tool["response"]["unwrap"]
    resolved = resolve(spec, op.returns) or {}
    agree = unwrap == "result" if op.unwrap == "result" else (
        unwrap is None or (unwrap == "result" and "result" not in resolved.get("properties", {}))
    )
    if not agree:
        raise ValueError(f"scoped MCP response unwrap mismatch: {entry['id']}")
    for field, cap in mapping.get("max_page_size", {}).items():
        if tool["inputSchema"]["properties"][field].get("maximum") != cap:
            raise ValueError(f"scoped MCP page limit mismatch: {entry['id']}.{field}")
    if (tool["request"]["method"], tool["request"]["path"], tool["source"]["operationId"]) != (
        op.method, op.path, operation_id
    ):
        raise ValueError(f"scoped MCP operation mismatch: {entry['id']}")
    _check_mcp_parameters(op, tool, max_page_size=mapping.get("max_page_size"))


def _merge_paths(baseline: dict, scoped: dict) -> dict:
    """Per path and method: each operation comes from one side; shared path parameters must agree."""
    merged = {path: dict(item) for path, item in baseline.items()}
    for path, item in scoped.items():
        target = merged.setdefault(path, {})
        for key, value in item.items():
            if key in target and target[key] != value:
                raise ValueError(f"scoped projection collides with baseline routes or definitions: {path} {key}")
            target[key] = value
    return merged


def check_scopes(source: dict, source_raw: bytes, manifest: dict, yaml_raw: bytes,
                 entries: list[dict], *, scopes: tuple[str, ...] | None = None,
                 pinned: dict[str, list[str]] | None = None,
                 ) -> tuple[dict[str, set[str]], dict[str, list[dict]], list[dict]]:
    """Check the scoped catalog entries against one product commit's OpenAPI, MCP manifest and
    tools.yaml, all passed in already read. Returns (tool names per scope, catalog entries per
    scope, unscoped entries) and raises ValueError on the first mismatch.

    compose() runs this before it writes the slice; pair_check.py runs it against the product
    commit a dev or pull-request build is paired with. Unscoped entries are only partitioned
    here: whether the product still serves them is compose()'s concern, not the pairing's.

    `scopes` names the scopes checked against this product (default: all). Every other scope
    takes its tool names from `pinned`, the committed record of the slice it stays pinned to;
    its entries are partitioned the same way but never compared with the product."""
    scopes = tuple(SCOPES) if scopes is None else tuple(scopes)
    if not scopes or set(scopes) - set(SCOPES) or len(set(scopes)) != len(scopes):
        raise ValueError(f"invalid scope selection: {list(scopes)}; choose from {sorted(SCOPES)}")
    pinned = pinned or {}
    unpinned = sorted(name for name in SCOPES if name not in scopes and name not in pinned)
    if unpinned:
        raise ValueError(f"a pinned scope needs its committed tool record: {unpinned}")
    tools = _manifest_tools(manifest, source_raw)
    scoped_names = {name: scope_tools(name, tools) if name in scopes else set(pinned[name]) for name in SCOPES}
    if any(not names for names in scoped_names.values()):
        raise ValueError(f"a scope has no product tools: {sorted(n for n, t in scoped_names.items() if not t)}")
    if any(a != b and scoped_names[a] & scoped_names[b] for a in SCOPES for b in SCOPES):
        raise ValueError("scopes overlap")

    in_scope: dict[str, list[dict]] = {name: [] for name in SCOPES}
    existing: list[dict] = []
    for entry in entries:
        method = entry["operation"]["method"]
        path = entry["operation"]["path"]
        scope = _scope_of(entry, scoped_names)
        group = (entry.get("surfaces", {}).get("mcp") or {}).get("group")
        for name, spec in SCOPES.items():
            if "id_prefixes" in spec:
                by_id = entry["id"].startswith(spec["id_prefixes"])
                if by_id and spec.get("include_sdk_only") and entry["surfaces"].get("mcp") in (None, False):
                    scope = name
                if by_id != path.startswith(spec["path_prefix"]) or by_id != (scope == name):
                    raise ValueError(f"{name} scope mismatch: {entry['id']}")
            # A catalog entry in a scope's MCP group must name one of that group's product tools.
            if "product_group" in spec and group == spec["product_group"] and scope != name:
                raise ValueError(f"{name} scope mismatch: {entry['id']} is in MCP group {group}, "
                                 f"but the product has no {group} tool of that name")
        if scope in scopes and method.lower() not in source["paths"].get(path, {}):
            raise ValueError(f"selected operation missing on product: {method} {path}")
        (in_scope[scope] if scope else existing).append(entry)

    for name, selected in in_scope.items():
        if name not in scopes:
            continue  # pinned: the SDK's own pairing compares it with the product, not this sync
        mapped = [mapping.get("name") or entry["id"].replace(".", "_") for entry in selected
                  if isinstance(mapping := entry["surfaces"].get("mcp"), dict)]
        if len(mapped) != len(set(mapped)) or set(mapped) != scoped_names[name]:
            raise ValueError(
                f"expected exactly one catalog mapping per {name} tool: missing "
                f"{sorted(scoped_names[name] - set(mapped))}, extra or repeated "
                f"{sorted({n for n in mapped if n not in scoped_names[name] or mapped.count(n) > 1})}"
            )
        for op, entry in zip(load(source, {"operations": selected}), selected):
            if "mcp" in op.surfaces:
                _check_tool(source, entry, op, tools[op.surfaces["mcp"]["name"]], SCOPES[name])
        if name in DESCRIBED_SCOPES:
            problems = check_mcp_descriptions.compare(
                {"operations": entries}, check_mcp_descriptions.yaml_tools(yaml_raw), groups=(SCOPES[name]["product_group"],)
            )
            if problems:
                raise ValueError(f"{name} descriptions differ from product tools.yaml: " + "; ".join(problems))
    return scoped_names, in_scope, existing


def used_schemes(spec: dict, entries: list[dict]) -> list[str]:
    schemes = set()
    for entry in entries:
        method, path = entry["operation"]["method"].lower(), entry["operation"]["path"]
        for requirement in spec["paths"][path][method].get("security", spec["security"]):
            schemes.update(requirement)
    return sorted(schemes)


def _baseline_openapi(old: dict) -> str:
    """Read the release OpenAPI digest only from a complete, unambiguous source record."""
    def require_hash(record: dict, key: str, length: int, scope: str) -> str:
        value = record.get(key)
        if not isinstance(value, str) or not re.fullmatch(rf"[0-9a-f]{{{length}}}", value):
            raise ValueError(f"invalid SDK baseline: {scope}.{key} must be {length} lowercase hex characters")
        return value

    if "x-contract-sources" not in old:
        return require_hash(old, "x-source-sha256", 64, "release")

    sources = old["x-contract-sources"]
    if ("x-source-sha256" in old or not isinstance(sources, dict) or "other" not in sources
            or len(sources) < 2 or sources.keys() - {"other", *SCOPES}):
        raise ValueError("invalid scoped SDK baseline; expected a release slice or previously synced scopes")
    for scope, record in sources.items():
        if not isinstance(record, dict):
            raise ValueError(f"invalid SDK baseline: {scope} must be a source record")
        require_hash(record, "openapi_sha256", 64, scope)
        if scope == "other":
            require_hash(record, "sdk_commit", 40, scope)
            require_hash(record, "slice_sha256", 64, scope)
        else:
            require_hash(record, "backend_commit", 40, scope)
            require_hash(record, "mcp_sha256", 64, scope)
            require_hash(record, "tools_yaml_sha256", 64, scope)
            tools = record.get("tools")
            if (not isinstance(tools, list) or not tools or not all(isinstance(t, str) and t.strip() for t in tools)
                    or len(set(tools)) != len(tools)):
                raise ValueError(f"invalid SDK baseline: {scope}.tools must list unique, nonblank tool names")
    return sources["other"]["openapi_sha256"]


def compose(product: Path, commit: str, baseline_sdk: str, scopes: tuple[str, ...] | None = None) -> dict:
    old_raw = _blob(sync_contract.ROOT, baseline_sdk, "sdkgen/contracts/swagger.json")
    source_raw = _blob(product, commit, SWAGGER)
    tools_raw = _blob(product, commit, MCP)
    yaml_raw = _blob(product, commit, TOOLS_YAML)
    old, source, manifest = map(json.loads, (old_raw, source_raw, tools_raw))
    other_openapi = _baseline_openapi(old)
    entries = yaml.safe_load(sync_contract.CATALOG.read_text())["operations"]
    selection = tuple(SCOPES) if scopes is None else tuple(scopes)
    # A strict subset pins every other scope, and the unscoped operations, to the baseline slice.
    partial = set(selection) != set(SCOPES)
    old_sources = old.get("x-contract-sources") if partial else None
    if partial and not isinstance(old_sources, dict):
        raise ValueError("pinning scopes needs a previously synced scoped SDK slice as the baseline")
    pinned = {}
    for name in SCOPES:
        if partial and name not in selection:
            if not isinstance(old_sources.get(name), dict):
                raise ValueError(f"the SDK baseline records no {name} source to pin")
            pinned[name] = old_sources[name]["tools"]
    scoped_names, in_scope, existing = check_scopes(source, source_raw, manifest, yaml_raw, entries,
                                                    scopes=selection, pinned=pinned)
    if not partial:
        # Upgrading every scope at once: the product must still serve each unscoped route.
        for entry in existing:
            method, path = entry["operation"]["method"], entry["operation"]["path"]
            if method.lower() not in source["paths"].get(path, {}):
                raise ValueError(f"selected operation missing on product: {method} {path}")
    kept = existing + [entry for name in SCOPES if name not in selection for entry in in_scope[name]]

    # The baseline holds the catalog's operations and nothing else, and every unscoped operation.
    present = [e for e in entries if e["operation"]["method"].lower() in old["paths"].get(e["operation"]["path"], {})]
    if sync_contract.project(old, present) != (old["paths"], old["definitions"]):
        raise ValueError("the SDK baseline holds operations or definitions outside the catalog")
    old_paths, old_defs = sync_contract.project(old, kept)
    scoped = [entry for name in selection for entry in in_scope[name]]
    new_paths, new_defs = sync_contract.project(source, scoped)
    if any(old_defs[k] != new_defs[k] for k in old_defs.keys() & new_defs.keys()):
        raise ValueError("scoped projection collides with baseline routes or definitions")
    paths = _merge_paths(old_paths, new_paths)
    if (any(old[key] != source[key] for key in ("swagger", "security")) or
            any(source["securityDefinitions"].get(k) != v for k, v in old["securityDefinitions"].items())):
        raise ValueError("product and SDK baseline dialect/auth differ")

    # Preserve baseline schemes; import only additional schemes used by scoped routes.
    schemes = dict(old["securityDefinitions"])
    for scheme in used_schemes(source, scoped):
        schemes[scheme] = source["securityDefinitions"][scheme]

    product_record = {"backend_commit": commit, "openapi_sha256": _sha256(source_raw),
                      "mcp_sha256": _sha256(tools_raw), "tools_yaml_sha256": _sha256(yaml_raw)}
    if partial:
        # Pinned records, and the baseline's own `other`, are copied byte for byte.
        sources = {name: {**product_record, "tools": sorted(scoped_names[name])} if name in selection
                   else old_sources[name] for name in SCOPES}
        sources["other"] = old_sources["other"]
    else:
        sources = {
            **{name: {**product_record, "tools": sorted(scoped_names[name])} for name in SCOPES},
            "other": {"sdk_commit": baseline_sdk, "slice_sha256": _sha256(old_raw),
                      "openapi_sha256": other_openapi},
        }
    return {
        **{key: old[key] for key in ("swagger", "info", "security")},
        "securityDefinitions": schemes,
        "x-contract-sources": sources,
        "paths": dict(sorted(paths.items())),
        "definitions": dict(sorted({**old_defs, **new_defs}.items())),
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("product", type=Path, help="a clone of future-agi/future-agi")
    parser.add_argument("commit", help="full product commit for the scoped groups")
    parser.add_argument("baseline_sdk", help="full SDK commit whose slice supplies unchanged operations")
    parser.add_argument("--scopes", nargs="+", choices=sorted(SCOPES), metavar="SCOPE",
                        help="re-sync only these scopes; the others stay pinned to the baseline slice")
    args = parser.parse_args(argv)
    result = compose(args.product, args.commit, args.baseline_sdk, tuple(args.scopes) if args.scopes else None)
    sync_contract.OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {sync_contract.OUT.relative_to(sync_contract.ROOT)}: {len(result['paths'])} paths, "
          f"{len(result['definitions'])} definitions")


if __name__ == "__main__":
    main()
