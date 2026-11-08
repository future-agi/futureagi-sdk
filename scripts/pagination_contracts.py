"""Source-evidenced query declarations shared by the SDK generators.

No runtime query-dialect translation is performed. Preserve source-backed selectors
when removing framework-added paging that the endpoint does not support.
The reviewed table, not framework-added Swagger defaults, is the source of truth.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "openapi/sdk/pagination-dialects.json"
PAGING = frozenset({"page", "limit", "page_size", "page_number", "offset", "cursor", "cursor_mode", "current_page_index", "page_token"})


def rows():
    return json.loads(TABLE.read_text())["operations"]


def lookup(method, path):
    return next((row for row in rows() if (row["method"], row["path"]) == (method.upper(), path)), None)


def documentation(method, path):
    row = lookup(method, path)
    return row["documentation"] if row else ""


def describe(text, method, path):
    note = documentation(method, path)
    if note and note in text:
        return text
    return " ".join(part for part in (text, note) if part)


def apply(spec):
    """Project paging overrides onto either Swagger 2 or OpenAPI 3 operations."""
    spec["x-sdk-pagination-dialects"] = "openapi/sdk/pagination-dialects.json"
    for row in rows():
        item = spec.get("paths", {}).get(row["path"], {})
        op = item.get(row["method"].lower())
        if not op:
            continue
        description = op.get("description", "")
        if row["documentation"] not in description:
            op["description"] = description.rstrip() + "\n\n" + row["documentation"]
        if row["in"] != "query":
            continue
        accepted = set(row["accepted"])
        for owner in (item, op):
            if "parameters" in owner:
                owner["parameters"] = [p for p in owner["parameters"] if not (
                    p.get("in") == "query" and p.get("name") in PAGING - accepted)]
        existing = {p.get("name") for p in item.get("parameters", []) + op.get("parameters", []) if p.get("in") == "query"}
        for name in row["accepted"]:
            if name in existing:
                continue
            schema = {"type": "boolean" if name == "cursor_mode" else "string" if name in {"cursor", "page_token"} else "integer"}
            if name in row["bases"]:
                schema["minimum"] = row["bases"][name]
            param = {"name": name, "in": "query", "required": False, "description": row["documentation"]}
            if "openapi" in spec:
                param["schema"] = schema
            else:
                param.update(schema)
            op.setdefault("parameters", []).append(param)
            existing.add(name)
        # Some Swagger actions omit their real selectors but advertise default
        # paging. Removing those defaults must not leave a query?: never client.
        for declared in row.get("non_paging_query_parameters", []):
            name = declared["name"]
            if name in existing:
                continue
            param = {"name": name, "in": "query", "required": False,
                     "description": declared["description"]}
            schema = dict(declared["schema"])
            if "openapi" in spec:
                param["schema"] = schema
            else:
                param.update(schema)
            op.setdefault("parameters", []).append(param)
            existing.add(name)
    return spec


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text())
    args.spec.write_text(json.dumps(apply(spec), indent=2) + "\n")
