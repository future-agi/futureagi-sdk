"""Load the contract + catalog into validated `Op`s. Every emitter starts from this list.

The catalog (`sdkgen/catalog/operations.yaml`) names each operation once; the contract
(`sdkgen/contracts/swagger.json`) describes its parameters and responses. Loading fails
on any catalog mistake, so a bad entry can never reach a generated file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

SURFACES = {"sdk", "mcp"}  # a CLI would be a third surface on the same catalog
STABILITY = {"stable", "beta", "deprecated"}
MCP_ACCESS = {"read", "write", "destructive"}
MCP_KEYS = {"name", "group", "access", "open_world", "max_page_size", "stability"}
CONTRACT_FIXES = {"note", "untyped", "page_items", "returns", "optional_in_response", "body", "body_fields", "body_required", "query"}
FIX_TYPES = {"string", "integer", "number", "boolean", "object", "array", "file", "json"}
DECODE_MODES = {"json", "text", "auto"}  # auto: JSON when the response says so, else the body text
BODY_METHODS = ("post", "put", "patch")


class CatalogError(Exception):
    pass


@dataclass
class Param:
    name: str  # as sent on the wire
    location: str  # path | query | body
    schema: dict
    required: bool
    description: str = ""
    arg_name: str | None = None  # SDK argument name, when it should differ from the wire name


@dataclass
class Op:
    id: str
    description: str
    method: str
    path: str
    operation_id: str
    surfaces: dict[str, dict]
    params: list[Param]
    pagination: dict | None
    unwrap: str | None
    returns: dict | None  # schema of what the caller gets (an item, for paginated ops)
    multipart: bool = False  # form fields + file uploads instead of a JSON body
    decode: str = "json"  # how the response body is read: json | text | auto

    @property
    def namespace(self) -> tuple[str, ...]:
        return tuple(self.id.split(".")[:-1])

    @property
    def method_name(self) -> str:
        return self.id.split(".")[-1]

    @property
    def sends_body(self) -> bool:
        return not self.pagination and self.method in ("POST", "PUT", "PATCH", "DELETE")

    def params_in(self, location: str) -> list[Param]:
        return [p for p in self.params if p.location == location]

    @property
    def file_params(self) -> list[Param]:
        return [p for p in self.params if p.location == "body" and is_file(p.schema)]


# --------------------------------------------------------------------------- #
# Schema helpers shared by the emitters
# --------------------------------------------------------------------------- #


def resolve(spec: dict, schema: dict | None) -> dict | None:
    while schema and "$ref" in schema:
        schema = spec["definitions"][schema["$ref"].rsplit("/", 1)[-1]]
    return schema


def walk(spec: dict, schema: dict | None, dotted: str) -> dict | None:
    for part in dotted.split("."):
        schema = resolve(spec, schema)
        if not schema or part not in schema.get("properties", {}):
            return None
        schema = schema["properties"][part]
    return schema


def class_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def is_file(schema: dict | None) -> bool:
    schema = schema or {}
    return schema.get("type") == "file" or (schema.get("type") == "array" and is_file(schema.get("items")))


def is_json_value(schema: dict | None) -> bool:
    """`x-json-value`: the backend's JsonValueField, any JSON value (a string, number, list or
    object) where drf-yasg's `type: object` would suggest only an object."""
    return bool(schema and schema.get("x-json-value"))


def is_method_field(prop: dict) -> bool:
    """drf-yasg types every DRF SerializerMethodField as a read-only plain string, whatever it
    really returns (seen live: lists and objects), so such fields are typed as unknown."""

    def plain(schema: dict) -> bool:
        return schema.get("type") == "string" and not ({"format", "enum", "maxLength", "minLength", "pattern"} & set(schema))

    if not prop.get("readOnly", False):
        return False
    # Also read-only lists of plain strings: drf-yasg's default for an untyped ListField (seen live: objects).
    return plain(prop) or (prop.get("type") == "array" and plain(prop.get("items", {})))


def model_refs(spec: dict, roots: list[dict]) -> list[str]:
    """Every definition reachable from the given schemas, sorted by name."""
    found: list[str] = []

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            if "$ref" in node:
                name = class_name(node["$ref"])
                if name not in found:
                    found.append(name)
                    visit(spec["definitions"][name])
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    for root in roots:
        visit(root)
    return sorted(found)


