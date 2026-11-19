"""Retain explicitly pinned lifecycle extensions while repinning the base Swagger.

The projection comes from upstream Swagger bytes, never from a generated client.
A base contract's own operations take precedence. Conflicting extension schema
names are qualified rather than overwriting base schemas.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from catalog_contracts import project

PROJECTION = "openapi/sdk/lifecycle-source.openapi.json"
PIN = "openapi/sdk/lifecycle-source.json"


def project_source(swagger, pin):
    scoped = copy.deepcopy(swagger)
    scoped["paths"] = {}
    operations = []
    for route in pin["operations"]:
        method, path = route.split(" ", 1)
        item = swagger["paths"][path]
        op = item[method.lower()]
        target = scoped["paths"].setdefault(path, {})
        target[method.lower()] = op
        for key in ("parameters", "servers"):
            if key in item:
                target[key] = item[key]
        operations.append({"operation_id": op["operationId"], "public": route})
    return project(scoped, {"operations": operations})


def stage(root, swagger_path, extensions=()):
    pin = json.loads((root / PIN).read_text())
    data = swagger_path.read_bytes()
    value = project_source(json.loads(data), pin)
    value["x-source-sha256"] = "sha256:" + hashlib.sha256(data).hexdigest()
    # These are successive, recorded amendments of the lifecycle contract, not
    # snapshots of generated SDK types. Their order is part of the input contract.
    expected = [name for name in ("release-gate", "trial-stability", "metadata-slices")
                if (root / f"openapi/sdk/{name}-source.json").exists()]
    supplied = {path.stem: path for path in extensions}
    if set(supplied) != set(expected) or len(supplied) != len(extensions):
        raise ValueError("supply every recorded lifecycle extension exactly once: " + ", ".join(expected))
    sources = {}
    for name in expected:
        amendment = json.loads((root / f"openapi/sdk/{name}-source.json").read_text())
        data = supplied[name].read_bytes()
        update = project_source(json.loads(data), amendment)
        for path, item in update["paths"].items():
            value["paths"].setdefault(path, {}).update(item)
        definitions = value.setdefault("definitions", {})
        for schema_name, schema in update.get("definitions", {}).items():
            prior = definitions.get(schema_name, {})
            if prior.get("properties") and schema.get("properties"):
                # Generated Python models accept positional arguments. Retain old
                # field positions and append newly added fields, as the recorded
                # incremental schema updates did before full regeneration.
                names = list(dict.fromkeys([*prior["properties"], *schema["properties"]]))
                schema["properties"] = {key: schema["properties"][key] for key in names
                                        if key in schema["properties"]}
            definitions[schema_name] = schema
        sources[name] = {"pin": f"openapi/sdk/{name}-source.json",
                         "sha256": "sha256:" + hashlib.sha256(data).hexdigest()}
    value["x-extension-sources"] = sources
    (root / PROJECTION).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    return value


def merge(base, extension):
    result = copy.deepcopy(base)
    extension = copy.deepcopy(extension)
    definitions = result.setdefault("definitions", {})
    renames = {name: "ContractExtension" + name for name, schema in extension.get("definitions", {}).items()
               if name in definitions}
    def rewrite(value):
        if isinstance(value, list):
            return [rewrite(v) for v in value]
        if not isinstance(value, dict):
            return value
        value = {k: rewrite(v) for k, v in value.items()}
        ref = value.get("$ref", "")
        if ref.startswith("#/definitions/") and ref[14:] in renames:
            value["$ref"] = "#/definitions/" + renames[ref[14:]]
        return value
    extension = rewrite(extension)
    for name, schema in extension.get("definitions", {}).items():
        target = renames.get(name, name)
        if target in definitions and definitions[target] != schema:
            raise ValueError(f"ambiguous extension schema: {target}")
        definitions[target] = schema
    for path, item in extension["paths"].items():
        target = result["paths"].setdefault(path, {})
        for method, operation in item.items():
            if method not in target:
                target[method] = operation
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path)
    parser.add_argument("extension", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    result = merge(json.loads(args.base.read_text()), json.loads(args.extension.read_text()))
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
