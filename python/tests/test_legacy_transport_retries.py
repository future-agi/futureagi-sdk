"""Legacy transport must not replay writes with an unknown outcome."""

import socket
from unittest.mock import Mock

import pytest
from requests import Response
from requests.exceptions import ConnectionError, ReadTimeout, Timeout

from fi.api.auth import HttpClient, ResponseHandler
from fi.api.types import HttpMethod, RequestConfig


BASE_URL = "https://transport.invalid"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.delenv("FI_EXTRA_HEADERS", raising=False)

    def refuse(*args, **kwargs):
        raise AssertionError("Unexpected network access")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)


@pytest.mark.parametrize("method", [HttpMethod.POST, HttpMethod.PATCH])
@pytest.mark.parametrize("error_type", [ReadTimeout, ConnectionError, Timeout, RuntimeError])
@pytest.mark.parametrize("failure_stage", ["dispatch", "response"])
def test_ambiguous_write_failure_is_not_replayed(method, error_type, failure_stage, monkeypatch):
    failure = error_type("Synthetic unknown write outcome")
    sleep = Mock()
    monkeypatch.setattr("fi.api.auth.time.sleep", sleep)
    session = Mock()
    if failure_stage == "dispatch":
        session.request.side_effect = failure
    else:
        session.request.return_value.result.side_effect = failure
    client = HttpClient(base_url=BASE_URL, session=session)
    config = RequestConfig(method=method, url=BASE_URL + "/write", json={"input": "a"})
    with pytest.raises(error_type) as caught:
        client.request(config)
    assert caught.value is failure
    assert session.request.call_count == 1
    sleep.assert_not_called()


@pytest.mark.parametrize("method", [HttpMethod.GET, HttpMethod.PUT, HttpMethod.DELETE])
def test_idempotent_methods_keep_the_configured_retry_budget(method):
    failure = ReadTimeout("Synthetic transient failure")
    session = Mock()
    session.request.return_value.result.side_effect = failure
    client = HttpClient(base_url=BASE_URL, session=session)
    with pytest.raises(ReadTimeout) as caught:
        client.request(RequestConfig(method=method, url=BASE_URL, retry_attempts=2, retry_delay=0))
    assert caught.value is failure
    assert session.request.call_count == 2


def test_get_can_recover_after_a_read_timeout():
    response = Response()
    response.status_code = 200
    session = Mock()
    session.request.return_value.result.side_effect = [ReadTimeout("Synthetic timeout"), response]
    client = HttpClient(base_url=BASE_URL, session=session)
    assert client.request(RequestConfig(method=HttpMethod.GET, url=BASE_URL, retry_delay=0)) is response
    assert session.request.call_count == 2


@pytest.mark.parametrize("status", [200, 400, 500])
def test_received_response_is_handled_once_without_replay(status):
    response = Response()
    response.status_code = status
    session = Mock()
    session.request.return_value.result.return_value = response
    failure = ValueError("Synthetic response parsing error")
    handler = Mock(spec=ResponseHandler)
    handler.parse.side_effect = failure
    client = HttpClient(base_url=BASE_URL, session=session)
    with pytest.raises(ValueError) as caught:
        client.request(RequestConfig(method=HttpMethod.POST, url=BASE_URL), handler)
    assert caught.value is failure
    assert session.request.call_count == 1
    handler.parse.assert_called_once_with(response=response)
