"""Regression tests for the dataset SDK request/parse hardening.

These pin two fixes and are written to fail if either is reverted:

- A parse/deserialization error on a 2xx response must NOT re-send the request.
  Retrying a non-idempotent POST on a parse failure silently creates orphan
  datasets server-side.
- By-name lookup must resolve the EXACT name. The backend matches ``search_text``
  as a substring, so a prefix-colliding name must not blow up with "Multiple
  datasets found".
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from requests import Response

from fi.api.auth import APIKeyAuth, ResponseHandler
from fi.api.types import HttpMethod, RequestConfig
from fi.datasets.dataset import DatasetResponseHandler
from fi.utils.errors import DatasetNotFoundError

UUID_FOO = "11111111-1111-1111-1111-111111111111"
UUID_FOOBAR = "22222222-2222-2222-2222-222222222222"


def _mock_response(data, status_code=200, url="http://api.test/"):
    resp = MagicMock(spec=Response)
    resp.status_code = status_code
    resp.ok = 200 <= status_code < 300
    resp.json.return_value = data
    resp.text = json.dumps(data)
    resp.url = url
    return resp


def _client_with_session(result=None, side_effect=None):
    client = APIKeyAuth(fi_api_key="k", fi_secret_key="s")
    client._session = MagicMock()
    future = client._session.request.return_value
    if side_effect is not None:
        future.result.side_effect = side_effect
    else:
        future.result.return_value = result
    return client


class _BrokenHandler(ResponseHandler):
    """Simulates a contract-mismatch parse error on an otherwise-successful 2xx."""

    @classmethod
    def _parse_success(cls, response):
        raise KeyError("datasetId")

    @classmethod
    def _handle_error(cls, response):
        raise RuntimeError("unexpected error path")


# --------------------------------------------------------------------------
# A non-idempotent POST must not be re-sent on a parse error
# --------------------------------------------------------------------------

def test_post_not_resent_when_parsing_a_successful_response_fails():
    client = _client_with_session(result=_mock_response({"result": {}}, 200))
    config = RequestConfig(
        method=HttpMethod.POST,
        url="http://api.test/create-empty-dataset/",
        json={"new_dataset_name": "x"},
    )

    with pytest.raises(KeyError):
        client.request(config=config, response_handler=_BrokenHandler)

    # The POST reached the server once; the parse failure must not retry it.
    assert client._session.request.call_count == 1


def test_transport_failures_are_still_retried():
    client = _client_with_session(side_effect=ConnectionError("boom"))
    config = RequestConfig(
        method=HttpMethod.GET,
        url="http://api.test/get-datasets/",
        retry_attempts=3,
        retry_delay=0,
    )

    with pytest.raises(ConnectionError):
        client.request(config=config, response_handler=None)

    assert client._session.request.call_count == 3


# --------------------------------------------------------------------------
# By-name lookup resolves the exact name, not a fuzzy prefix match
# --------------------------------------------------------------------------

def _names_response(datasets, search_text):
    url = f"http://api.test/model-hub/develops/get-datasets-names/?search_text={search_text}"
    data = {"result": {"datasets": datasets}}
    return data, _mock_response(data, 200, url=url)


def test_by_name_resolves_exact_match_among_prefix_collision():
    datasets = [
        {"name": "foo", "dataset_id": UUID_FOO, "model_type": "GenerativeLLM"},
        {"name": "foo-bar", "dataset_id": UUID_FOOBAR, "model_type": "GenerativeLLM"},
    ]
    data, resp = _names_response(datasets, "foo")

    config = DatasetResponseHandler._parse_dataset_names(data, resp)

    assert str(config.id) == UUID_FOO
    assert config.name == "foo"


def test_by_name_raises_not_found_when_only_fuzzy_matches_exist():
    datasets = [
        {"name": "foo-bar", "dataset_id": UUID_FOOBAR, "model_type": "GenerativeLLM"},
    ]
    data, resp = _names_response(datasets, "foo")

    with pytest.raises(DatasetNotFoundError):
        DatasetResponseHandler._parse_dataset_names(data, resp)


@pytest.mark.parametrize("by_name", [True, False])
def test_legacy_rows_serialize_only_the_write_contract(by_name):
    from types import SimpleNamespace

    from fi.datasets.dataset import Dataset
    from fi.datasets.types import Cell, DatasetConfig, Row

    client = Dataset.__new__(Dataset)
    client.dataset_config = DatasetConfig(id=UUID_FOO, name="fixture", model_type="GenerativeLLM")
    client._base_url = "http://api.test"
    table = SimpleNamespace(columns=[SimpleNamespace(id=UUID_FOOBAR, name="answer")])
    client.request_with_retry = MagicMock(return_value=table)
    cell = Cell(column_id=UUID_FOOBAR, column_name="answer" if by_name else None,
                value=False, metadata={"read_only": True})
    row = Row(cells=[cell])
    before = row.model_dump()
    assert client.add_rows([row]) is client
    assert client.request_with_retry.call_count == (1 if by_name else 2)
    payload = client.request_with_retry.call_args.kwargs["config"].json
    assert payload == {"rows": [{"id": str(row.id), "order": 0,
                                 "cells": [{"column_name": "answer", "value": False}]}]}
    assert row.model_dump() == before


def test_legacy_unknown_column_id_cannot_post_partial_rows():
    from types import SimpleNamespace

    from fi.datasets.dataset import Dataset
    from fi.datasets.types import Cell, DatasetConfig, Row
    from fi.utils.errors import DatasetValidationError

    client = Dataset.__new__(Dataset)
    client.dataset_config = DatasetConfig(id=UUID_FOO, name="fixture", model_type="GenerativeLLM")
    client._base_url = "http://api.test"
    client.request_with_retry = MagicMock(return_value=SimpleNamespace(columns=[]))
    with pytest.raises(DatasetValidationError, match="unknown column"):
        client.add_rows([Row(cells=[Cell(column_id=UUID_FOOBAR, value="test")])])
    assert client.request_with_retry.call_count == 1
    assert client.request_with_retry.call_args.kwargs["config"].method == HttpMethod.GET
