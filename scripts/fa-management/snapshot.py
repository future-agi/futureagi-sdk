"""Snapshot a scoped management Swagger and its admin schema from local files."""
import argparse
import hashlib
import json
from pathlib import Path


def public_schema(value):
    """Remove documentation prose, not schema keys, constraints or wire values.

    Admin descriptions can include private development notes. The raw input stays
    digest-bound; public snapshots retain every non-documentation schema field.
    """
    if isinstance(value, list):
        return [public_schema(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        if key == "description":
            continue
        if key in ("properties", "$defs", "definitions", "patternProperties"):
            # These keys name wire fields/types, including a field named description.
            result[key] = {name: public_schema(schema) for name, schema in item.items()}
        elif key in ("default", "example", "examples", "enum", "const"):
            result[key] = item  # Literal values are wire data, not schema prose.
        else:
            result[key] = public_schema(item)
    return result


def snapshot(swagger, admin, out):
    raw = swagger.read_bytes()
    source = json.loads(raw)
    prefixes = ("/agentcc/org-configs/", "/agentcc/api-keys/", "/agentcc/provider-credentials/")
    paths = {p: ops for p, ops in source["paths"].items()
             if p.startswith(prefixes) or p == "/agentcc/gateways/{id}/update-config/"}
    definitions = {}

    def collect(value):
        if isinstance(value, dict):
            ref = value.get("$ref", "")
            if ref.startswith("#/definitions/"):
                name = ref.rsplit("/", 1)[1]
                if name not in definitions:
                    definitions[name] = source["definitions"][name]
                    collect(definitions[name])
            for item in value.values():
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)

    collect(paths)
    result = {"swagger": "2.0", "info": {"title": "Gateway Management", "version": "1"},
              "basePath": source.get("basePath", "/"), "paths": paths, "definitions": definitions}
    out.mkdir(parents=True, exist_ok=True)
    public_admin = public_schema(json.loads(admin.read_bytes()))
    admin_bytes = (json.dumps(public_admin, indent=2, sort_keys=True) + "\n").encode()
    for name, value in (("swagger.json", result), ("admin.schema.json", public_admin),
                        ("source.json", {"swagger_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
                         "admin_sha256": "sha256:" + hashlib.sha256(admin.read_bytes()).hexdigest(),
                         "public_admin_sha256": "sha256:" + hashlib.sha256(admin_bytes).hexdigest()})):
        (out / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--swagger", type=Path, required=True)
    parser.add_argument("--admin", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    snapshot(args.swagger, args.admin, args.out)
