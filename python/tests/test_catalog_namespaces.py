"""Contract smoke for each admitted public catalog operation, with no network.

Adapted from the catalog SDK's all-operations and dashboard lifecycle suites;
these smoke tests are not evidence of backend feature acceptance.
"""
import asyncio
import importlib
import json
from pathlib import Path

import httpx
import pytest

from fi import AsyncFutureAGIClient, FutureAGIClient
from fi.errors import BadRequestError, ConfigurationError, NotFoundError, UnexpectedRedirectError

ROOT = Path(__file__).resolve().parents[2]
ROWS = json.loads((ROOT / "openapi/catalog/operations.json").read_text())["operations"]


def make(handler, async_=False, **selectors):
    cls = AsyncFutureAGIClient if async_ else FutureAGIClient
    selectors = {"workspace_id": "workspace-fixture", "organization_id": "organization-fixture", **selectors}
    client = cls("fixture-api", "fixture-secret", base_url="http://localhost:9012", retries=0, **selectors)
    transport = httpx.MockTransport(handler)
    if async_:
        client.generated_client.set_async_httpx_client(httpx.AsyncClient(
            transport=transport, base_url=client.base_url, auth=client._auth))
    else:
        client.generated_client.set_httpx_client(httpx.Client(
            transport=transport, base_url=client.base_url, auth=client._auth))
    return client


def method(client, row):
    target = client
    for part in row["public"].split("."):
        target = getattr(target, part)
    return target


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row["public"])
@pytest.mark.parametrize("async_", [False, True])
def test_every_admitted_operation(row, async_):
    seen = []
    def handler(request):
        seen.append(request)
        assert request.headers["x-api-key"] == "fixture-api"
        assert request.headers["x-secret-key"] == "fixture-secret"
        assert request.headers["x-workspace-id"] == "workspace-fixture"
        assert request.headers["x-organization-id"] == "organization-fixture"
        assert request.url.host == "localhost"
        payload = {"id": "answer"}
        if row["pagination"]:
            payload = {"table": [], "results": [], "metadata": {"total_rows": 0}, "next": None}
        return httpx.Response(200, json={"result": payload} if row["unwrap"] else payload)
    client = make(handler, async_)
    kwargs = {p: "sample" for p in row["path_params"]}
    if row["method"] in ("POST", "PUT", "PATCH"):
        kwargs["body"] = {"name": "smoke"}
    result = method(client, row)(**kwargs)
    if async_:
        result = asyncio.run(result)
    assert len(seen) == 1
    assert seen[0].method == row["method"]
    expected = row["path"]
    for p in row["path_params"]:
        expected = expected.replace("{" + p + "}", "sample")
    assert seen[0].url.path == expected
    if "body" in kwargs:
        assert json.loads(seen[0].content) == kwargs["body"]
    if not row["pagination"]:
        assert result == {"id": "answer"}


@pytest.mark.parametrize("async_", [False, True])
@pytest.mark.parametrize("kind", ["widgets", "optimizations"])
def test_pagination_walk_stays_on_declared_origin(async_, kind):
    seen = []
    def handler(request):
        seen.append(request)
        page = int(request.url.params["page"])
        assert request.url.host == "localhost"
        if kind == "widgets":
            return httpx.Response(200, json={"results": [{"id": page}],
                "next": "https://untrusted.invalid/steal?page=2" if page == 1 else None})
        return httpx.Response(200, json={"status": "success", "result": {
            "table": [{"id": page}], "metadata": {"total_rows": 2}}})
    client = make(handler, async_)
    page = client.tracing.dashboards.widgets.list("dashboard", limit=1) if kind == "widgets" else client.optimizations.list(limit=1)
    async def collect():
        return [item async for item in await page]
    rows = asyncio.run(collect()) if async_ else list(page)
    assert rows == [{"id": 1}, {"id": 2}]
    assert len(seen) == 2


@pytest.mark.parametrize("async_", [False, True])
@pytest.mark.parametrize("status,error", [(404, NotFoundError), (302, UnexpectedRedirectError)])
def test_shared_typed_errors_and_redirect_guard(async_, status, error):
    client = make(lambda r: httpx.Response(status, json={"detail": "no"}, headers={"location": "https://untrusted.invalid"}), async_)
    with pytest.raises(error):
        result = client.workspaces.list()
        if async_:
            asyncio.run(result)


