"""The management pagination adapter preserves the complete DRF envelope and follows only page numbers."""
import asyncio
import json

import httpx
import pytest

from fi._core.catalog import AsyncResource, Resource
from fi._core.policy import OperationSpec
from ._contract_runtime import Runtime, resolve
from ._gates_support import REPO

ROWS = json.loads((REPO / "tests/fixtures/contracts/operations.json").read_text())["operations"]


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_drf_pages_preserve_fields_and_do_not_follow_foreign_origins(mode):
    async def run():
        row = next(r for r in ROWS if r["adapter"] == "catalog" and r["method"] == "GET")
        requests = []
        def handler(request):
            requests.append(request)
            page = int(request.url.params["page"])
            return httpx.Response(200, json={"status": True, "result": {
                "count": 2, "next": "http://foreign.invalid/ignored?page=2" if page == 1 else None,
                "previous": None if page == 1 else "?page=1", "results": [{"page": page}],
                "total_pages": 2, "current_page": page}})
        runtime = Runtime(row, mode, handler)
        # The adapter is contract-driven. This is the standard DRF descriptor;
        # resource-specific descriptors are exercised by the generated cases.
        operation = (OperationSpec(name=row["name"], family=row["namespace"], method="GET",
                                  path=row["path"], path_params=tuple(row["path_params"]), query=("page", "page_size")),
                     "result", {"page_param": "page", "size_param": "page_size", "first_page": 1,
                                "items": "results", "next": "next", "total_items": "count"})
        resource = (AsyncResource if mode == "async" else Resource)(runtime.client)
        try:
            first = await resolve(resource._call(operation, path={p: "fixture" for p in row["path_params"]}, query={}, body=None))
            assert first.items == [{"page": 1}] and first.has_more
            assert first.raw == {"count": 2, "next": "http://foreign.invalid/ignored?page=2", "previous": None,
                                 "results": [{"page": 1}], "total_pages": 2, "current_page": 1}
            second = await resolve(first.next_page())
            assert second.raw == {"count": 2, "next": None, "previous": "?page=1",
                                  "results": [{"page": 2}], "total_pages": 2, "current_page": 2}
            assert not second.has_more and await resolve(second.next_page()) is None
            assert len(requests) == 2
            assert all(r.url.host == "127.0.0.1" for r in requests)
            assert requests[0].url.path == requests[1].url.path
        finally:
            await runtime.close()
    asyncio.run(run())
