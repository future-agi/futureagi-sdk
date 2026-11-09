"""Offline regressions for dataset identity, pagination, and response parsing."""

import json
import socket
from copy import deepcopy
from unittest.mock import Mock
from uuid import UUID

import pandas as pd
import pytest
from requests import Response

from fi.api.types import HttpMethod
from fi.datasets.dataset import Dataset, DatasetResponseHandler, LRUCache
from fi.datasets.types import (
    Cell, Column, DatasetConfig, DatasetTable, HuggingfaceDatasetConfig, Row,
)
from fi.utils.errors import DatasetError, DatasetNotFoundError

DATASET_ID = UUID(int=1)
COLUMN_ID = UUID(int=2)
BOOLEAN_COLUMN_ID = UUID(int=3)
BASE_URL = "https://datasets.invalid"


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setenv("FI_API_KEY", "synthetic-api")
    monkeypatch.setenv("FI_SECRET_KEY", "synthetic-secret")
    monkeypatch.setenv("FI_BASE_URL", BASE_URL)
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "no-login.json"))
    monkeypatch.delenv("FI_EXTRA_HEADERS", raising=False)
    monkeypatch.setattr(Dataset, "_dataset_instance_cache", LRUCache())

    def refuse(*args, **kwargs):
        raise AssertionError("Network access is not allowed in dataset unit tests")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(Dataset, "request", refuse)


def dataset_config(name="shared", dataset_id=DATASET_ID):
    return DatasetConfig(id=dataset_id, name=name, model_type="GenerativeLLM")


@pytest.mark.parametrize("changed", ["fi_api_key", "fi_secret_key", "fi_base_url", "session"])
def test_lookup_uses_each_callers_identity(monkeypatch, changed):
    calls = []

    def lookup(client, config, response_handler):
        calls.append((client, deepcopy(config)))
        return dataset_config(dataset_id=UUID(int=10 + len(calls)))

    monkeypatch.setattr(Dataset, "request", lookup)
    first_options = dict(fi_api_key="synthetic-a", fi_secret_key="synthetic-secret-a",
                         fi_base_url=BASE_URL, session=Mock())
    second_options = dict(first_options)
    second_options[changed] = Mock() if changed == "session" else {
        "fi_api_key": "synthetic-b", "fi_secret_key": "synthetic-secret-b",
        "fi_base_url": "https://other-datasets.invalid",
    }[changed]
    first = Dataset.get_dataset_config("shared", excluded_datasets=["excluded"], **first_options)
    second = Dataset.get_dataset_config("shared", excluded_datasets=["excluded"], **second_options)

    assert second is not first, "A lookup must not reuse another caller's authenticated client"
    assert len(calls) == 2
    assert second.dataset_config.id == UUID(int=12)
    assert second._fi_api_key == second_options["fi_api_key"]
    assert second._fi_secret_key == second_options["fi_secret_key"]
    assert second._base_url == second_options["fi_base_url"]
    assert second._session is second_options["session"]
    assert calls[1][1].params == {"search_text": "shared", "excluded_datasets": ["excluded"]}
    assert calls[1][1].url.startswith(second_options["fi_base_url"] + "/")


def test_lookup_resolves_changed_environment(monkeypatch):
    request = Mock(side_effect=[dataset_config(dataset_id=UUID(int=11)), dataset_config(dataset_id=UUID(int=12))])
    monkeypatch.setattr(Dataset, "request", request)
    first = Dataset.get_dataset_config("shared", session=Mock())
    monkeypatch.setenv("FI_API_KEY", "synthetic-next-api")
    monkeypatch.setenv("FI_SECRET_KEY", "synthetic-next-secret")
    monkeypatch.setenv("FI_BASE_URL", "https://next-datasets.invalid")
    second = Dataset.get_dataset_config("shared", session=Mock())
    assert second is not first
    assert second._fi_api_key == "synthetic-next-api"
    assert second._fi_secret_key == "synthetic-next-secret"
    assert second._base_url == "https://next-datasets.invalid"
    assert request.call_count == 2


def test_delete_by_name_uses_the_requested_account(monkeypatch):
    calls = []

    def request(client, config, response_handler):
        calls.append((client._fi_api_key, client._base_url, deepcopy(config)))
        if config.method == HttpMethod.GET:
            return dataset_config(dataset_id=UUID(int=11 if client._fi_api_key == "synthetic-a" else 12))
        return {"result": "deleted"}

    monkeypatch.setattr(Dataset, "request", request)
    first = Dataset.get_dataset_config("shared", fi_api_key="synthetic-a",
                                       fi_secret_key="synthetic-secret-a", session=Mock())
    Dataset.delete_dataset("shared", fi_api_key="synthetic-b", fi_secret_key="synthetic-secret-b",
                           fi_base_url="https://other-datasets.invalid", session=Mock())
    key, base, deletion = calls[-1]
    assert key == "synthetic-b"
    assert base == "https://other-datasets.invalid"
    assert deletion.method == HttpMethod.DELETE
    assert deletion.json == {"dataset_ids": [str(UUID(int=12))]}
    assert first.dataset_config.id == UUID(int=11)


def table(values, metadata, reverse_columns=False):
    columns = [Column(id=COLUMN_ID, name="number", data_type="integer"),
               Column(id=BOOLEAN_COLUMN_ID, name="enabled", data_type="boolean")]
    if reverse_columns:
        columns.reverse()
    rows = [Row(id=UUID(int=100 + value), cells=[
        Cell(column_id=COLUMN_ID, value=value),
        Cell(column_id=BOOLEAN_COLUMN_ID, value="true" if value % 2 else "false"),
    ]) for value in values]
    return DatasetTable(id=DATASET_ID, columns=columns, rows=rows, metadata=metadata)


def download_client(pages):
    client = Dataset(dataset_config=dataset_config(), session=Mock())
    seen = []

    def request(config, response_handler):
        assert response_handler is DatasetResponseHandler
        assert config.method == HttpMethod.GET
        page = config.params["current_page_index"]
        seen.append(page)
        assert page < len(pages), "Download requested a page after pagination had ended"
        return pages[page]

    client.request = Mock(side_effect=request)
    return client, seen


@pytest.mark.parametrize("metadata", [
    {"total_pages": 0, "total_rows": 0, "has_more": False},
    {"totalPages": 0, "totalRows": 0, "hasMore": False},
    {"total_pages": 0},
    {"has_more": False},
    {},
    None,
])
def test_empty_download_stops_after_one_request(tmp_path, metadata):
    client, seen = download_client([table([], metadata)])
    frame = client.download(str(tmp_path / "empty.csv"), load_to_pandas=True)
    assert isinstance(frame, pd.DataFrame)
    assert frame.empty
    assert list(frame.columns) == ["number", "enabled"]
    assert seen == [0]


@pytest.mark.parametrize("metadata", [
    {"total_pages": 5, "has_more": False},
    {"totalPages": 5, "hasMore": False},
    {"total_pages": 0},
])
def test_download_honors_terminal_pagination_metadata(tmp_path, metadata):
    client, seen = download_client([table([1], metadata)])
    frame = client.download(str(tmp_path / "last.csv"), load_to_pandas=True)
    assert frame["number"].tolist() == [1]
    assert seen == [0]


@pytest.mark.parametrize("metadata", [{}, {"total_pages": "invalid"}, {"total_pages": -1}])
def test_download_rejects_nonempty_pages_without_a_finite_page_count(tmp_path, metadata):
    client, seen = download_client([table([1], metadata)])
    with pytest.raises(DatasetError, match="pagination"):
        client.download(str(tmp_path / "invalid.csv"))
    assert seen == [0]
