"""Scope filtering preserves every non-withdrawn operation and shared model."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_scope_removes_only_exclusive_components_and_is_idempotent(tmp_path):
    shared = {"type": "object", "properties": {"id": {"type": "string"}}}
    operation = {"operationId": "listDatasets", "tags": ["datasets"], "responses": {
        "200": {"schema": {"$ref": "#/components/schemas/Shared"}}
    }}
    spec = {
        "paths": {
            "/model-hub/datasets/": {"get": operation},
            "/simulate/run-tests/": {"get": {"operationId": "listRunTests", "responses": {
                "200": {"schema": {"$ref": "#/components/schemas/Exclusive"}}
            }}},
            "/sdk/api/v1/simulation/runs/": {"get": {"operationId": "listSimulationRuns"}},
        },
        "tags": [{"name": "datasets"}, {"name": "simulate"}],
        "components": {"schemas": {
            "Shared": shared,
            "Exclusive": {"type": "object", "properties": {"shared": {"$ref": "#/components/schemas/Shared"}},
                          "discriminator": {"mapping": {"nested": "#/components/schemas/Nested"}}},
            "Nested": {"type": "object", "properties": {"cycle": {"$ref": "#/components/schemas/Exclusive"}}},
            "UnrelatedExtension": {"type": "string"},
        }, "securitySchemes": {"apiKey": {"type": "apiKey", "in": "header", "name": "X-Api-Key"}}},
    }
    path = tmp_path / "spec.json"
    operations = tmp_path / "operations.txt"
    path.write_text(json.dumps(spec))
    command = ["node", str(ROOT / "scripts/filter-sdk-scope.mjs"), str(path), str(operations)]
    subprocess.run(command, check=True)
    actual = json.loads(path.read_text())
    assert actual["paths"] == {"/model-hub/datasets/": {"get": operation}}
    assert actual["components"]["schemas"] == {"Shared": shared, "UnrelatedExtension": {"type": "string"}}
    assert actual["components"]["securitySchemes"] == spec["components"]["securitySchemes"]
    assert actual["tags"] == [{"name": "datasets"}]
    assert operations.read_text() == "listDatasets\n"
    first = path.read_bytes()
    subprocess.run(command, check=True)
    assert path.read_bytes() == first


def test_retained_extension_keeps_its_shared_dependencies(tmp_path):
    spec = {"paths": {"/simulate/personas/": {"get": {"responses": {
        "200": {"schema": {"$ref": "#/components/schemas/Shared"}}
    }}}}, "components": {"schemas": {
        "Shared": {"type": "string"},
        "Extension": {"properties": {"value": {"$ref": "#/components/schemas/Shared"}}},
    }}}
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    subprocess.run(["node", str(ROOT / "scripts/filter-sdk-scope.mjs"), str(path)], check=True)
    actual = json.loads(path.read_text())
    assert actual["paths"] == {}
    assert actual["components"] == spec["components"]