def test_no_path_traversal_or_undeclared_query():
    client = make(lambda r: pytest.fail("invalid parameters must not reach transport"))
    with pytest.raises(ConfigurationError):
        client.workspaces.get("..")
    with pytest.raises(ConfigurationError):
        client.workspaces.list(unknown=True)


@pytest.mark.parametrize("async_", [False, True])
def test_invalid_page_is_not_silently_empty(async_):
    from fi.errors import FutureAGIAPIError
    client = make(lambda r: httpx.Response(200, json={"result": {"unexpected": []}}), async_)
    with pytest.raises(FutureAGIAPIError) as error:
        page = client.optimizations.list()
        if async_:
            asyncio.run(page)
    assert error.value.code == "invalid_page"


@pytest.mark.parametrize("async_", [False, True])
def test_server_capped_page_size_does_not_skip_items(async_):
    seen = []
    def handler(request):
        page = int(request.url.params["page"])
        seen.append(page)
        rows = [{"id": 1}, {"id": 2}] if page == 1 else [{"id": 3}, {"id": 4}] if page == 2 else [{"id": 5}]
        return httpx.Response(200, json={"result": {"table": rows, "metadata": {"total_rows": 5}}})
    page = make(handler, async_).optimizations.list(limit=1000)
    async def collect():
        return [row["id"] async for row in await page]
    assert (asyncio.run(collect()) if async_ else [row["id"] for row in page]) == [1, 2, 3, 4, 5]
    assert seen == [1, 2, 3]


@pytest.mark.parametrize("async_", [False, True])
@pytest.mark.parametrize("start,total", [(2, 6), (2, 5), (3, 6)])
def test_resumed_server_capped_page_size_does_not_skip_items(async_, start, total):
    seen = []
    def handler(request):
        page = int(request.url.params["page"])
        size = min(int(request.url.params["limit"]), 2)
        seen.append((page, size))
        assert page <= 3, "must not request a phantom page"
        rows = [{"id": i} for i in range(1, total + 1)][(page - 1) * size:page * size]
        return httpx.Response(200, json={"result": {"table": rows, "metadata": {"total_rows": total}}})
    page = make(handler, async_).optimizations.list(page=start, limit=1000)
    async def collect():
        first = await page
        assert first.has_more == (start < 3)
        return [row["id"] async for row in first]
    if async_:
        actual = asyncio.run(collect())
    else:
        assert page.has_more == (start < 3)
        actual = [row["id"] for row in page]
    assert actual == list(range((start - 1) * 2 + 1, total + 1))
    assert seen == [(number, 2) for number in range(start, 4)]


@pytest.mark.parametrize("async_", [False, True])
def test_resume_on_short_last_page_never_changes_wire_limit(async_):
    seen = []
    def handler(request):
        page = int(request.url.params["page"])
        assert request.url.params["limit"] == "1000"
        seen.append(page)
        assert page <= 4
        rows = [{"id": 5}] if page == 3 else []
        return httpx.Response(200, json={"result": {"table": rows, "metadata": {"total_rows": 5}}})
    page = make(handler, async_).optimizations.list(page=3, limit=1000)
    async def collect():
        return [row async for row in await page]
    assert (asyncio.run(collect()) if async_ else list(page)) == [{"id": 5}]
    # Without effective-size metadata a short resumed page needs an empty probe;
    # the wire limit remains unchanged so that probe cannot repeat earlier rows.
    assert seen == [3, 4]


def test_short_last_page_keeps_original_page_size_and_raw():
    seen = []
    def handler(request):
        page = int(request.url.params["page"])
        seen.append(page)
        if page > 2:
            pytest.fail("a short final page must not fetch a phantom page")
        rows = [{"id": 1}, {"id": 2}] if page == 1 else [{"id": 3}]
        return httpx.Response(200, json={"result": {"table": rows, "metadata": {"total_rows": 3}}})
    page = make(handler).optimizations.list()
    assert page.raw["metadata"]["total_rows"] == 3
    assert list(page) == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert seen == [1, 2]


