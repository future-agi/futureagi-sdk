"""Platform catalog contract checks against an in-memory HTTP transport."""
from __future__ import annotations

import asyncio
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import re

import httpx
import pytest

from fi import AsyncFutureAGIClient, FutureAGIClient
from fi.errors import (
    AuthenticationError, ConfigurationError, PermissionDeniedError,
    ProductNotAvailableError, RateLimitError, ServerError, UnexpectedRedirectError,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = json.loads((ROOT / "openapi/catalog/models-source.json").read_text())


def make(handler, asynchronous=False):
    cls = AsyncFutureAGIClient if asynchronous else FutureAGIClient
    client = cls("catalog-api", "catalog-secret", base_url="http://localhost:9031",
                 workspace_id="workspace-a", organization_id="org-a", retries=0)
    kwargs = dict(base_url=client.base_url, auth=client._auth, transport=httpx.MockTransport(handler))
    if asynchronous:
        client.generated_client.set_async_httpx_client(httpx.AsyncClient(**kwargs))
    else:
        client.generated_client.set_httpx_client(httpx.Client(**kwargs))
    return client


def invoke(client, asynchronous, **query):
    result = client.models.list(**query)
    return asyncio.run(result) if asynchronous else result


@pytest.mark.parametrize("asynchronous", [False, True])
def test_platform_catalog_uses_declared_read_and_shared_identity(asynchronous):
    seen = []
    def handler(request):
        seen.append(request)
        assert request.method == "GET"
        assert request.url.path == SOURCE["path"]
        assert request.url.host == "localhost"
        assert request.headers["x-api-key"] == "catalog-api"
        assert request.headers["x-secret-key"] == "catalog-secret"
        assert request.headers["x-workspace-id"] == "workspace-a"
        assert request.headers["x-organization-id"] == "org-a"
        assert "authorization" not in request.headers
        assert "idempotency-key" not in request.headers
        assert not request.content
        assert request.extensions["fi.retry"]["class"] == "http-idempotent"
        return httpx.Response(200, json={"count": 1, "next": None, "previous": None,
            "results": [{"model_name": "example/model", "is_available": False, "new_field": 12}]})
    client = make(handler, asynchronous)
    page = invoke(client, asynchronous, search="example model", limit=10,
                  model_type="llm", exclude_providers=["one", "two"])
    assert page.items == [{"model_name": "example/model", "is_available": False, "new_field": 12}]
    assert not page.has_more
    assert seen[0].url.params["search"] == "example model"
    assert seen[0].url.params.get_list("exclude_providers") == ["one", "two"]
    assert len(seen) == 1


@pytest.mark.parametrize("asynchronous", [False, True])
def test_catalog_pagination_keeps_filters_and_never_follows_foreign_links(asynchronous):
    seen = []
    def handler(request):
        seen.append(request)
        number = int(request.url.params["page"])
        assert request.url.host == "localhost"
        assert request.url.path == SOURCE["path"]
        assert request.url.params["search"] == "example"
        assert request.url.params["limit"] == "100"
        return httpx.Response(200, json={"count": 3, "results": [{"id": number}],
            "next": f"https://untrusted.invalid/other?page={number + 1}" if number < 3 else None})
    client = make(handler, asynchronous)
    async def collect():
        return [item async for item in await client.models.list(search="example", limit=100)]
    rows = asyncio.run(collect()) if asynchronous else list(client.models.list(search="example", limit=100))
    assert rows == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert len(seen) == 3


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("status,code,error", [
    (401, "unauthenticated", AuthenticationError),
    (403, "forbidden", PermissionDeniedError),
    (403, "product_not_admitted", PermissionDeniedError),
    (404, "product_not_admitted", ProductNotAvailableError),
    (429, "rate_limited", RateLimitError),
    (500, "server_error", ServerError),
    (302, None, UnexpectedRedirectError),
])
def test_catalog_errors_keep_shared_classes(asynchronous, status, code, error):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(status, json={"code": code}, headers={
            "x-request-id": "catalog-request", "retry-after": "2",
            "location": "https://untrusted.invalid/credentials"})
    with pytest.raises(error):
        invoke(make(handler, asynchronous), asynchronous)
    assert len(calls) == 1


@pytest.mark.parametrize("asynchronous", [False, True])
def test_unknown_catalog_filter_never_reaches_transport(asynchronous):
    client = make(lambda request: pytest.fail("invalid query was sent"), asynchronous)
    with pytest.raises(ConfigurationError):
        invoke(client, asynchronous, organization_id="org-b")


@pytest.mark.parametrize("asynchronous", [False, True])
def test_with_options_keeps_models_on_the_same_client_identity(asynchronous):
    client = make(lambda r: httpx.Response(200, json={"count": 0, "results": [], "next": None}), asynchronous)
    clone = client.with_options(timeout=2)
    assert type(clone.models) is type(client.models)
    assert clone.models._client is clone
    assert clone.models._client is not client
    assert clone.models.list.__doc__


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("total,number,items", [(5, 3, [{"id": 5}]), (6, 3, [{"id": 5}, {"id": 6}]), (0, 1, [])])
def test_last_page_selector_is_terminal_without_a_probe(asynchronous, total, number, items):
    seen = []
    payload = {"count": total, "current_page": number, "results": items, "next": None}
    def handler(request):
        seen.append(request)
        assert len(seen) == 1, "the last-page selector must not probe a phantom page"
        assert request.url.params["page"] == "last"
        assert request.url.params["limit"] == "100"
        assert request.url.params["search"] == "example"
        return httpx.Response(200, json=payload)
    client = make(handler, asynchronous)
    async def collect():
        page = await client.models.list(page="last", limit=100, search="example")
        assert page.raw == payload
        assert not page.has_more
        assert await page.next_page() is None
        return [item async for item in page]
    if asynchronous:
        actual = asyncio.run(collect())
    else:
        page = client.models.list(page="last", limit=100, search="example")
        assert page.raw == payload
        assert not page.has_more
        assert page.next_page() is None
        actual = list(page)
    assert actual == items
    assert len(seen) == 1


@pytest.mark.parametrize("asynchronous", [False, True])
def test_catalog_uses_resolved_page_for_continuation(asynchronous):
    seen = []
    def handler(request):
        seen.append(request.url.params["page"])
        # A server-resolved page takes precedence over the requested number.
        assert seen == ["1"]
        return httpx.Response(200, json={"count": 6, "current_page": 3,
            "results": [{"id": 5}, {"id": 6}], "next": None})
    page = invoke(make(handler, asynchronous), asynchronous, page=1, limit=2)
    assert page.items == [{"id": 5}, {"id": 6}]
    assert not page.has_more
    assert seen == ["1"]


def test_catalog_row_matches_source_and_language_twins():
    rows = json.loads((ROOT / "openapi/catalog/operations.json").read_text())["operations"]
    row, = [r for r in rows if r["id"] == "models.list"]
    assert row["method"] == SOURCE["method"] == "GET"
    assert row["path"] == SOURCE["path"]
    assert row["operation_id"] == SOURCE["operation_id"]
    source_query = SOURCE["overrides"]["query"]
    assert len(source_query) == len(set(source_query))
    assert len(row["query"]) == len(set(row["query"]))
    # Committed producer representation; generic catalog inputs may be permuted.
    assert row["query"] == sorted(source_query)
    assert row["pagination"]["items"] == "results"
    assert row["pagination"]["current_page"] == SOURCE["overrides"]["pagination"]["current_page"]
    assert SOURCE["overrides"]["pagination"]["last_page_selector"] == "last"
    mapping = json.loads((ROOT / "openapi/catalog/read-wrapper-map.json").read_text())["operations"]
    assert mapping[SOURCE["operation_id"]]["methods"][0]["py"] == "client.models.list"
    assert mapping[SOURCE["operation_id"]]["methods"][0]["ts"] == "client.models.list"


# Independent names and Swagger fixture: neither is derived from generated metadata.
DECLARED_QUERY = ["page", "limit", "name", "search", "model_type", "exclude_providers"]
CANONICAL_QUERY = ["exclude_providers", "limit", "model_type", "name", "page", "search"]


def assert_canonical_query(query, source_query):
    """Producer representation, not a restriction on generic catalog input order."""
    assert len(source_query) == len(set(source_query)), "duplicate source query"
    assert len(query) == len(set(query)), "duplicate catalog query"
    assert query == sorted(source_query), "noncanonical or changed query membership"


@pytest.fixture
def model_producer():
    spec = importlib.util.spec_from_file_location("catalog_models", ROOT / "scripts/catalog-models.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def model_swagger():
    return {"swagger": "2.0", "info": {"title": "Fixture", "version": "1"}, "paths": {
        "/model-hub/api/models_list/": {"get": {
            "operationId": "model-hub_api_models_list_list",
            "responses": {"200": {"description": "Model page", "schema": {"$ref": "#/definitions/Page"}}},
        }}}, "definitions": {"Page": {"type": "object", "properties": {
            "count": {"type": "integer"}, "next": {"type": "string"},
            "results": {"type": "array", "items": {"type": "object"}},
        }}}}


@pytest.mark.parametrize("reverse", [False, True])
def test_model_producer_canonicalizes_only_row(model_producer, model_swagger, monkeypatch, reverse):
    assert model_producer.QUERY == DECLARED_QUERY
    original_row, _ = model_producer.operation(model_swagger)
    declaration = list(reversed(DECLARED_QUERY)) if reverse else list(DECLARED_QUERY)
    monkeypatch.setattr(model_producer, "QUERY", declaration)
    row, source = model_producer.operation(model_swagger)
    # Check provenance before the RED-producing assertion; never sort the source.
    assert source["overrides"]["query"] == declaration
    assert model_producer.QUERY == declaration
    assert row["query"] == CANONICAL_QUERY
    assert row == original_row
    assert_canonical_query(row["query"], source["overrides"]["query"])
    monkeypatch.syspath_prepend(str(ROOT / "scripts/platform"))
    from catalog_contracts import reconcile
    from composed_contracts import catalog_source
    catalog = {"operations": [row]}
    assert reconcile(catalog, catalog_source({"paths": {}}, source)) == catalog


def test_model_producer_does_not_hide_duplicates(model_producer, model_swagger, monkeypatch):
    declaration = [*DECLARED_QUERY, "search"]
    monkeypatch.setattr(model_producer, "QUERY", declaration)
    row, source = model_producer.operation(model_swagger)
    assert source["overrides"]["query"] == declaration
    assert row["query"].count("search") == 2
    with pytest.raises(AssertionError, match="duplicate source"):
        assert_canonical_query(row["query"], source["overrides"]["query"])
    with pytest.raises(AssertionError, match="duplicate catalog"):
        assert_canonical_query(row["query"], DECLARED_QUERY)


@pytest.mark.parametrize("query", [
    pytest.param([key for key in CANONICAL_QUERY if key != missing], id=f"missing-{missing}")
    for missing in DECLARED_QUERY
] + [
    pytest.param([*CANONICAL_QUERY, "organization_id"], id="extra-organization"),
    pytest.param([*CANONICAL_QUERY, "search"], id="duplicate-search"),
    pytest.param(["q" if key == "search" else key for key in CANONICAL_QUERY], id="renamed-search"),
    pytest.param(["search" if key == "name" else key for key in CANONICAL_QUERY], id="missing-plus-duplicate"),
    pytest.param(["organization_id" if key == "name" else key for key in CANONICAL_QUERY], id="wrong-member-same-length"),
    pytest.param([*CANONICAL_QUERY[:3], "page", "name", "search"], id="canonical-output-swap"),
])
def test_model_query_projection_rejects_catalog_mutations(query):
    with pytest.raises(AssertionError):
        assert_canonical_query(query, DECLARED_QUERY)


@pytest.mark.parametrize("both", [False, True])
def test_model_query_projection_rejects_source_duplicates(both):
    source_query = [*DECLARED_QUERY, "search"]
    query = sorted(source_query) if both else CANONICAL_QUERY
    with pytest.raises(AssertionError, match="duplicate source"):
        assert_canonical_query(query, source_query)


def test_model_language_twins_exactly_project_catalog_query():
    from fi.generated.platform.catalog.models import MODELS_LIST
    rows = json.loads((ROOT / "openapi/catalog/operations.json").read_text())["operations"]
    row, = [r for r in rows if r["id"] == "models.list"]
    text = (ROOT / "typescript/futureagi/src/generated/catalog/models.ts").read_text()
    declaration, = re.findall(r"^const MODELS_LIST: CatalogOperation = (.+);$", text, re.MULTILINE)
    assert list(MODELS_LIST[0].query) == row["query"] == json.loads(declaration)["query"]


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("declaration", [DECLARED_QUERY, DECLARED_QUERY[::-1], CANONICAL_QUERY])
def test_model_wire_query_ignores_declaration_and_caller_order(monkeypatch, asynchronous, declaration):
    from fi.generated.platform.catalog import models
    spec, unwrap, pagination = models.MODELS_LIST
    monkeypatch.setattr(models, "MODELS_LIST", (replace(spec, query=tuple(declaration)), unwrap, pagination))
    seen = []
    def handler(request):
        seen.append(request.url.query.decode())
        return httpx.Response(200, json={"count": 0, "results": [], "next": None})
    client = make(handler, asynchronous)
    for values in (["z", "a"], ["a", "z"]):
        pairs = [("page", 2), ("limit", 3), ("name", "n"), ("search", "a b"),
                 ("model_type", "llm"), ("exclude_providers", values)]
        expected = (f"exclude_providers={values[0]}&exclude_providers={values[1]}"
                    "&limit=3&model_type=llm&name=n&page=2&search=a+b")
        for caller in (pairs, pairs[::-1]):
            invoke(client, asynchronous, **dict(caller))
            assert seen[-1] == expected
    assert len(seen) == 4
    with pytest.raises(ConfigurationError):
        invoke(client, asynchronous, organization_id="org-b")
    assert len(seen) == 4


@pytest.mark.parametrize("asynchronous", [False, True])
def test_model_missing_nonpaging_declaration_rejects_before_transport(monkeypatch, asynchronous):
    from fi.generated.platform.catalog import models
    spec, unwrap, pagination = models.MODELS_LIST
    monkeypatch.setattr(models, "MODELS_LIST", (
        replace(spec, query=tuple(key for key in spec.query if key != "search")), unwrap, pagination))
    client = make(lambda request: pytest.fail("undeclared filter was sent"), asynchronous)
    with pytest.raises(ConfigurationError):
        invoke(client, asynchronous, search="a b")


def test_model_source_refresh_fails_closed_on_contract_drift():
    spec = importlib.util.spec_from_file_location("catalog_models", ROOT / "scripts/catalog-models.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(ValueError, match="exactly one"):
        module.operation({"paths": {}})
    with pytest.raises(ValueError, match="pagination contract"):
        module.operation({"paths": {SOURCE["path"]: {"get": {
            "operationId": SOURCE["operation_id"], "responses": {"200": {"schema": {"properties": {}}}}
        }}}})