def sdk_ops(ops: list[Op]) -> list[Op]:
    return [op for op in ops if "sdk" in op.surfaces]


def namespace_tree(ops: list[Op]) -> dict[tuple[str, ...], list[Op]]:
    """{('datasets',): [...], ('datasets', 'columns'): [...]} for the SDK surface."""
    tree: dict[tuple[str, ...], list[Op]] = {}
    for op in sdk_ops(ops):
        ns = op.namespace
        for i in range(1, len(ns) + 1):
            tree.setdefault(ns[:i], [])
        tree[ns].append(op)
    return tree


def children_of(tree: dict[tuple[str, ...], list[Op]], ns: tuple[str, ...]) -> list[tuple[str, ...]]:
    return sorted(child for child in tree if len(child) == len(ns) + 1 and child[: len(ns)] == ns)


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #


def _normalize_surfaces(raw: Any, op_id: str) -> dict[str, dict]:
    if raw is None:
        raise CatalogError(f"{op_id}: `surfaces` is required")
    if isinstance(raw, list):
        raw = {name: {} for name in raw}
    out: dict[str, dict] = {}
    for name, settings in raw.items():
        if name not in SURFACES:
            raise CatalogError(f"{op_id}: unknown surface {name!r} (expected one of {sorted(SURFACES)})")
        if settings is False:
            continue
        settings = dict(settings or {})
        stability = settings.setdefault("stability", "stable")
        if stability not in STABILITY:
            raise CatalogError(f"{op_id}: {name}.stability must be one of {sorted(STABILITY)}")
        if name == "mcp":
            for key in ("group", "access"):
                if key not in settings:
                    raise CatalogError(f"{op_id}: mcp.{key} is required when the op ships to MCP")
            if settings["access"] not in MCP_ACCESS:
                raise CatalogError(f"{op_id}: mcp.access must be one of {sorted(MCP_ACCESS)}")
            unknown = set(settings) - MCP_KEYS
            if unknown:
                raise CatalogError(f"{op_id}: unknown mcp settings {sorted(unknown)}")
        out[name] = settings
    if not out:
        raise CatalogError(f"{op_id}: ships to no surface")
    return out


def _fix_schema(op_id: str, type_name: str) -> dict:
    """`string`, `object`, `file`, ... or `X[]` for a list of X, as written in a contract_fix."""
    if type_name.endswith("[]"):
        return {"type": "array", "items": _fix_schema(op_id, type_name[:-2])}
    if type_name not in FIX_TYPES:
        raise CatalogError(f"{op_id}: contract_fix type {type_name!r} is not one of {sorted(FIX_TYPES)} or `X[]`")
    if type_name == "array":
        return {"type": "array", "items": {}}
    if type_name == "json":
        return {"type": "object", "x-json-value": True}
    return {"type": type_name}


def _same_shape(a: dict | None, b: dict | None) -> bool:
    """Whether two schemas say the same thing as far as the emitters care (type, items, JSON-value)."""
    a, b = a or {}, b or {}
    if a.get("type") != b.get("type") or is_json_value(a) != is_json_value(b) or is_file(a) != is_file(b):
        return False
    return _same_shape(a.get("items"), b.get("items")) if a.get("type") == "array" else True


def _fix_field(op_id: str, name: str, kind: Any, location: str) -> Param:
    """One `{name: type}` or `{name: {type: T, as: argument_name}}` entry of a contract_fix."""
    arg_name = None
    if isinstance(kind, dict):
        kind, arg_name = kind["type"], kind.get("as")
    return Param(name, location, _fix_schema(op_id, kind), False, arg_name=arg_name)


