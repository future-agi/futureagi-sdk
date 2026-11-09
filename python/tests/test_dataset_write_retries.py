"""Offline regressions for ambiguous dataset writes and bounded read retries."""

import json
import socket
from unittest.mock import Mock
from uuid import UUID

import pytest
from requests import Response
from requests.exceptions import ConnectionError, ReadTimeout

from fi.api.types import HttpMethod, RequestConfig
from fi.datasets.dataset import Dataset, DatasetResponseHandler
from fi.datasets.types import Cell, DatasetConfig, Row


BASE_URL = "https://datasets.invalid"


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "missing-login.json"))
    monkeypatch.delenv("FI_EXTRA_HEADERS", raising=False)
    monkeypatch.setattr("fi.api.auth.time.sleep", Mock())

    def refuse(*args, **kwargs):
        raise AssertionError("Unexpected network access")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)


def response(url, payload, status=200):
    result = Response()
    result.url = url
    result.status_code = status
    result._content = json.dumps(payload).encode()
    return result


def client_with(session, existing=False):
    return Dataset(
        dataset_config=DatasetConfig(
            id=UUID(int=1) if existing else None,
            name="sample", model_type="GenerativeLLM",
        ),
        fi_api_key="synthetic-api", fi_secret_key="synthetic-secret",
        fi_base_url=BASE_URL, session=session,
    )


def test_create_preserves_lost_response_instead_of_replaying_duplicate_name():
    lost_response = ReadTimeout("Synthetic response lost after creation")
    posts = []

    def send(method, url, **kwargs):
        future = Mock()
        if method == "GET":
            future.result.return_value = response(url, {"result": {"datasets": []}})
        else:
            assert method == "POST"
            posts.append(kwargs["json"])
            if len(posts) == 1:
                future.result.side_effect = lost_response
            else:
                future.result.return_value = response(url, {"detail": "Dataset already exists"}, 400)
        return future

    client = client_with(Mock(request=Mock(side_effect=send)))
    with pytest.raises(ReadTimeout) as caught:
        client.create()
    assert caught.value is lost_response
    assert posts == [{"new_dataset_name": "sample", "model_type": "GenerativeLLM"}]
    assert client.dataset_config.id is None


@pytest.mark.parametrize("operation", ["create", "add_rows"])
@pytest.mark.parametrize("error_type", [ReadTimeout, ConnectionError])
def test_dataset_write_is_sent_once_on_persistent_transport_failure(operation, error_type):
    failure = error_type("Synthetic ambiguous write failure")
    posts = []

    def send(method, url, **kwargs):
        future = Mock()
        if method == "GET":
            future.result.return_value = response(url, {"result": {"datasets": []}})
        else:
            assert method == "POST"
            posts.append(kwargs["json"])
            future.result.side_effect = failure
        return future

    client = client_with(Mock(request=Mock(side_effect=send)), existing=operation == "add_rows")
    with pytest.raises(error_type) as caught:
        if operation == "create":
            client.create()
        else:
            client.add_rows([Row(cells=[Cell(column_name="input", value="a")])])
    assert caught.value is failure
    assert len(posts) == 1


@pytest.mark.parametrize("max_retries,config_attempts,expected", [
    (3, 3, 3), (1, 3, 1), (3, 1, 1), (2, 5, 2), (5, 2, 2),
])
def test_dataset_reads_use_one_attempt_budget(max_retries, config_attempts, expected):
    failure = ReadTimeout("Synthetic read failure")
    session = Mock()
    session.request.return_value.result.side_effect = failure
    client = client_with(session, existing=True)
    config = RequestConfig(
        method=HttpMethod.GET, url=BASE_URL + "/rows", retry_attempts=config_attempts,
        retry_delay=0,
    )
    with pytest.raises(ReadTimeout) as caught:
        client.request_with_retry(config, DatasetResponseHandler, max_retries=max_retries)
    assert caught.value is failure
    assert session.request.call_count == expected
    assert config.retry_attempts == config_attempts


def test_dataset_read_can_recover_within_the_budget():
    session = Mock()
    expected = response(BASE_URL + "/rows", {"result": "ok"})
    session.request.return_value.result.side_effect = [ReadTimeout("Synthetic timeout"), expected]
    client = client_with(session, existing=True)
    result = client.request_with_retry(
        RequestConfig(method=HttpMethod.GET, url=expected.url, retry_delay=0),
        DatasetResponseHandler,
    )
    assert result == {"result": "ok"}
    assert session.request.call_count == 2
