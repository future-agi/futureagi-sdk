"""Published model-log behavior, exercised through an offline HTTP transport."""

import json
import socket
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from fi.client import Client, ClientResponseHandler, LegacyModelLogUnavailableError
from fi.api.types import HttpMethod
from fi.utils.constants import MAX_FUTURE_YEARS_FROM_CURRENT_TIME, MAX_PAST_YEARS_FROM_CURRENT_TIME
from fi.utils.errors import InvalidValueType, MissingRequiredKey
from fi.utils.routes import Routes
from fi.utils.types import Environments, ModelTypes
from tests.core import _egress


pytestmark = pytest.mark.filterwarnings("ignore:Client.log is deprecated:DeprecationWarning")
NOW = 1_800_000_000
YEAR = 365 * 24 * 60 * 60
BASE_URL = "https://logging.example.invalid/tenant"
HISTORY = {"chat_history": [{"role": "user", "content": "Hello"}]}
GRAPH = {
    "chat_graph": {
        "conversation_id": "conversation-id",
        "nodes": [{"message": {
            "id": "message-id",
            "author": {"role": "assistant", "metadata": {}},
            "content": {"content_type": "text", "parts": ["Hello"]},
            "context": {},
        }}],
    }
}


@pytest.fixture
def transport(monkeypatch, tmp_path):
    _egress.install(monkeypatch, tmp_path)
    monkeypatch.delenv("FI_EXTRA_HEADERS", raising=False)

    def no_network(*args, **kwargs):
        pytest.fail("The mocked model-log transport must not open a socket")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket, "getaddrinfo", no_network)
    monkeypatch.setattr("fi.client.time.time", lambda: NOW)
    response = requests.Response()
    response.status_code = 200
    response._content = b'{"id": "log-id"}'
    calls = []

    def send(session, request, **kwargs):
        response.request = request
        response.url = request.url
        calls.append((request, kwargs))
        return response

    monkeypatch.setattr(requests.Session, "send", send)
    client = Client(
        "offline-key", "offline-secret", BASE_URL + "/",
        timeout=41, max_workers=1,
    )
    client.request = Mock(wraps=client.request)
    try:
        yield client, calls, response
    finally:
        client.close()
        _egress.assert_no_attempts()


def log(client, **kwargs):
    arguments = {
        "model_id": "model-id",
        "model_type": ModelTypes.GENERATIVE_LLM,
        "environment": Environments.PRODUCTION,
    }
    arguments.update(kwargs)
    return client.log(**arguments)


@pytest.mark.parametrize("model_type", list(ModelTypes))
@pytest.mark.parametrize("environment", list(Environments))
def test_positional_payload_and_configured_route(transport, model_type, environment):
    client, calls, response = transport
    conversation = {**HISTORY, **GRAPH}
    tags = {"text": "value", "flag": False, "count": 2, "fraction": 0.5}
    result = client.log(
        "model-id", model_type, environment, "v1", NOW,
        conversation, tags, 9,
    )
    assert result == {"id": "log-id", "status": "success"}
    assert len(calls) == 1
    request, options = calls[0]
    assert request.method == "POST"
    assert Routes.log_model.value == "sdk/api/v1/log/model/"
    assert request.url == BASE_URL + "/sdk/api/v1/log/model/"
    assert json.loads(request.body) == {
        "model_id": "model-id", "model_type": model_type.value,
        "environment": environment.value, "model_version": "v1",
        "prediction_timestamp": NOW, "conversation": conversation, "tags": tags,
    }
    assert options["timeout"] == 9
    config = client.request.call_args.kwargs["config"]
    assert config.method is HttpMethod.POST
    assert config.timeout == 9
    assert client.request.call_args.kwargs["response_handler"] is ClientResponseHandler


@pytest.mark.parametrize("timeout,wire_timeout", [(None, 41), (0, 41), (7, 7)])
def test_default_null_fields_and_timeout_forwarding(transport, timeout, wire_timeout):
    client, calls, response = transport
    log(client, timeout=timeout)
    request, options = calls[0]
    assert json.loads(request.body) == {
        "model_id": "model-id", "model_type": "GenerativeLLM", "environment": 3,
        "model_version": None, "prediction_timestamp": None,
        "conversation": None, "tags": None,
    }
    assert client.request.call_args.kwargs["config"].timeout == timeout
    assert options["timeout"] == wire_timeout


@pytest.mark.parametrize("value", [None, {}, "", [], 0, False])
def test_published_falsy_optional_values_are_not_rewritten(transport, value):
    client, calls, response = transport
    log(client, model_version=value, conversation=value, tags=value)
    payload = json.loads(calls[0][0].body)
    assert payload["model_version"] == value
    assert payload["conversation"] == value
    assert payload["tags"] == value


