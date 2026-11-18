"""Prompt error responses must not hide the API failure with parsing errors."""

import json
from concurrent.futures import Future

import pytest
import requests
from requests_futures.sessions import FuturesSession

from fi.prompt import Prompt
from fi.prompt.cache import PromptCache
from fi.prompt.client import PromptResponseHandler
from fi.utils.errors import (
    InvalidAuthError,
    SDKException,
    TemplateAlreadyExists,
    TemplateNotFound,
)

BAD_REQUEST_MESSAGE = "Bad request – please verify request body."


def response_with_body(body, status=400):
    response = requests.Response()
    response.status_code = status
    response._content = body
    response.encoding = "utf-8"
    response.url = (
        "https://example.invalid/model-hub/prompt-labels/get-by-name/?name=example"
    )
    response.request = requests.Request("GET", response.url).prepare()
    return response


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Unexpected network request")

    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)


@pytest.mark.parametrize(
    "body",
    [b"", b"<html>Bad request</html>", b'{"message":'],
    ids=["empty", "html", "malformed-json"],
)
def test_non_json_bad_request_raises_sdk_exception(body):
    with pytest.raises(SDKException) as error:
        PromptResponseHandler.parse(response_with_body(body))

    assert type(error.value) is SDKException
    assert str(error.value) == BAD_REQUEST_MESSAGE


@pytest.mark.parametrize("detail", [None, [], "invalid", 42, False])
def test_non_object_bad_request_raises_sdk_exception(detail):
    response = response_with_body(json.dumps(detail).encode())

    with pytest.raises(SDKException) as error:
        PromptResponseHandler.parse(response)

    assert type(error.value) is SDKException
    assert str(error.value) == BAD_REQUEST_MESSAGE


@pytest.mark.parametrize(
    "detail, expected",
    [
        ({"message": "Invalid template version"}, "Invalid template version"),
        ({}, BAD_REQUEST_MESSAGE),
    ],
)
def test_bad_request_preserves_message(detail, expected):
    with pytest.raises(SDKException) as error:
        PromptResponseHandler.parse(response_with_body(json.dumps(detail).encode()))

    assert type(error.value) is SDKException
    assert str(error.value) == expected


@pytest.mark.parametrize("name", ["existing-template", None])
def test_duplicate_template_preserves_specialized_error(name):
    detail = {"error_code": "TEMPLATE_ALREADY_EXIST"}
    if name is not None:
        detail["name"] = name

    with pytest.raises(TemplateAlreadyExists) as error:
        PromptResponseHandler.parse(response_with_body(json.dumps(detail).encode()))

    assert error.value.template_name == (name if name is not None else "<unknown>")


def test_missing_label_preserves_specialized_error():
    detail = {"result": "No version found for label 'staging'", "label": "staging"}

    with pytest.raises(TemplateNotFound) as error:
        PromptResponseHandler.parse(response_with_body(json.dumps(detail).encode()))

    assert error.value.template_name == "Label 'staging'"


@pytest.mark.parametrize(
    "status, exception",
    [(403, InvalidAuthError), (404, TemplateNotFound), (500, requests.HTTPError)],
)
def test_other_error_statuses_preserve_exception(status, exception):
    response = response_with_body(b"not json", status=status)

    with pytest.raises(exception) as error:
        PromptResponseHandler.parse(response)

    if status == 404:
        assert error.value.template_name == "example"
    if status == 500:
        assert error.value.response is response


def test_success_response_is_unchanged():
    detail = {"result": {"id": "example"}}
    response = response_with_body(json.dumps(detail).encode(), status=200)
    response.request.method = "POST"
    assert PromptResponseHandler.parse(response) == detail


@pytest.mark.parametrize("body", [b"", b"<html>Bad request</html>", b'{"message":'])
@pytest.mark.parametrize("version, expected_requests", [("v1", 1), (None, 2)])
def test_get_template_by_name_surfaces_bad_request(
    monkeypatch, body, version, expected_requests
):
    calls = []

    def mocked_request(self, **kwargs):
        calls.append(kwargs)
        future = Future()
        future.set_result(response_with_body(body))
        return future

    monkeypatch.setattr(FuturesSession, "request", mocked_request)
    monkeypatch.setattr("fi.prompt.client.prompt_cache", PromptCache(max_workers=0))

    with pytest.raises(SDKException) as error:
        Prompt.get_template_by_name(
            "example",
            version=version,
            fi_api_key="synthetic-api-key",
            fi_secret_key="synthetic-secret-key",
            fi_base_url="https://example.invalid",
        )

    assert type(error.value) is SDKException
    assert str(error.value) == BAD_REQUEST_MESSAGE
    assert len(calls) == expected_requests
    assert all(call["method"] == "GET" for call in calls)
    if version is not None:
        assert calls[0]["params"] == {"name": "example", "version": version}
    else:
        assert calls[0]["params"] == {"name": "example", "label": "production"}
        assert calls[1]["params"] == {"name": "example"}
