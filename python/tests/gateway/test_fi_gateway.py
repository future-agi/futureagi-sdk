"""Tests for fi.gateway.Gateway / AsyncGateway: Future AGI env vars and defaults."""

from __future__ import annotations

import httpx
import pytest
import respx

from fi.gateway import AgentCC, AgentCCError, AsyncGateway, Gateway
from fi.gateway._fi import DEFAULT_GATEWAY_URL

COMPLETION = {
    "id": "chatcmpl-1",
    "object": "chat.completion",
    "created": 1,
    "model": "gpt-4o-mini",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
}


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("FI_GATEWAY_API_KEY", "FI_GATEWAY_URL", "AGENTCC_API_KEY", "AGENTCC_BASE_URL"):
        monkeypatch.delenv(name, raising=False)


def test_gateway_is_an_agentcc_client() -> None:
    assert issubclass(Gateway, AgentCC)


def test_defaults_to_hosted_gateway() -> None:
    gw = Gateway(api_key="sk-agentcc-x")
    assert gw._base_url == DEFAULT_GATEWAY_URL


def test_fi_env_vars_win_over_agentcc_ones(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FI_GATEWAY_API_KEY", "sk-agentcc-fi")
    monkeypatch.setenv("FI_GATEWAY_URL", "http://fi-gw/v1")
    monkeypatch.setenv("AGENTCC_API_KEY", "sk-agentcc-old")
    monkeypatch.setenv("AGENTCC_BASE_URL", "http://old-gw/v1")
    gw = Gateway()
    assert (gw._api_key, gw._base_url) == ("sk-agentcc-fi", "http://fi-gw")


def test_agentcc_env_vars_still_work(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTCC_API_KEY", "sk-agentcc-old")
    monkeypatch.setenv("AGENTCC_BASE_URL", "http://old-gw/v1")
    gw = Gateway()
    assert (gw._api_key, gw._base_url) == ("sk-agentcc-old", "http://old-gw")


@pytest.mark.parametrize("url", ["http://gw.test", "http://gw.test/", "http://gw.test/v1", "http://gw.test/v1/"])
def test_openai_style_v1_url_is_accepted(url: str) -> None:
    assert Gateway(api_key="sk-agentcc-x", base_url=url)._base_url == "http://gw.test"


def test_missing_key_is_a_clear_error() -> None:
    with pytest.raises(AgentCCError, match="api_key is required"):
        Gateway()


def test_agentcc_keeps_requiring_base_url() -> None:
    with pytest.raises(AgentCCError, match="base_url is required"):
        AgentCC(api_key="sk-agentcc-x")


@respx.mock
def test_chat_completion_goes_through_the_gateway() -> None:
    route = respx.post("http://gw.test/v1/chat/completions").mock(return_value=httpx.Response(200, json=COMPLETION))
    gw = Gateway(api_key="sk-agentcc-x", base_url="http://gw.test", session_id="s-1")
    reply = gw.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": "hello"}])
    assert reply.choices[0].message.content == "hi"
    sent = route.calls.last.request
    assert sent.headers["authorization"] == "Bearer sk-agentcc-x"
    assert sent.headers["x-agentcc-session-id"] == "s-1"


@respx.mock
async def test_async_gateway() -> None:
    respx.post("http://gw.test/v1/chat/completions").mock(return_value=httpx.Response(200, json=COMPLETION))
    gw = AsyncGateway(api_key="sk-agentcc-x", base_url="http://gw.test")
    reply = await gw.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": "hello"}])
    assert reply.choices[0].message.content == "hi"
    await gw.aclose()
