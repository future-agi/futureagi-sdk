"""Every admitted management operation has a real public contract case."""
import asyncio
import json

import pytest

from ._contract_runtime import Runtime
from ._gates_support import REPO


def test_management_inventory_covers_every_admitted_operation():
    data = json.loads((REPO / "tests/fixtures/contracts/operations.json").read_text())
    surface = json.loads((REPO / "openapi/fa-mgmt/surface.json").read_text())
    expected = {row["operation_id"] for row in surface["operations"]}
    rows = [row for row in data["operations"] if row["adapter"] == "management"]
    assert len(expected) == len(rows) == 19
    assert {row["operation_id"] for row in rows} == expected
    assert "management" not in data["modules"]
    for mode in ("py_sync", "py_async", "ts"):
        assert {row["id"] for row in rows} <= set(data["public_cases"][mode])
        assert not ({row["id"] for row in rows} & {row["id"] for row in data["not_offered"][mode]})


SURFACE = json.loads((REPO / "openapi/fa-mgmt/surface.json").read_text())["operations"]


@pytest.mark.parametrize("operation", SURFACE, ids=lambda op: op["name"])
@pytest.mark.parametrize("mode", ["sync", "async"])
def test_each_management_method_is_required_before_transport(monkeypatch, operation, mode):
    data = json.loads((REPO / "tests/fixtures/contracts/operations.json").read_text())
    row = next(row for row in data["operations"] if row["adapter"] == "management" and row["name"] == operation["name"])
    async def run():
        requests = []
        subject = Runtime(row, mode, lambda request: requests.append(request) or pytest.fail("missing method must not request"))
        try:
            parts = row["wrapper"]["py"].split(".")[1:]
            owner = subject.client
            for part in parts[:-1]:
                owner = getattr(owner, part)
            assert callable(getattr(owner, parts[-1]))
            monkeypatch.delattr(type(owner), parts[-1])
            with pytest.raises(AttributeError, match=parts[-1]):
                await subject.call()
            assert requests == []
            assert subject.setup_requests == []
        finally:
            await subject.close()
    asyncio.run(run())