@pytest.mark.parametrize("conversation", [HISTORY, GRAPH])
def test_each_published_conversation_format(transport, conversation):
    client, calls, response = transport
    log(client, conversation=conversation)
    assert json.loads(calls[0][0].body)["conversation"] == conversation


@pytest.mark.parametrize("changes,error", [
    ({"model_id": 123}, InvalidValueType),
    ({"model_type": "GenerativeLLM"}, InvalidValueType),
    ({"environment": 3}, InvalidValueType),
    ({"model_version": 123}, InvalidValueType),
    ({"conversation": "history"}, InvalidValueType),
    ({"conversation": {"other": []}}, MissingRequiredKey),
    ({"conversation": {"chat_history": "history"}}, InvalidValueType),
    ({"conversation": {"chat_history": ["message"]}}, InvalidValueType),
    ({"conversation": {"chat_history": [{"role": "user"}]}}, MissingRequiredKey),
    ({"conversation": {"chat_history": [{"role": 1, "content": "text"}]}}, InvalidValueType),
    ({"conversation": {"chat_history": [{"role": "user", "content": 1}]}}, InvalidValueType),
    ({"conversation": {"chat_graph": {"nodes": []}}}, MissingRequiredKey),
    ({"conversation": {"chat_graph": {"conversation_id": "id"}}}, MissingRequiredKey),
    ({"conversation": {"chat_graph": {"conversation_id": "id", "nodes": {}}}}, InvalidValueType),
    ({"conversation": {"chat_graph": {"conversation_id": "id", "nodes": [{}]}}}, MissingRequiredKey),
    ({"conversation": {"chat_graph": {"conversation_id": "id", "nodes": [{"message": "text"}]}}}, InvalidValueType),
    ({"tags": ["value"]}, InvalidValueType),
    ({"tags": {1: "value"}}, InvalidValueType),
    ({"tags": {"nested": {}}}, InvalidValueType),
    ({"tags": {"null": None}}, InvalidValueType),
    ({"prediction_timestamp": "now"}, InvalidValueType),
    ({"prediction_timestamp": NOW + MAX_FUTURE_YEARS_FROM_CURRENT_TIME * YEAR + 1}, ValueError),
    ({"prediction_timestamp": NOW - MAX_PAST_YEARS_FROM_CURRENT_TIME * YEAR - 1}, ValueError),
])
def test_validation_precedes_transport(transport, changes, error):
    client, calls, response = transport
    with pytest.raises(error) as caught:
        log(client, **changes)
    assert type(caught.value) is error
    assert calls == []
    client.request.assert_not_called()


@pytest.mark.parametrize("timestamp", [
    NOW, NOW + MAX_FUTURE_YEARS_FROM_CURRENT_TIME * YEAR,
    NOW - MAX_PAST_YEARS_FROM_CURRENT_TIME * YEAR,
])
def test_timestamp_boundaries_are_inclusive(transport, timestamp):
    client, calls, response = transport
    log(client, prediction_timestamp=timestamp)
    assert json.loads(calls[0][0].body)["prediction_timestamp"] == timestamp


@pytest.mark.parametrize("status_code,payload,expected", [
    (200, {"id": "log-id"}, {"id": "log-id", "status": "success"}),
    (201, {"status": "queued", "result": [1]}, {"status": "queued", "result": [1]}),
    (202, {"status": None}, {"status": None}),
])
def test_response_handler_returns_parsed_result(transport, status_code, payload, expected):
    client, calls, response = transport
    response.status_code = status_code
    response._content = json.dumps(payload).encode()
    assert log(client) == expected


@pytest.mark.parametrize("status_code", [400, 401, 404, 429, 500])
def test_http_errors_remain_requests_http_errors(transport, status_code):
    client, calls, response = transport
    response.status_code = status_code
    response._content = b"server error, not JSON"
    with pytest.raises(requests.HTTPError) as caught:
        log(client)
    assert isinstance(caught.value, requests.HTTPError)
    if status_code == 404:
        assert type(caught.value) is LegacyModelLogUnavailableError
    else:
        assert type(caught.value) is requests.HTTPError
    assert caught.value.response is response
    assert caught.value.request is calls[0][0]
    assert calls[0][0].url == BASE_URL + "/sdk/api/v1/log/model/"


def test_deprecation_points_to_current_api_without_redirecting(transport):
    client, calls, response = transport
    with pytest.warns(DeprecationWarning, match="Client.log is deprecated") as caught:
        client.log("model-id", ModelTypes.GENERATIVE_LLM, Environments.PRODUCTION)
    assert len(caught) == 1
    assert Path(caught[0].filename) == Path(__file__)
    message = str(caught[0].message)
    assert "traceAI" in message
    assert "FutureAGIClient" in message
    assert "client.tracing" in message
    assert "not drop-in" in message
    assert calls[0][0].url == BASE_URL + "/sdk/api/v1/log/model/"
