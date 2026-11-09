"""JSON downloads use the same records-array format when loading pandas."""

import json
import socket
from unittest.mock import Mock
from uuid import UUID

import pandas as pd
import pytest

from fi.api.types import HttpMethod
from fi.datasets.dataset import Dataset, DatasetResponseHandler
from fi.datasets.types import Cell, Column, DatasetConfig, DatasetTable, Row


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "missing-login.json"))
    monkeypatch.delenv("FI_EXTRA_HEADERS", raising=False)

    def refuse(*args, **kwargs):
        raise AssertionError("Unexpected network access")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)


def download_client(pages):
    client = Dataset(
        dataset_config=DatasetConfig(id=UUID(int=1), name="sample", model_type="GenerativeLLM"),
        fi_api_key="synthetic-api", fi_secret_key="synthetic-secret",
        fi_base_url="https://datasets.invalid", session=Mock(),
    )
    seen = []

    def request(config, response_handler):
        assert config.method == HttpMethod.GET
        assert response_handler is DatasetResponseHandler
        page = config.params["current_page_index"]
        seen.append(page)
        return DatasetTable(
            id=UUID(int=1), columns=[Column(id=UUID(int=2), name="input", data_type="text")],
            rows=[Row(cells=[Cell(column_id=UUID(int=2), value=value)]) for value in pages[page]],
            metadata={"total_pages": len(pages)},
        )

    client.request = Mock(side_effect=request)
    return client, seen


@pytest.mark.parametrize("pages", [[["a", "b"]], [["a"], ["b"]], [["a"]]])
def test_json_download_preserves_record_rows_and_named_columns(tmp_path, pages):
    client, seen = download_client(pages)
    path = tmp_path / "rows.json"
    frame = client.download(str(path), load_to_pandas=True)
    expected = [{"input": value} for page in pages for value in page]
    assert json.loads(path.read_text()) == expected
    assert isinstance(frame, pd.DataFrame)
    assert list(frame.columns) == ["input"]
    assert frame.to_dict("records") == expected
    assert seen == list(range(len(pages)))


def test_empty_json_download_returns_an_empty_frame(tmp_path):
    client, seen = download_client([[]])
    path = tmp_path / "empty.json"
    frame = client.download(str(path), load_to_pandas=True)
    assert json.loads(path.read_text()) == []
    assert isinstance(frame, pd.DataFrame)
    assert frame.empty
    assert seen == [0]


def test_json_file_download_keeps_records_array_and_chaining(tmp_path):
    client, seen = download_client([["a", "b"]])
    path = tmp_path / "rows.json"
    assert client.download(str(path)) is client
    assert client.file_path == str(path)
    assert json.loads(path.read_text()) == [{"input": "a"}, {"input": "b"}]
    assert seen == [0]
