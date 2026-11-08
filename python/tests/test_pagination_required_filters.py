"""Removing bogus paging must not leave a source-backed selector undeclared.

FA d502de895f0add84ed2eaacd4bb6b24287935a25, unchanged at d5cb8abd:
model_hub/views/prompt_labels.py:382-402 requires template_id or template_name.
"""
import ast
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ROUTE = "/model-hub/prompt-labels/template-labels/"
SELECTORS = {"template_id", "template_name"}


def projection():
    spec = importlib.util.spec_from_file_location(
        "pagination_selector_projection", ROOT / "scripts/pagination_contracts.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("openapi", [False, True], ids=["swagger2", "openapi3"])
def test_projection_declares_source_backed_nonpaging_selectors(openapi):
    kind = {"openapi": "3.0.3"} if openapi else {"swagger": "2.0"}
    old = {"name": "page", "in": "query", "required": False}
    old.update({"schema": {"type": "integer"}} if openapi else {"type": "integer"})
    source = {**kind, "paths": {ROUTE: {"get": {"parameters": [old]}}}}
    result = projection().apply(source)
    parameters = result["paths"][ROUTE]["get"]["parameters"]
    assert {p["name"] for p in parameters if p["in"] == "query"} == SELECTORS
    for param in parameters:
        assert param["required"] is False  # The server accepts either selector.
        assert (param["schema"] if openapi else param)["type"] == "string"
    # The normal build and reuse-spec paths both apply the projection.
    snapshot = json.loads(json.dumps(result))
    assert projection().apply(result) == snapshot


def test_committed_spec_keeps_selector_without_invented_paging():
    spec = json.loads((ROOT / "openapi/sdk/generated/futureagi-sdk.openapi.json").read_text())
    parameters = spec["paths"][ROUTE]["get"]["parameters"]
    assert {p["name"] for p in parameters if p["in"] == "query"} == SELECTORS


def test_python_generated_client_exposes_both_selectors():
    source = ROOT / "python/fi/generated/openapi_client/api/model_hub/model_hub_prompt_labels_template_labels.py"
    tree = ast.parse(source.read_text())
    calls = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
             and node.name in {"sync", "sync_detailed", "asyncio", "asyncio_detailed"}]
    assert len(calls) == 4
    for call in calls:
        names = {arg.arg for arg in call.args.kwonlyargs}
        assert SELECTORS <= names, f"{call.name} omits the template selectors"