def _apply_request_fix(op_id: str, fix: dict | None, params: list[Param]) -> list[Param]:
    """Catalog corrections for request parameters the contract describes wrongly.

    body_fields: {name: type}  patches single body fields: a listed field replaces the
                               contract's one (or is added), every other field stays as the
                               contract says, so a field the backend adds later reaches the SDK
    body: {name: type}         replaces every body field; only for a contract that documents the
                               wrong serializer altogether (drf-yasg often shows the response
                               serializer as the request body)
    body_required: [name]      overrides which body fields are required
    query: {name: type}        adds query parameters the contract leaves out
    A value may be {type: T, as: argument_name} when the wire name makes a poor argument.

    Each fix is checked against the contract: once the backend has fixed its contract, a fix
    that no longer changes anything fails the build so it gets removed.
    """
    if not fix or not ({"body", "body_fields", "body_required", "query"} & set(fix)):
        return params
    contract_body = [p for p in params if p.location == "body"]
    if "body" in fix and "body_fields" in fix:
        raise CatalogError(f"{op_id}: contract_fix.body replaces the body; use body_fields alone to patch fields")
    if "body" in fix:
        fixed = [_fix_field(op_id, name, kind, "body") for name, kind in fix["body"].items()]
        if [p.name for p in contract_body] == [p.name for p in fixed] and all(_same_shape(a.schema, b.schema) for a, b in zip(contract_body, fixed)):
            raise CatalogError(f"{op_id}: contract_fix.body is stale: the contract now describes these body fields; use body_fields or drop the fix")
        params = [p for p in params if p.location != "body"] + fixed
    for name, kind in fix.get("body_fields", {}).items():
        patched = _fix_field(op_id, name, kind, "body")
        current = next((p for p in params if p.location == "body" and p.name == name), None)
        if current is not None and _same_shape(current.schema, patched.schema) and (patched.arg_name in (None, current.arg_name)):
            raise CatalogError(f"{op_id}: contract_fix.body_fields.{name} is stale: the contract already says so")
        if current is not None:
            patched.required, patched.description = current.required, current.description
            params[params.index(current)] = patched
        else:
            params.append(patched)
    if "body_required" in fix:
        body = [p for p in params if p.location == "body"]
        unknown = set(fix["body_required"]) - {p.name for p in body}
        if unknown:
            raise CatalogError(f"{op_id}: contract_fix.body_required names unknown body fields {sorted(unknown)}")
        if {p.name for p in body if p.required} == set(fix["body_required"]):
            raise CatalogError(f"{op_id}: contract_fix.body_required is stale: these are the required fields already")
        for p in body:
            p.required = p.name in fix["body_required"]
    for name, kind in fix.get("query", {}).items():
        if any(p.location == "query" and p.name == name for p in params):
            raise CatalogError(f"{op_id}: contract_fix.query.{name} is stale: the contract has that query parameter")
        params.append(_fix_field(op_id, name, kind, "query"))
    return params


def _result_name(op_id: str) -> str:
    return "".join(part.title() for part in op_id.replace(".", "_").split("_")) + "Result"


def _apply_response_fix(op_id: str, spec: dict, fix: dict | None, returns: dict | None, unwrap: str | None):
    """Catalog corrections for responses the contract describes wrongly (found on a live backend).

    returns: Name          the response is really this definition of the contract (e.g. a create
                           that answers with the detail serializer, not the input one)
    returns: {name: type}  the response is an object the contract has no definition for; one named
                           `<Resource><Method>Result` is generated from these fields
    optional_in_response: [field]  the response definition marks a field required that the server
                           never sends (a write-only input the serializer also documents as output);
                           it becomes optional on that definition, for every operation returning it
    page_items: KEY        the contract's array is really a page object whose items are under KEY
    untyped: true          the contract's schema is wrong; return the raw JSON
    Every fix needs a `note` so the backend bug can be fixed at the source. (A missing
    {status, result} envelope needs no fix: the transport unwraps it whenever present.)
    """
    if not fix:
        return returns, unwrap
    unknown = set(fix) - CONTRACT_FIXES
    if unknown:
        raise CatalogError(f"{op_id}: unknown contract_fix keys {sorted(unknown)}")
    if not fix.get("note"):
        raise CatalogError(f"{op_id}: contract_fix needs a `note` describing the contract bug")
    if fix.get("untyped"):
        if "returns" in fix:
            raise CatalogError(f"{op_id}: contract_fix.untyped and contract_fix.returns contradict each other")
        return None, unwrap
    if "returns" in fix:
        target = fix["returns"]
        if isinstance(target, str):
            if target not in spec["definitions"]:
                raise CatalogError(f"{op_id}: contract_fix.returns names {target!r}, which is not a definition of the contract")
            if (returns or {}).get("$ref") == f"#/definitions/{target}":
                raise CatalogError(f"{op_id}: contract_fix.returns is stale: the contract already answers with {target}")
            returns = {"$ref": f"#/definitions/{target}"}
        elif isinstance(target, dict) and target:
            name = _result_name(op_id)
            definition = {
                "type": "object",
                "properties": {field: _fix_schema(op_id, kind) for field, kind in target.items()},
                "x-contract-fix": op_id,  # synthesized from the catalog, not from the backend
            }
            existing = spec["definitions"].get(name)
            if existing is not None and existing != definition:
                raise CatalogError(f"{op_id}: contract_fix.returns would generate {name}, which the contract already defines differently")
            spec["definitions"][name] = definition
            returns = {"$ref": f"#/definitions/{name}"}
        else:
            raise CatalogError(f"{op_id}: contract_fix.returns must be a definition name or {{field: type}}")
    if "optional_in_response" in fix:
        ref = (returns or {}).get("$ref")
        if not ref:
            raise CatalogError(f"{op_id}: contract_fix.optional_in_response needs a response that is a definition of the contract")
        name = class_name(ref)
        definition = spec["definitions"][name]
        relaxed: dict[str, str] = definition.setdefault("x-contract-fix-optional", {})  # field -> the op that declared it
        for field in fix["optional_in_response"]:
            if relaxed.get(field) not in (None, op_id):
                raise CatalogError(f"{op_id}: {name}.{field} is already made optional by {relaxed[field]}'s contract_fix; declare it once")
            if field not in definition.get("required", []) and field not in relaxed:
                raise CatalogError(f"{op_id}: contract_fix.optional_in_response.{field} is stale: {name} does not require it")
            definition["required"] = [f for f in definition.get("required", []) if f != field]
            relaxed[field] = op_id
    if "page_items" in fix:
        if not returns or returns.get("type") != "array":
            raise CatalogError(f"{op_id}: contract_fix.page_items needs an array response in the contract")
        returns = {"type": "object", "properties": {fix["page_items"]: returns}}
    return returns, unwrap


