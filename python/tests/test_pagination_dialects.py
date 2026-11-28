"""Pagination claims must be grounded in the pinned FA implementation, not Swagger defaults."""
import ast
import asyncio
import httpx
import pytest
from fi import FutureAGIClient, AsyncFutureAGIClient
from fi.errors import BadRequestError
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGING = {"page", "limit", "page_size", "page_number", "offset", "cursor", "cursor_mode", "page_token", "current_page", "current_page_index"}
SPECS = ["openapi/sdk/generated/futureagi-sdk.openapi.json", "openapi/catalog/source.json",
         "openapi/catalog/models-source.json", "openapi/tracing/source.json", "openapi/connectors/fa.json",
         "openapi/fa-mgmt/swagger.json"]


@pytest.mark.parametrize("asynchronous", [False, True])
def test_wrong_paging_dialect_reaches_server_unchanged(asynchronous):
    seen = []
    def handler(request):
        seen.append(dict(request.url.params))
        return httpx.Response(400, json={"page": ["Unknown field."]})
    cls = AsyncFutureAGIClient if asynchronous else FutureAGIClient
    client = cls("fixture-api", "fixture-secret", base_url="http://localhost:9012", retries=0)
    transport = httpx.MockTransport(handler)
    if asynchronous:
        async def run():
            async with httpx.AsyncClient(base_url=client.base_url, transport=transport) as http:
                client.generated_client.set_async_httpx_client(http)
                with pytest.raises(BadRequestError):
                    await client.tracing.spans(page=1)
        asyncio.run(run())
    else:
        with httpx.Client(base_url=client.base_url, transport=transport) as http:
            client.generated_client.set_httpx_client(http)
            with pytest.raises(BadRequestError):
                client.tracing.spans(page=1)
    assert seen == [{"page": "1"}], "Do not translate 1-based page to 0-based page_number"


def test_generated_facade_preserves_undeclared_paging_kwargs():
    seen = []
    def handler(request):
        seen.append(dict(request.url.params))
        return httpx.Response(400, json={"page_size": ["Unknown field."]})
    client = FutureAGIClient("fixture-api", "fixture-secret", base_url="http://localhost:9012", retries=0)
    with httpx.Client(base_url=client.base_url, transport=httpx.MockTransport(handler)) as http:
        client.generated_client.set_httpx_client(http)
        with pytest.raises(BadRequestError):
            client.annotation_queues.items.list("queue", page_size=4)
    assert seen == [{"page_size": "4"}]


def test_alert_details_preserves_zero_based_nested_log_paging():
    seen = []
    def handler(request):
        seen.append(dict(request.url.params))
        return httpx.Response(200, json={"status": True, "result": {"logs": {"results": []}}})
    client = FutureAGIClient("fixture-api", "fixture-secret", base_url="http://localhost:9012", retries=0)
    with httpx.Client(base_url=client.base_url, transport=httpx.MockTransport(handler)) as http:
        client.generated_client.set_httpx_client(http)
        client.alerts.details("alert", page_number=0, page_size=2)
    assert seen == [{"page_number": "0", "page_size": "2"}]


def table():
    path = ROOT / "openapi/sdk/pagination-dialects.json"
    assert path.exists(), "Missing FA-evidenced per-operation pagination table"
    return json.loads(path.read_text())


def functions(path):
    result = {}
    def walk(node, prefix=""):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                name = prefix + child.name
                if not isinstance(child, ast.ClassDef):
                    result[name] = child
                walk(child, name + ".")
    walk(ast.parse(path.read_text()))
    return result


def test_no_mixed_pagination_dialects():
    for spec in SPECS:
        for path, item in json.loads((ROOT / spec).read_text()).get("paths", {}).items():
            for method, op in item.items():
                if method not in {"get", "post"}:
                    continue
                names = {p.get("name") for p in item.get("parameters", []) + op.get("parameters", []) if p.get("in") == "query"}
                # FA AnnotationQueuePagination explicitly supports page_size as an alias.
                if path not in {"/model-hub/annotation-queues/", "/simulate/agent-definitions/{agent_id}/versions/{version_id}/call-executions/"}:
                    assert not ({"limit", "page_size"} <= names), f"{spec}: {method} {path} declares both pagination dialects"


def test_table_evidence_and_declared_parameters():
    data = table()
    assert re.fullmatch(r"[a-f0-9]{40}", data["fa_head"])
    rows = {(r["method"].lower(), r["path"]): r for r in data["operations"]}
    assert len(rows) == len(data["operations"]), "Duplicate endpoint evidence"
    for row in rows.values():
        assert row["evidence"] and all(re.fullmatch(r"[^:]+\.py:\d+(?:-\d+)?", e) for e in row["evidence"])
        assert row["documentation"].startswith("Pagination:")
        for language in ("python", "typescript"):
            assert row["methods"][language] or row.get("not_offered", {}).get(language), f"Missing {language} inventory or absence evidence: {row['path']}"
        for name in row["accepted"]:
            assert name in row["documentation"]
        for name, base in row["bases"].items():
            assert name in row["accepted"] and base in (0, 1)
            assert f"{base}-based" in row["documentation"]
    for spec in SPECS:
        for path, item in json.loads((ROOT / spec).read_text()).get("paths", {}).items():
            for method, op in item.items():
                if method not in {"get", "post"}:
                    continue
                declared = {p.get("name") for p in item.get("parameters", []) + op.get("parameters", []) if p.get("in") == "query"} & PAGING
                if declared:
                    assert (method, path) in rows, f"Uninventoried paged endpoint: {method} {path}"
                    assert declared <= set(rows[method, path]["accepted"]), f"{spec}: {method} {path}: {declared}"


@pytest.mark.parametrize("path,accepted,bases", [
    ("/model-hub/eval-templates/{template_id}/feedback-list/", {"page", "page_size"}, {"page": 0}),
    ("/tracer/trace-session/{id}/eval_logs/", {"page", "page_size"}, {"page": 0}),
    ("/tracer/user-alerts/{id}/details/", {"page_number", "page_size"}, {"page_number": 0}),
])
def test_lists_without_swagger_paging_are_inventoried(path, accepted, bases):
    rows = {row["path"]: row for row in table()["operations"] if row["method"] == "GET"}
    assert path in rows, f"Missing source-paginated endpoint omitted by Swagger: {path}"
    assert set(rows[path]["accepted"]) == accepted
    assert rows[path]["bases"] == bases
    assert set(rows[path]["upstream_missing_query_parameters"]) == accepted


def test_python_documented_dialects_match_table():
    cache = {}
    for row in table()["operations"]:
        for ref in row["methods"]["python"]:
            if ref["file"] not in cache:
                cache[ref["file"]] = functions(ROOT / ref["file"])
            node = cache[ref["file"]][ref["symbol"]]
            assert row["documentation"] in " ".join((ast.get_docstring(node) or "").split()), f"{ref}: missing {row['documentation']}"
            args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            declared = {a.arg for a in args} & PAGING
            assert declared <= set(row["accepted"]), f"{ref}: unsupported typed paging parameters {declared}"
