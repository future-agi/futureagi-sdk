"""Namespace drift includes referenced schemas, not only HTTP policy fields."""
from __future__ import annotations

import hashlib
import json

METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def closure(doc, value, seen=None):
    seen = set() if seen is None else seen
    if isinstance(value, list):
        return [closure(doc, item, set(seen)) for item in value]
    if not isinstance(value, dict):
        return value
    result = {k: closure(doc, v, set(seen)) for k, v in value.items() if k != "$ref"}
    ref = value.get("$ref")
    if ref:
        if not ref.startswith("#/"):
            raise ValueError(f"non-local contract reference {ref}")
        if ref in seen:
            result["$recursiveRef"] = ref
        else:
            node = doc
            for part in ref[2:].split("/"):
                node = node[part.replace("~1", "/").replace("~0", "~")]
            result["$resolved"] = closure(doc, node, seen | {ref})
    return result


def signature(doc, operation):
    return hashlib.sha256(json.dumps(closure(doc, operation), sort_keys=True).encode()).hexdigest()


def inventory(doc, aliases=None):
    aliases = aliases or {}
    rows = {}
    for path, item in doc.get("paths", {}).items():
        for method, op in item.items():
            if method not in METHODS:
                continue
            sdk = op.get("x-omega-sdk", {})
            name = ".".join((sdk.get("family", ""), sdk.get("method", ""))) if sdk else op.get("operationId", method + " " + path)
            if aliases and op.get("operationId") not in aliases:
                continue  # admission inventory owns unwrapped operations
            names = aliases.get(op.get("operationId"), [name])
            for public in names:
                namespace = ".".join(public.split(".")[:2]) if public.startswith("platform.") else public.split(".")[0]
                rows[public] = {"namespace": namespace, "method": method.upper(), "path": path,
                                "signature": signature(doc, {"operation": op, "parameters": item.get("parameters", []),
                                    "url": {"basePath": doc.get("basePath", "/"), "host": doc.get("host"),
                                            "schemes": op.get("schemes", doc.get("schemes")),
                                            "servers": op.get("servers", item.get("servers", doc.get("servers", [])))}})}
    return rows


def compare(before, after):
    namespaces = {}
    for name in sorted(set(before) | set(after)):
        old, new = before.get(name), after.get(name)
        if old == new:
            continue
        namespace = (new or old)["namespace"]
        group = namespaces.setdefault(namespace, {"verdict": "NOT-EVALUATED", "added": [], "removed": [], "changed": []})
        key = "added" if old is None else "removed" if new is None else "changed"
        group[key].append(name)
    return namespaces