def _contract_params(op_id: str, spec: dict, method: str, item: dict, contract_op: dict) -> list[Param]:
    params: list[Param] = []
    for p in item.get("parameters", []) + contract_op.get("parameters", []):
        if p["in"] == "body":
            body = resolve(spec, p["schema"]) or {}
            # A PATCH is a partial update: the backend accepts any subset of the fields, whatever
            # the contract says (drf-yasg marks the create serializer's required fields). A view
            # that does need a field on PATCH says so with contract_fix.body_required.
            required = set() if method == "patch" else set(body.get("required", []))
            for name, prop in body.get("properties", {}).items():
                if prop.get("readOnly"):
                    continue  # server-owned fields never appear in inputs
                params.append(Param(name, "body", prop, name in required, prop.get("title", "")))
        elif p["in"] in ("path", "query"):
            schema = {k: v for k, v in p.items() if k not in ("name", "in", "required", "description")}
            params.append(Param(p["name"], p["in"], schema, p["in"] == "path" or p.get("required", False), p.get("description", "")))
        elif p["in"] == "formData":
            # A real multipart form (drf-yasg writes one for a view with MultiPartParser):
            # form fields and files are both body params, and the entry needs
            # `operation.multipart: true`, which _load_one enforces for the file fields.
            schema = {k: v for k, v in p.items() if k not in ("name", "in", "required", "description")}
            params.append(Param(p["name"], "body", schema, p.get("required", False), p.get("description", "")))
        else:
            raise CatalogError(f"{op_id}: unsupported parameter location {p['in']!r}")
    return params


def _check_pagination(op_id: str, spec: dict, pagination: dict, params: list[Param], returns: dict | None) -> dict | None:
    """Validate the pagination spec; return the item schema the pager yields."""
    for key in ("page_param", "size_param", "first_page", "items"):
        if key not in pagination:
            raise CatalogError(f"{op_id}: pagination.{key} is required")
    if not isinstance(pagination["first_page"], int):
        raise CatalogError(f"{op_id}: pagination.first_page must be an integer")
    query_names = {p.name for p in params if p.location == "query"}
    for key in ("page_param", "size_param"):
        if pagination[key] not in query_names:
            raise CatalogError(f"{op_id}: pagination.{key}={pagination[key]!r} is not a query param")
    if not ({"next", "total_pages", "total_items"} & set(pagination)):
        raise CatalogError(f"{op_id}: pagination needs `next`, `total_pages` or `total_items` to know when to stop")
    if returns is None:  # an untyped response (contract_fix.untyped) yields raw items
        return None
    items = walk(spec, returns, pagination["items"])
    if not items or items.get("type") != "array":
        raise CatalogError(f"{op_id}: pagination.items={pagination['items']!r} is not an array in the response")
    return items["items"]


