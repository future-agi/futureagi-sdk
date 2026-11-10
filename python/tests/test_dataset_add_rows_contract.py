"""Add-rows wire contract, with real public models and mocked transport.

Schemas copied from api_contracts/openapi/swagger.json at revision
502e447cc32857480fd3c9b2e90c9fef2a13719c (file SHA-256
021dd308f7eef8ea1ce1353b93959e38a1f569a054647568b7ed17565cc308c9).
Only the OpenAPI x-json-value extension is translated for JSON Schema validation.
No server, credentials, or network access is needed.
"""

import json
from copy import deepcopy
from unittest.mock import Mock

import pytest
from fi.api.types import HttpMethod
from fi.datasets.dataset import Dataset, DatasetResponseHandler
from fi.datasets.types import Cell, Column, DatasetConfig, Row
from fi.utils.errors import DatasetError, DatasetValidationError
from jsonschema import Draft7Validator, FormatChecker, ValidationError

SCHEMAS = {
    "DatasetRowCellRequest": {
        "required": ["column_name"],
        "type": "object",
        "properties": {
            "column_name": {"title": "Column name", "type": "string", "minLength": 1},
            "value": {
                "title": "Value", "type": "object", "x-nullable": True,
                "x-json-value": True, "description": "Any valid JSON value.",
            },
        },
        "additionalProperties": False,
    },
    "DatasetRowRequest": {
        "type": "object",
        "properties": {
            "id": {"title": "Id", "type": "string", "format": "uuid"},
            "order": {
                "title": "Order",
                "description": "Legacy input accepted for compatibility; rows are appended in request order.",
                "type": "integer",
            },
            "cells": {
                "type": "array", "items": {"$ref": "#/definitions/DatasetRowCellRequest"},
                "default": [],
            },
        },
        "additionalProperties": False,
    },
    "DatasetAddRowsRequest": {
        "required": ["rows"],
        "type": "object",
        "properties": {
            "rows": {"type": "array", "items": {"$ref": "#/definitions/DatasetRowRequest"}},
        },
        "additionalProperties": False,
    },
}

DATASET_ID = "11111111-1111-4111-8111-111111111111"
ROW_ID = "22222222-2222-4222-8222-222222222222"
COLUMN_ID = "33333333-3333-4333-8333-333333333333"
BASE_URL = "https://dataset.invalid"
VALUES = ["hello", "", 0, 1.5, False, None, [], {}, [1, False, None], {"nested": [0, False, None]}]


def validate_body(body):
    schemas = deepcopy(SCHEMAS)
    value = schemas["DatasetRowCellRequest"]["properties"]["value"]
    assert value["x-json-value"] is True
    value["type"] = ["object", "array", "string", "number", "boolean", "null"]
    schema = {"$ref": "#/definitions/DatasetAddRowsRequest", "definitions": schemas}
    Draft7Validator.check_schema(schema)
    Draft7Validator(schema, format_checker=FormatChecker()).validate(body)


@pytest.mark.parametrize("level", ["request", "row", "cell"])
def test_contract_rejects_extra_fields_at_every_level(level):
    cell = {"column_name": "input", "value": None}
    row = {"id": ROW_ID, "order": 0, "cells": [cell]}
    body = {"rows": [row]}
    validate_body(body)
    {"request": body, "row": row, "cell": cell}[level]["unexpected"] = "synthetic"
    with pytest.raises(ValidationError, match="Additional properties are not allowed"):
        validate_body(body)


@pytest.fixture
def dataset(monkeypatch):
    # Avoid constructor credential discovery; leave all request builders intact.
    client = object.__new__(Dataset)
    client._base_url = BASE_URL
    client.dataset_config = DatasetConfig(id=DATASET_ID, name="fixture", model_type="GenerativeLLM")

    def transport(*, config, response_handler):
        assert response_handler is DatasetResponseHandler
        assert config.timeout == 30
        if config.method == HttpMethod.GET:
            assert config.url == f"{BASE_URL}/model-hub/develops/get-datasets-names/"
            assert config.params == {"search_text": "fixture"}
            assert config.json == {}
            return client.dataset_config
        return {"result": "synthetic success"}

    client.request = Mock(side_effect=transport)
    monkeypatch.setattr(Dataset, "_get_instance", classmethod(lambda cls, **kwargs: client))
    return client


def posted(dataset, route):
    calls = [c.kwargs["config"] for c in dataset.request.call_args_list
             if c.kwargs["config"].method == HttpMethod.POST]
    assert len(calls) == 1
    assert calls[0].url == f"{BASE_URL}/model-hub/develops/{route}"
    # Validate the serialized JSON rather than only Python container objects.
    return json.loads(json.dumps(calls[0].json, allow_nan=False))


