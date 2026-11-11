"""Draft saves and deployment endpoint behavior with offline transports."""

import asyncio
import json
import socket
from unittest.mock import Mock

import httpx
import pytest
import requests

from fi.client import Client as LegacyClient
from fi.gateway import AgentCC, AsyncAgentCC
from fi.platform import AsyncClient, Client, NotFoundError, RequestOptions
from fi.platform._errors import AuthenticationError, InternalServerError
from fi.prompt.client import Prompt
from fi.prompt.types import ModelConfig, PromptTemplate, UserMessage
from fi.utils.types import Environments, ModelTypes

BASE_URL = "https://deployment.example.invalid"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.delenv("FI_EXTRA_HEADERS", raising=False)

    def blocked(*args, **kwargs):
        pytest.fail("Offline tests must not open a socket")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


def test_save_current_draft_only_saves(monkeypatch):
    template = PromptTemplate(
        id="00000000-0000-0000-0000-000000000001", name="example", version="v7",
        messages=[UserMessage(content="Hello {{name}}")],
        model_configuration=ModelConfig(model_name="test-model"),
        variable_names={"name": ["Ada"]}, evaluation_configs=[{"name": "test-eval"}],
        metadata={"description": "example"},
    )
    prompt = Prompt(template, "test-key", "test-secret", BASE_URL)
    monkeypatch.setattr(prompt, "_current_version_is_draft", lambda: True)
    messages, placeholders = prompt._prepare_messages_and_placeholders()
    request = Mock(return_value={})
    monkeypatch.setattr(prompt, "request", request)
    try:
        assert prompt.save_current_draft() is True
        request.assert_called_once()
        config = request.call_args.kwargs["config"]
        assert config.method.value == "POST"
        assert str(template.id) in config.url
        assert config.json == {
            "is_run": False, "is_sdk": True, "version": "v7",
            "prompt_config": [{
                "messages": messages,
                "configuration": {
                    "model": "test-model", "temperature": 0.7, "max_tokens": 1000,
                    "top_p": 1.0, "frequency_penalty": 0, "presence_penalty": 0,
                },
                "placeholders": list(placeholders),
            }],
            "variable_names": template.variable_names,
            "evaluation_configs": template.evaluation_configs,
            "metadata": template.metadata, "placeholders": placeholders,
        }
        assert config.json["is_run"] is False
    finally:
        prompt.close()


