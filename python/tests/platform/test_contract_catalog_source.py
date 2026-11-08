"""Catalog expectations follow certified source identities, never runtime tables."""
import copy
import json

import pytest

from ._gates_support import REPO, load


def tooling(monkeypatch):
    monkeypatch.syspath_prepend(str(REPO / "scripts/platform"))
    return load("catalog_contract_source", "scripts/platform/catalog_contracts.py")


def inputs():
    catalog = {"operations": [{"id": "dashboards.list", "public": "tracing.dashboards.list",
        "operation_id": "listDashboards", "method": "GET", "path": "/tracer/dashboard/",
        "query": [], "path_params": [], "unwrap": None, "pagination": None}]}
    swagger = {"swagger": "2.0", "paths": {"/tracer/dashboard/": {"get": {
        "operationId": "listDashboards", "parameters": [], "responses": {
            "200": {"schema": {"$ref": "#/definitions/Dashboard"}}}}}},
        "definitions": {"Dashboard": {"type": "object", "properties": {"name": {"type": "string"}}}}}
    return catalog, swagger


def test_incoming_catalog_method_path_and_query_are_reconciled(monkeypatch):
    module = tooling(monkeypatch)
    catalog, swagger = inputs()
    old = module.project(swagger, catalog)
    candidate = copy.deepcopy(swagger)
    operation = candidate["paths"].pop("/tracer/dashboard/")["get"]
    operation["parameters"] = [{"in": "query", "name": "search", "type": "string"}]
    candidate["paths"]["/tracer/dashboards/"] = {"post": operation}
    source = module.project(candidate, catalog)
    updated = module.reconcile(catalog, source)
    assert updated["operations"][0]["method"] == "POST"
    assert updated["operations"][0]["path"] == "/tracer/dashboards/"
    assert updated["operations"][0]["query"] == ["search"]
    drift = module.drift(old, source, catalog)
    assert drift["tracing"]["verdict"] == "NOT-EVALUATED"
    assert drift["tracing"]["changed"] == ["tracing.dashboards.list"]
    assert module.drift(source, source, updated) == {}


def test_catalog_schema_drift_and_removed_identity_are_not_hidden(monkeypatch):
    module = tooling(monkeypatch)
    catalog, swagger = inputs()
    old = module.project(swagger, catalog)
    swagger["definitions"]["Dashboard"]["properties"]["name"]["type"] = "integer"
    new = module.project(swagger, catalog)
    assert module.drift(old, new, catalog)["tracing"]["changed"]
    swagger["paths"] = {}
    removed = module.project(swagger, catalog)
    assert module.drift(old, removed, catalog)["tracing"]["removed"] == ["tracing.dashboards.list"]
    with pytest.raises(ValueError, match="missing catalog operation"):
        module.reconcile(catalog, removed)


def test_duplicate_catalog_source_identities_are_refused(monkeypatch):
    module = tooling(monkeypatch)
    catalog, swagger = inputs()
    swagger["paths"]["/duplicate/"] = copy.deepcopy(swagger["paths"]["/tracer/dashboard/"])
    with pytest.raises(ValueError, match="duplicate operation"):
        module.project(swagger, catalog)


def test_case_generation_rejects_self_consistent_stale_catalog_metadata(monkeypatch, tmp_path):
    module = tooling(monkeypatch)
    generator = load("independent_catalog_cases", "scripts/platform/contract_cases.py")
    catalog, swagger = inputs()
    source = module.project(swagger, catalog)
    catalog["operations"][0]["method"] = "DELETE"
    with pytest.raises(ValueError, match="catalog metadata drift"):
        generator.catalog_cases(catalog, source)


def test_unrelated_duplicate_identities_do_not_block_catalog_projection(monkeypatch):
    module = tooling(monkeypatch)
    catalog, swagger = inputs()
    for path in ("/unrelated/one", "/unrelated/two"):
        swagger["paths"][path] = {"get": {"operationId": "unrelated"}}
    assert set(module.project(swagger, catalog)["paths"]) == {"/tracer/dashboard/"}


MODEL_QUERY = ["page", "limit", "name", "search", "model_type", "exclude_providers"]
MODEL_CANONICAL = ["exclude_providers", "limit", "model_type", "name", "page", "search"]


def model_inputs(monkeypatch, query):
    tooling(monkeypatch)
    from composed_contracts import catalog_source
    row = {"id": "models.list", "public": "models.list", "operation_id": "model-hub_api_models_list_list",
           "method": "GET", "path": "/model-hub/api/models_list/", "query": list(MODEL_CANONICAL),
           "path_params": [], "unwrap": None, "pagination": None}
    models = {"path": row["path"], "method": "GET", "operation_id": row["operation_id"],
              "response_schema": {"type": "object", "properties": {}}, "overrides": {"query": list(query)}}
    return {"operations": [row]}, catalog_source({"paths": {}}, models)


@pytest.mark.parametrize("source_query", [MODEL_QUERY, MODEL_QUERY[::-1]])
@pytest.mark.parametrize("catalog_query", [MODEL_QUERY, MODEL_QUERY[::-1], MODEL_CANONICAL])
def test_model_cases_accept_unique_permutations(monkeypatch, source_query, catalog_query):
    module = tooling(monkeypatch)
    generator = load("independent_model_cases", "scripts/platform/contract_cases.py")
    catalog, source = model_inputs(monkeypatch, source_query)
    catalog["operations"][0]["query"] = list(catalog_query)
    assert module.reconcile(catalog, source)["operations"][0]["query"] == MODEL_CANONICAL
    cases = generator.catalog_cases(catalog, source)
    assert len(cases) == 1
    assert cases[0]["catalog"]["query"] == catalog_query


@pytest.mark.parametrize("query", [
    pytest.param([key for key in MODEL_CANONICAL if key != missing], id=f"missing-{missing}")
    for missing in MODEL_QUERY
] + [
    pytest.param([*MODEL_CANONICAL, "organization_id"], id="extra-organization"),
    pytest.param([*MODEL_CANONICAL, "search"], id="duplicate-search"),
    pytest.param(["q" if key == "search" else key for key in MODEL_CANONICAL], id="renamed-search"),
    pytest.param(["search" if key == "name" else key for key in MODEL_CANONICAL], id="missing-plus-duplicate"),
    pytest.param(["organization_id" if key == "name" else key for key in MODEL_CANONICAL], id="wrong-member-same-length"),
])
def test_model_cases_reject_membership_drift(monkeypatch, query):
    catalog, source = model_inputs(monkeypatch, MODEL_QUERY)
    catalog["operations"][0]["query"] = query
    generator = load("independent_model_drift", "scripts/platform/contract_cases.py")
    with pytest.raises(ValueError, match="catalog metadata drift"):
        generator.catalog_cases(catalog, source)


def test_source_projection_keeps_only_reachable_definitions(monkeypatch):
    module = tooling(monkeypatch)
    catalog, swagger = inputs()
    swagger["definitions"]["Unused"] = {"type": "integer"}
    assert set(module.project(swagger, catalog)["definitions"]) == {"Dashboard"}