@pytest.mark.parametrize("method", ["add_rows", "add_dataset_rows"])
@pytest.mark.parametrize("input_kind", ["public-defaults", "public-rich", "dictionaries"])
def test_add_rows_sends_only_request_cell_fields(dataset, method, input_kind):
    cells = []
    expected_cells = []
    for index, value in enumerate(VALUES):
        options = {"column_name": f"column_{index}", "value": deepcopy(value)}
        expected_cells.append(deepcopy(options))
        if input_kind == "public-rich":
            options.update(column_id=COLUMN_ID, row_id=ROW_ID, value_infos=[{"score": 0}],
                           metadata={"keep": False}, status="failed", failure_reason="synthetic")
        cells.append(Cell(**options))
    rows = [Row(id=ROW_ID, order=7, cells=cells), Row(cells=[Cell(column_name="other", value="second")])]
    if input_kind == "dictionaries":
        rows = [{"cells": expected_cells}, {"cells": [{"column_name": "other", "value": "second"}]}]
    before = deepcopy(rows)

    if method == "add_rows":
        assert dataset.add_rows(rows) is dataset
        assert dataset.request.call_count == 1
    else:
        assert Dataset.add_dataset_rows("fixture", rows) is dataset
        assert dataset.request.call_count == 2  # Unchanged by-name lookup, then POST.

    body = posted(dataset, f"{DATASET_ID}/add_rows/")
    validate_body(body)
    assert set(body) == {"rows"}
    assert len(body["rows"]) == 2
    assert body["rows"][0]["cells"] == expected_cells
    assert body["rows"][1]["cells"] == [{"column_name": "other", "value": "second"}]
    for index, row in enumerate(body["rows"]):
        assert set(row) == {"id", "order", "cells"}
        assert all(set(cell) == {"column_name", "value"} for cell in row["cells"])
        if input_kind != "dictionaries":
            assert row["id"] == str(rows[index].id)
            assert row["order"] == rows[index].order
    assert rows == before


def test_public_cell_and_row_serialization_is_unchanged(dataset):
    cell = Cell(column_id=COLUMN_ID, row_id=ROW_ID, column_name="input", value={"a": [False]},
                value_infos=[{"score": 0}], metadata={"keep": True}, status="failed",
                failure_reason="synthetic")
    expected_cell = {
        "column_id": COLUMN_ID, "row_id": ROW_ID, "column_name": "input", "value": {"a": [False]},
        "value_infos": [{"score": 0}], "metadata": {"keep": True}, "status": "failed",
        "failure_reason": "synthetic",
    }
    row = Row(id=ROW_ID, order=9, cells=[cell])
    expected_row = {"id": ROW_ID, "order": 9, "cells": [expected_cell]}
    assert cell.to_dict() == expected_cell
    assert row.to_dict() == expected_row
    dataset.add_rows([row])
    assert cell.to_dict() == expected_cell
    assert row.to_dict() == expected_row


@pytest.mark.parametrize("method", ["add_columns", "add_dataset_columns"])
def test_add_columns_body_is_unchanged(dataset, method):
    column = Column(id=COLUMN_ID, name="input", data_type="text", source_id="synthetic",
                    metadata={"keep": False})
    if method == "add_columns":
        assert dataset.add_columns([column]) is dataset
    else:
        assert Dataset.add_dataset_columns("fixture", [column]) is dataset
    assert posted(dataset, f"{DATASET_ID}/add_columns/") == {"new_columns_data": [{
        "id": COLUMN_ID, "name": "input", "data_type": "text", "source": "OTHERS",
        "source_id": "synthetic", "metadata": {"keep": False},
    }]}


def test_delete_body_is_unchanged(dataset):
    dataset.delete()
    config = dataset.request.call_args.kwargs["config"]
    assert config.method == HttpMethod.DELETE
    assert config.json == {"dataset_ids": [DATASET_ID]}
    dataset.request.assert_called_once()


def test_create_body_is_unchanged(dataset):
    created = dataset.dataset_config
    dataset.dataset_config = DatasetConfig(name="fixture", model_type="GenerativeLLM")
    dataset.request.side_effect = None
    dataset.request.return_value = created
    assert dataset.create() is dataset
    assert posted(dataset, "create-empty-dataset/") == {
        "new_dataset_name": "fixture", "model_type": "GenerativeLLM",
    }


@pytest.mark.parametrize("method", ["add_rows", "add_dataset_rows"])
def test_empty_rows_still_fail_before_transport(dataset, method):
    with pytest.raises(DatasetValidationError, match="Rows list cannot be empty"):
        if method == "add_rows":
            dataset.add_rows([])
        else:
            Dataset.add_dataset_rows("fixture", [])
    dataset.request.assert_not_called()


def test_missing_dataset_id_still_fails_before_transport(dataset):
    dataset.dataset_config = None
    with pytest.raises(DatasetError, match="configured with an ID"):
        dataset.add_rows([Row(cells=[Cell(column_name="input", value="value")])])
    dataset.request.assert_not_called()
