"""Each paginated catalog operation is exercised through its registered public facade."""
import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest

from ._contract_runtime import Runtime, path_args, resolve
from ._gates_support import REPO

DATA = json.loads((REPO / "tests/fixtures/contracts/operations.json").read_text())
PUBLIC = [(row, mode) for mode in ("sync", "async") for row in DATA["operations"]
          if row["adapter"] == "catalog" and row["catalog"]["pagination"]
          and row["id"] in DATA["public_cases"]["py_" + mode]]
PUBLIC_IDS = [mode + ":" + row["id"] for row, mode in PUBLIC]


def put(target, path, value):
    parts = path.split(".")
    for key in parts[:-1]:
        target = target.setdefault(key, {})
    target[parts[-1]] = value


async def check_pages(row, mode, mutation=None):
    descriptor = row["catalog"]
    page = descriptor["pagination"]
    requests = []
    def handler(request):
        requests.append(request)
        number = int(request.url.params[page["page_param"]])
        raw = {"count": 2, "previous": None, "total_pages": 2, "current_page": number}
        put(raw, page["items"], [{"n": number}])
        if page.get("total_items"):
            put(raw, page["total_items"], 2)
        if page.get("next"):
            put(raw, page["next"], "http://127.0.0.1:9/ignored?page=2" if number == 1 else None)
        wire = {descriptor["unwrap"]: raw} if descriptor["unwrap"] else raw
        return httpx.Response(200, json=wire)
    subject = Runtime(row, mode, handler)
    try:
        first = await resolve(subject.call())
        if mutation:
            # Keep raw intact: the former raw-only assertion accepted these defects.
            first = SimpleNamespace(raw=first.raw, items=[] if mutation == "items" else first.items,
                                    has_more=False if mutation == "continuation" else first.has_more,
                                    next_cursor=first.next_cursor, next_page=first.next_page)
        assert first.items == [{"n": 1}]
        assert first.has_more and first.next_cursor == "2"
        second = await resolve(first.next_page())
        assert second.items == [{"n": 2}]
        assert not second.has_more and second.next_cursor is None
        assert await resolve(second.next_page()) is None
        assert len(requests) == 2
        assert requests[0].method == requests[1].method == row["method"]
        expected_path = row["path"]
        for name, value in path_args(row).items():
            expected_path = expected_path.replace("{" + name + "}", value)
        assert requests[0].url.path == requests[1].url.path == expected_path
        assert requests[1].url.params[page["page_param"]] == "2"
        assert {k: v for k, v in requests[0].url.params.items() if k != page["page_param"]} == {
            k: v for k, v in requests[1].url.params.items() if k != page["page_param"]}
    finally:
        await subject.close()


@pytest.mark.parametrize("row,mode", PUBLIC, ids=PUBLIC_IDS)
def test_public_operation_walks_two_pages(row, mode):
    asyncio.run(check_pages(row, mode))


@pytest.mark.parametrize("row,mode", PUBLIC, ids=PUBLIC_IDS)
@pytest.mark.parametrize("mutation", ["items", "continuation"])
def test_broken_public_page_with_intact_raw_is_rejected(row, mode, mutation):
    with pytest.raises(AssertionError):
        asyncio.run(check_pages(row, mode, mutation))
