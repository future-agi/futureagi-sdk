#!/usr/bin/env python3
"""Recover queue field direction omitted by Swagger 2 from the server snapshot.

The historical AnnotationQueue model is also a public request builder. Keep its
write-only attributes optional for compatibility, but give request bodies their
own schema with the server's required inputs. Responses never require those
inputs. This runs before either language generator, not on generated source.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


SNAPSHOT = Path("tests/fixtures/server-contracts/annotation-queue-create.json")


def normalize(spec, snapshot):
    schemas = spec.get("components", {}).get("schemas", {})
    if "AnnotationQueue" not in schemas:
        return
    queue = schemas["AnnotationQueue"]
    fields = snapshot["serializer"]["declared_fields"]
    write_only = {name for name, field in fields.items() if field.get("write_only")}
    for name in write_only:
        # A changed upstream shape must be reviewed, not patched by inventing a field.
        queue["properties"][name]["writeOnly"] = True
    request = copy.deepcopy(queue)
    request["required"] = list(snapshot["create"]["required"])
    request["properties"] = {name: field for name, field in request["properties"].items()
                             if not field.get("readOnly")}
    if not set(request["required"]) <= request["properties"].keys():
        raise ValueError("queue create snapshot requires a missing or read-only property")
    schemas["AnnotationQueueRequest"] = request
    queue["required"] = [name for name in queue.get("required", []) if name not in write_only]

    def request_refs(node):
        if isinstance(node, dict):
            if node.get("$ref") == "#/components/schemas/AnnotationQueue":
                node["$ref"] = "#/components/schemas/AnnotationQueueRequest"
            for value in node.values():
                request_refs(value)
        elif isinstance(node, list):
            for value in node:
                request_refs(value)

    # Request-body components may be shared by create, put and patch. Do not
    # rewrite schema references in responses or in the retained shared model.
    request_refs(spec.get("components", {}).get("requestBodies", {}))
    for path in spec.get("paths", {}).values():
        for operation in path.values():
            if isinstance(operation, dict):
                request_refs(operation.get("requestBody", {}))


def main():
    path = Path(sys.argv[1])
    spec = json.loads(path.read_text())
    if "AnnotationQueue" in spec.get("components", {}).get("schemas", {}):
        root = Path(__file__).resolve().parents[1]
        normalize(spec, json.loads((root / SNAPSHOT).read_text()))
        path.write_text(json.dumps(spec, indent=2) + "\n")


if __name__ == "__main__":
    main()