@pytest.mark.parametrize("async_", [False, True])
def test_option_copies_rebind_namespaces_without_mutating_parent(async_):
    client = make(lambda r: httpx.Response(200, json={}), async_)
    clone = client.with_options(timeout=2)
    assert clone.workspaces._client is clone
    assert clone.tracing.dashboards._client is clone
    assert client.workspaces._client is client
    assert client.tracing.dashboards._client is client


def test_dashboard_lifecycle():
    calls = []
    def handler(request):
        calls.append(request)
        if request.method == "DELETE":
            return httpx.Response(204)
        return httpx.Response(200, json={"id": "d1", "name": "changed"})
    client = make(handler)
    dashboards = client.tracing.dashboards
    assert dashboards.create({"name": "initial"})["id"] == "d1"
    assert dashboards.get("d1")["id"] == "d1"
    assert dashboards.update("d1", {"name": "changed"})["name"] == "changed"
    assert dashboards.delete("d1") is None
    assert [r.method for r in calls] == ["POST", "GET", "PATCH", "DELETE"]


@pytest.mark.parametrize("async_", [False, True])
@pytest.mark.parametrize("name,header", [("FI_WORKSPACE_ID", "x-workspace-id"),
                                         ("FI_ORGANIZATION_ID", "x-organization-id")])
def test_an_empty_selector_variable_sends_no_selector(monkeypatch, async_, name, header):
    monkeypatch.setenv(name, "")
    seen = []
    client = make(lambda r: (seen.append(r), httpx.Response(200, json={"id": "answer"}))[1], async_,
                  workspace_id=None, organization_id=None)
    result = client.workspaces.list()
    if async_:
        asyncio.run(result)
    assert header not in seen[0].headers


def _resumed_walk(async_, answer):
    """Resume on page 3 of a 5-row table with limit 2; *answer* decides each page."""
    seen = []
    def handler(request):
        page = int(request.url.params["page"])
        seen.append(page)
        return answer(page)
    page = make(handler, async_).optimizations.list(page=3, limit=2)
    async def collect():
        return [row async for row in await page]
    return (asyncio.run(collect()) if async_ else list(page)), seen


def _rows(page, total=5, size=2):
    rows = [{"id": i} for i in range(1, total + 1)][(page - 1) * size:page * size]
    return httpx.Response(200, json={"result": {"table": rows, "metadata": {"total_rows": total}}})


@pytest.mark.parametrize("async_", [False, True])
@pytest.mark.parametrize("status", [400, 404])
def test_an_out_of_range_probe_after_a_short_resumed_page_ends_the_walk(async_, status):
    # A page shorter than the limit may be the last one or a server-capped one, so the walk
    # asks for the next page. FA's dataset optimization list answers a page past the end
    # with 400 (its list view turns the paginator's not-found into a bad request); a plain
    # paginated view answers 404. Either ends the walk after that one probe.
    def answer(page):
        if page == 4:
            return httpx.Response(status, json={"detail": "Invalid page."})
        return _rows(page)
    rows, seen = _resumed_walk(async_, answer)
    assert rows == [{"id": 5}]
    assert seen == [3, 4]


@pytest.mark.parametrize("async_", [False, True])
@pytest.mark.parametrize("status,error", [(400, BadRequestError), (404, NotFoundError)])
def test_an_error_on_a_counted_page_still_raises(async_, status, error):
    # A full first page (2 rows of the 2 asked) makes page 2 certain, so its error is real.
    seen = []
    def handler(request):
        page = int(request.url.params["page"])
        seen.append(page)
        return _rows(page) if page == 1 else httpx.Response(status, json={"detail": "no"})
    page = make(handler, async_).optimizations.list(limit=2)
    async def collect():
        return [row async for row in await page]
    with pytest.raises(error):
        asyncio.run(collect()) if async_ else list(page)
    assert seen == [1, 2]


@pytest.mark.parametrize("async_", [False, True])
def test_a_probe_that_finds_rows_continues_the_walk(async_):
    # The short resumed page was server-capped: the probe page has rows and the walk goes on.
    def answer(page):
        rows = [{"id": i} for i in range(1, 8)][page - 1:page]
        return httpx.Response(200, json={"result": {"table": rows, "metadata": {"total_rows": 7}}})
    rows, seen = _resumed_walk(async_, answer)
    assert rows == [{"id": 3}, {"id": 4}, {"id": 5}, {"id": 6}, {"id": 7}]
    assert seen == [3, 4, 5, 6, 7]
