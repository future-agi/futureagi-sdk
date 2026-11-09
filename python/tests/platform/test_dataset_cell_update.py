"""Cell updates must never turn an omitted replacement into a destructive write."""

from __future__ import annotations

import asyncio
import copy
import json

import httpx
import pytest

import fi.platform as fp


BASE = "https://sdk.invalid"
DATASET_ID = "dataset-1"
CELL = {"row_id": "row-1", "column_id": "column-1"}
MISSING_VALUES = [
    {},
    {"new_value": fp.NOT_GIVEN},
    {"new_value": "replacement", "extra_body": {"new_value": fp.NOT_GIVEN}},
]
MISSING_IDS = ["omitted", "not-given", "not-given-body-override"]


def _handler(seen):
    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200, json={"status": True, "result": "Cell value updated successfully"}
        )

    return handle


@pytest.fixture
def client():
    seen = []
    with httpx.Client(transport=httpx.MockTransport(_handler(seen))) as http:
        with fp.Client(
            api_key="k", secret_key="s", base_url=BASE, http_client=http
        ) as sdk:
            yield sdk, seen


@pytest.mark.parametrize("kwargs", MISSING_VALUES, ids=MISSING_IDS)
def test_missing_new_value_is_rejected_before_http(client, kwargs):
    sdk, seen = client
    with pytest.raises(TypeError, match="new_value"):
        sdk.datasets.cells.update(DATASET_ID, **CELL, **kwargs)
    assert seen == []


@pytest.mark.parametrize("via_extra_body", [False, True], ids=["direct", "body-override"])
@pytest.mark.parametrize("new_value", ["replacement", "", None])
def test_explicit_new_value_is_sent_including_clear_values(client, new_value, via_extra_body):
    sdk, seen = client
    sdk.datasets.cells.update(
        DATASET_ID, **CELL,
        new_value="original" if via_extra_body else new_value,
        extra_body={"new_value": new_value} if via_extra_body else None,
    )
    assert len(seen) == 1
    assert seen[0].method == "POST"
    assert str(seen[0].url) == f"{BASE}/model-hub/develops/{DATASET_ID}/update_cell_value/"
    assert json.loads(seen[0].content) == {**CELL, "new_value": new_value}


@pytest.mark.parametrize("kwargs", MISSING_VALUES, ids=MISSING_IDS)
def test_async_missing_new_value_is_rejected_before_http(kwargs):
    async def scenario():
        seen = []
        async with httpx.AsyncClient(transport=httpx.MockTransport(_handler(seen))) as http:
            async with fp.AsyncClient(
                api_key="k", secret_key="s", base_url=BASE, http_client=http
            ) as sdk:
                with pytest.raises(TypeError, match="new_value"):
                    await sdk.datasets.cells.update(DATASET_ID, **CELL, **kwargs)
        assert seen == []

    asyncio.run(scenario())


@pytest.mark.parametrize("via_extra_body", [False, True], ids=["direct", "body-override"])
@pytest.mark.parametrize("new_value", ["replacement", "", None])
def test_async_explicit_new_value_is_sent_including_clear_values(new_value, via_extra_body):
    async def scenario():
        seen = []
        async with httpx.AsyncClient(transport=httpx.MockTransport(_handler(seen))) as http:
            async with fp.AsyncClient(
                api_key="k", secret_key="s", base_url=BASE, http_client=http
            ) as sdk:
                await sdk.datasets.cells.update(
                    DATASET_ID, **CELL,
                    new_value="original" if via_extra_body else new_value,
                    extra_body={"new_value": new_value} if via_extra_body else None,
                )
        assert len(seen) == 1
        assert seen[0].method == "POST"
        assert str(seen[0].url) == f"{BASE}/model-hub/develops/{DATASET_ID}/update_cell_value/"
        assert json.loads(seen[0].content) == {**CELL, "new_value": new_value}

    asyncio.run(scenario())


def test_catalog_regeneration_preserves_cell_update_safety_and_examples():
    from ._generator_support import CATALOG, CONTRACT, ROOT, generate, pygen, tsgen
    from sdkgen.generator import docs

    spec = copy.deepcopy(CONTRACT)
    op = next(
        op for op in generate.load(spec, copy.deepcopy(CATALOG))
        if op.id == "datasets.cells.update"
    )
    replacement = next(p for p in op.params_in("body") if p.name == "new_value")
    assert replacement.required
    assert replacement.schema["x-nullable"] is True

    py_source = (ROOT / "python/fi/platform/resources/base.py").read_text()
    for is_async in (False, True):
        method = pygen.py39(pygen._method(op, is_async=is_async))
        assert "new_value: str | None," in method
        assert "isinstance(body['new_value'], NotGiven)" in method
        assert method in py_source

    ts_source = (ROOT / "typescript/futureagi/src/platform/resources/base.ts").read_text()
    interface, fields = tsgen._params_interface(op)
    method = tsgen._method(op, fields)
    assert "new_value: string | null;" in interface
    assert "params?.new_value === undefined" in method
    assert "...(options?.extraBody ?? {})" in method
    assert "body.new_value === undefined" in method
    assert "{ ...options, extraBody: undefined }" in method
    assert interface in ts_source
    assert method in ts_source

    page = (ROOT / "docs/sdk-reference/datasets.mdx").read_text()
    py_example = docs.python_example(op, spec["definitions"])
    ts_example = docs.typescript_example(op, spec["definitions"])
    assert 'new_value="your-new-value"' in py_example
    assert 'new_value: "your-new-value"' in ts_example
    assert py_example in page
    assert ts_example in page
    assert docs.python_signature(op) in page
    assert docs.typescript_signature(op) in page
    assert "To clear a cell deliberately" in op.description
    assert op.description in page
    section = docs._method_section(op, {}, spec["definitions"])
    assert section in page
    assert section.count("<CodeGroup>") == 2
    assert "#### Clear a cell deliberately" in section
    assert "new_value=None" in section
    assert "new_value: null" in section
    assert 'when `new_value` is omitted, `null`, or `""`' in section