def _load_one(spec: dict, entry: dict, seen_mcp: set[str]) -> Op:
    op_id = entry["id"]
    method = entry["operation"]["method"].lower()
    path = entry["operation"]["path"]
    item = spec["paths"].get(path, {})
    if method not in item:
        raise CatalogError(f"{op_id}: {method.upper()} {path} is not in the contract")
    contract_op = item[method]
    fix = entry.get("contract_fix")

    params = _apply_request_fix(op_id, fix, _contract_params(op_id, spec, method, item, contract_op))

    multipart = bool(entry["operation"].get("multipart", False))
    decode = entry["operation"].get("decode", "json")
    if decode not in DECODE_MODES:
        raise CatalogError(f"{op_id}: operation.decode must be one of {sorted(DECODE_MODES)}")
    file_params = [p.name for p in params if p.location == "body" and is_file(p.schema)]
    if multipart and method not in BODY_METHODS:
        raise CatalogError(f"{op_id}: multipart is only meaningful on POST/PUT/PATCH")
    if file_params and not multipart:
        raise CatalogError(f"{op_id}: file params {file_params} need `operation.multipart: true`")

    placeholders = set(re.findall(r"{(\w+)}", path))
    path_params = {p.name for p in params if p.location == "path"}
    if placeholders != path_params:
        raise CatalogError(f"{op_id}: path placeholders {placeholders} != path params {path_params}")

    # What the caller gets back: unwrap the {status, result} envelope, then the page items.
    ok = contract_op["responses"].get("200") or contract_op["responses"].get("201") or {}
    returns = ok.get("schema")
    resolved = resolve(spec, returns) or {}
    unwrap = None
    if {"status", "result"} <= set(resolved.get("properties", {})):
        unwrap = "result"
        returns = resolved["properties"]["result"]
    returns, unwrap = _apply_response_fix(op_id, spec, fix, returns, unwrap)

    pagination = entry.get("pagination")
    sends_body = method in ("post", "put", "patch", "delete") and not pagination
    if any(p.location == "body" for p in params) and not sends_body:
        raise CatalogError(f"{op_id}: has body params, but a {method.upper()}{' paginated' if pagination else ''} call sends no body")
    if pagination:
        returns = _check_pagination(op_id, spec, pagination, params, returns)

    surfaces = _normalize_surfaces(entry.get("surfaces"), op_id)
    input_names = {p.name for p in params if p.location != "path"}
    for name in surfaces.get("mcp", {}).get("max_page_size", {}):
        if name not in input_names:
            raise CatalogError(f"{op_id}: mcp.max_page_size names {name!r}, which is not a query or body param")
    if "mcp" in surfaces:
        name = surfaces["mcp"].get("name", op_id.replace(".", "_"))
        if name in seen_mcp:
            raise CatalogError(f"{op_id}: MCP tool name {name!r} is already used")
        seen_mcp.add(name)
        surfaces["mcp"]["name"] = name

    return Op(
        id=op_id,
        description=entry.get("description") or contract_op.get("description") or contract_op.get("summary") or "",
        method=method.upper(),
        path=path,
        operation_id=contract_op["operationId"],
        surfaces=surfaces,
        params=params,
        pagination=pagination,
        unwrap=unwrap,
        returns=returns,
        multipart=multipart,
        decode=decode,
    )


def load(spec: dict, catalog: dict) -> list[Op]:
    ops: list[Op] = []
    seen_ids: set[str] = set()
    seen_mcp: set[str] = set()
    for entry in catalog["operations"]:
        op_id = entry["id"]
        if not re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+", op_id):
            raise CatalogError(f"{op_id}: id must look like resource.method")
        if op_id in seen_ids:
            raise CatalogError(f"{op_id}: duplicate id")
        seen_ids.add(op_id)
        ops.append(_load_one(spec, entry, seen_mcp))

    namespaces = {tuple(op.id.split(".")[:i]) for op in ops for i in range(1, len(op.id.split(".")))}
    for op in ops:
        if tuple(op.id.split(".")) in namespaces:
            raise CatalogError(f"{op.id}: is both a method and a resource namespace")
    return ops
