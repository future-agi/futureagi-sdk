"""RL 2263a: no-send inspection shares wrapper validation and wire construction."""

import json
import socket

import httpx
import pytest

from fi.gateway._constants import NOT_GIVEN
from fi.gateway._exceptions import AgentCCError
from fi.gateway._fi import AsyncGateway, Gateway
from fi.gateway._utils import return_raw_request
from fi.gateway._version import futureagi_version

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
KEY = "sk-agentcc-unit-placeholder"
ORIGIN = "https://gateway.example.test/v1/"
MESSAGES = [{"role": "user", "content": "snowman ☃ and newline\n"}]
ENV_NAMES = (
    "FI_GATEWAY_API_KEY", "AGENTCC_API_KEY", "FI_GATEWAY_BASE_URL",
    "FI_GATEWAY_URL", "AGENTCC_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY",
)


@pytest.fixture(autouse=True)
def clean_gateway_env(monkeypatch):
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_helper_never_constructs_clients_resolves_dns_or_connects(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("raw inspection attempted network/client creation")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    for cls in (httpx.Client, httpx.AsyncClient):
        monkeypatch.setattr(cls, "__init__", forbidden)
        monkeypatch.setattr(cls, "send", forbidden)
        monkeypatch.setattr(cls, "request", forbidden)
    for origin in (None, ORIGIN, "http://127.0.0.1:8080"):
        result = return_raw_request(model="test", messages=MESSAGES, base_url=origin)
        assert result["method"] == "POST"
        if origin is None:
            assert result["url"] == "https://gateway.futureagi.com/v1/chat/completions"
        assert result["headers"]["Authorization"] == "Bearer [REDACTED]"
        assert json.loads(result["body_bytes"]) == result["body"]


INVALID_ORIGINS = [
    "http://gateway.example.test", "https://user:pass@gateway.example.test",
    "https://gateway.example.test/#fragment", "ftp://gateway.example.test",
    "https://gateway.example.test:invalid", "https://gateway.example.test\\other",
    "https://gateway.example.test/\npath", "https:///missing-host",
]


@pytest.mark.parametrize("origin", INVALID_ORIGINS)
@pytest.mark.parametrize("env_name", [None, "FI_GATEWAY_BASE_URL", "FI_GATEWAY_URL", "AGENTCC_BASE_URL"])
def test_helper_rejects_exactly_the_wrapper_origins(monkeypatch, origin, env_name):
    if env_name:
        monkeypatch.setenv(env_name, origin)
    settings = {"api_key": KEY, **({} if env_name else {"base_url": origin})}
    for wrapper in (Gateway, AsyncGateway):
        if origin.startswith("http://"):
            from fi.gateway._deprecation import AgentCCDeprecationWarning

            client = wrapper(**settings)
            assert client._base_url == origin
            with pytest.warns(AgentCCDeprecationWarning, match="sending gateway credentials in cleartext"):
                raw = return_raw_request(model="test", messages=[], **settings)
            assert raw["url"] == origin + "/v1/chat/completions"
            assert raw["headers"]["Authorization"] == f"Bearer {KEY}"
            continue
        with pytest.raises(AgentCCError) as wrapper_error:
            wrapper(**settings)
        with pytest.raises(AgentCCError) as helper_error:
            return_raw_request(model="test", messages=[], **settings)
        assert str(helper_error.value) == str(wrapper_error.value)


def test_env_resolution_and_explicit_precedence(monkeypatch):
    monkeypatch.setenv("FI_GATEWAY_API_KEY", KEY)
    monkeypatch.setenv("FI_GATEWAY_BASE_URL", ORIGIN)
    result = return_raw_request(model="test", messages=[])
    assert result["url"] == "https://gateway.example.test/v1/chat/completions"
    assert result["headers"]["Authorization"] == f"Bearer {KEY}"
    monkeypatch.setenv("FI_GATEWAY_BASE_URL", "http://unsafe.example.test")
    result = return_raw_request(model="test", messages=[], base_url=ORIGIN)
    assert result["url"].startswith("https://gateway.example.test/")


def test_platform_key_guard_is_not_bypassed(monkeypatch):
    monkeypatch.setenv("FI_API_KEY", "platform-unit-placeholder")
    for kwargs in (
        {"api_key": "platform-unit-placeholder"},
        {"api_key": KEY, "extra_headers": {"Authorization": "Bearer platform-unit-placeholder"}},
    ):
        with pytest.raises(AgentCCError):
            return_raw_request(model="test", messages=[], base_url=ORIGIN, **kwargs)


PARAMETERS = [
    {},
    {"temperature": 0, "top_p": NOT_GIVEN, "stop": None, "max_tokens": 5},
    {"session_id": "s", "trace_id": "t", "request_metadata": {"x": 1},
     "guardrail_policy": "policy", "request_timeout": 7, "cache_ttl": 13,
     "cache_namespace": "ns", "cache_force_refresh": False, "cache_control": "no-cache"},
    {"temperature": 0.8, "extra_body": {"temperature": 0, "custom": [1, "☃"]},
     "extra_headers": {"X-Test": "yes", "x-agentcc-trace-id": "override"}, "trace_id": "base"},
    {"properties": {"environment": "unit"}, "user_id": "user", "request_id": "request",
     "timeout": 2, "extra_headers": {"Accept-Encoding": "identity"}},
    {"stream": True, "stream_options": {"include_usage": True}, "extra_body": {"seed": 3}},
]


def capture_transport(seen, streaming):
    def handle(request):
        seen.append(request)
        if streaming:
            return httpx.Response(200, text="data: [DONE]\n\n", headers={"content-type": "text/event-stream"})
        return httpx.Response(200, json={
            "id": "c", "object": "chat.completion", "created": 0,
            "model": "test", "choices": [],
        })
    return httpx.MockTransport(handle)


def assert_parity(raw, request):
    assert raw["method"] == request.method
    assert raw["url"] == str(request.url)
    assert httpx.Headers(raw["headers"]).raw == request.headers.raw
    assert raw["body_bytes"] == request.content
    assert raw["body"] == json.loads(request.content)
    assert "extra_body" not in raw["body"]
    assert "extra_headers" not in raw["body"]
    assert "session_id" not in raw["body"]
    assert "guardrail_policy" not in raw["body"]
    assert "x-agentcc-sdk-version" in request.headers


@pytest.mark.parametrize("params", PARAMETERS)
def test_sync_wrapper_request_byte_parity(params):
    seen = []
    raw = return_raw_request(model="test", messages=MESSAGES, api_key=KEY, base_url=ORIGIN, **params)
    with httpx.Client(transport=capture_transport(seen, params.get("stream"))) as http:
        with Gateway(api_key=KEY, base_url=ORIGIN, http_client=http) as gateway:
            result = gateway.chat.completions.create(model="test", messages=MESSAGES, **params)
            if params.get("stream"):
                result.close()
    assert len(seen) == 1
    assert raw["headers"]["User-Agent"] == f"agentcc-python/{futureagi_version()}"
    assert seen[0].headers["user-agent"] == f"agentcc-python/{futureagi_version()}"
    assert seen[0].headers["x-agentcc-sdk-version"] == futureagi_version()
    assert_parity(raw, seen[0])


@pytest.mark.anyio
@pytest.mark.parametrize("params", PARAMETERS)
async def test_async_wrapper_request_byte_parity(params):
    seen = []
    raw = return_raw_request(model="test", messages=MESSAGES, api_key=KEY, base_url=ORIGIN, **params)
    async with httpx.AsyncClient(transport=capture_transport(seen, params.get("stream"))) as http:
        async with AsyncGateway(api_key=KEY, base_url=ORIGIN, http_client=http) as gateway:
            result = await gateway.chat.completions.create(model="test", messages=MESSAGES, **params)
            if params.get("stream"):
                await result.aclose()
    assert len(seen) == 1
    assert raw["headers"]["User-Agent"] == f"agentcc-python/{futureagi_version()}"
    assert seen[0].headers["user-agent"] == f"agentcc-python/{futureagi_version()}"
    assert seen[0].headers["x-agentcc-sdk-version"] == futureagi_version()
    assert_parity(raw, seen[0])