INVALID_MODELS = [
    {}, {"model": None}, {"model": ""}, {"model": " \t"}, {"model": 3},
    {"extra_body": {"model": ""}}, {"extra_body": {"model": None}},
    {"extra_body": {"model": " \n"}},
    {"model": "test-model", "extra_body": {"model": ""}},
]
VALID_MODELS = [
    {"model": "test-model"},
    {"extra_body": {"model": "test-model"}},
    {"model": "", "extra_body": {"model": "test-model"}},
    {"model": "other-model", "extra_body": {"model": "test-model"}},
]


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("arguments", INVALID_MODELS)
def test_images_require_model_before_request(arguments, asynchronous):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(200, json={"created": 1, "data": []})

    async def run_async():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as transport:
            async with AsyncAgentCC(api_key="test-key", base_url=BASE_URL, http_client=transport) as client:
                with pytest.raises(ValueError, match="model"):
                    await client.images.generate(prompt="A tree", **arguments)

    try:
        if asynchronous:
            asyncio.run(run_async())
        else:
            with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
                with AgentCC(api_key="test-key", base_url=BASE_URL, http_client=transport) as client:
                    with pytest.raises(ValueError, match="model"):
                        client.images.generate(prompt="A tree", **arguments)
    finally:
        assert calls == []


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("arguments", VALID_MODELS)
def test_images_accept_model_from_argument_or_extra_body(arguments, asynchronous):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(200, json={"created": 1, "data": []})

    async def run_async():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as transport:
            async with AsyncAgentCC(api_key="test-key", base_url=BASE_URL, http_client=transport) as client:
                return await client.images.generate(prompt="A tree", n=2, **arguments)

    if asynchronous:
        result = asyncio.run(run_async())
    else:
        with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
            with AgentCC(api_key="test-key", base_url=BASE_URL, http_client=transport) as client:
                result = client.images.generate(prompt="A tree", n=2, **arguments)
    assert result.data == []
    assert len(calls) == 1
    assert calls[0].method == "POST"
    assert calls[0].url.path == "/v1/images/generations"
    assert json.loads(calls[0].content) == {"prompt": "A tree", "n": 2, "model": "test-model"}


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("status,error_type", [(404, NotFoundError), (401, AuthenticationError), (500, InternalServerError)])
def test_usage_overview_errors_preserve_compatibility(status, error_type, asynchronous):
    calls = []
    body = {"detail": "unavailable", "code": "test-code", "type": "test-type"}

    def respond(request):
        calls.append(request)
        return httpx.Response(status, json=body, headers={"x-request-id": "test-request"})

    arguments = dict(
        period="month", period_end="2026-01-01", workspace_id="workspace-1",
        extra_query={"custom": "value"}, options=RequestOptions(headers={"X-Test": "value"}),
    )

    async def run_async():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as transport:
            async with AsyncClient(api_key="test-key", secret_key="test-secret", base_url=BASE_URL,
                                   http_client=transport, max_retries=0) as client:
                with pytest.raises(error_type) as caught:
                    await client.usage.overview(**arguments)
                return caught.value

    if asynchronous:
        error = asyncio.run(run_async())
    else:
        with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
            with Client(api_key="test-key", secret_key="test-secret", base_url=BASE_URL,
                        http_client=transport, max_retries=0) as client:
                with pytest.raises(error_type) as caught:
                    client.usage.overview(**arguments)
                error = caught.value
    assert len(calls) == 1
    assert calls[0].method == "GET"
    assert calls[0].url.path == "/usage/v2/usage-overview/"
    assert dict(calls[0].url.params) == {
        "period": "month", "period_end": "2026-01-01", "workspace_id": "workspace-1", "custom": "value",
    }
    assert calls[0].headers["X-Test"] == "value"
    assert error.status_code == status
    assert error.response.request is calls[0]
    assert error.body == body
    assert error.request_id == "test-request"
    if status == 404:
        assert type(error).__name__ == "UsageOverviewUnavailableError"
        from fi.platform.resources.usage import UsageOverviewUnavailableError

        assert isinstance(error, UsageOverviewUnavailableError)
        assert isinstance(error, NotFoundError)
        assert "this deployment does not provide" in str(error).lower()
        assert "GET /usage/v2/usage-overview/" in str(error)
        assert isinstance(error.__cause__, NotFoundError)
    else:
        assert type(error) is error_type


@pytest.mark.parametrize("status", [404, 401, 500])
def test_legacy_log_errors_preserve_compatibility(monkeypatch, status):
    response = requests.Response()
    response.status_code = status
    response._content = b"not JSON"
    calls = []

    def send(session, request, **kwargs):
        calls.append(request)
        response.request = request
        response.url = request.url
        return response

    monkeypatch.setattr(requests.Session, "send", send)
    client = LegacyClient("test-key", "test-secret", BASE_URL)
    try:
        with pytest.warns(DeprecationWarning, match="Client.log is deprecated"):
            with pytest.raises(requests.HTTPError) as caught:
                client.log("test-model", ModelTypes.GENERATIVE_LLM, Environments.PRODUCTION)
        error = caught.value
        assert len(calls) == 1
        assert calls[0].method == "POST"
        assert calls[0].url == BASE_URL + "/sdk/api/v1/log/model/"
        assert error.response is response
        assert error.request is calls[0]
        if status == 404:
            assert type(error).__name__ == "LegacyModelLogUnavailableError"
            from fi.client import LegacyModelLogUnavailableError

            assert isinstance(error, LegacyModelLogUnavailableError)
            assert isinstance(error, requests.HTTPError)
            assert "this deployment does not provide" in str(error).lower()
            assert "POST /sdk/api/v1/log/model/" in str(error)
            assert "traceAI instrumentation" in str(error)
        else:
            assert type(error) is requests.HTTPError
    finally:
        client.close()
