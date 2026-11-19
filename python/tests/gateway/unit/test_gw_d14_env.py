"""D-14: ``FI_GATEWAY_*`` names, read before the ``AGENTCC_*`` ones, and the FI-key guard.

Key ``api_key=`` > ``FI_GATEWAY_API_KEY`` > ``AGENTCC_API_KEY``; base URL
``base_url=`` > ``FI_GATEWAY_BASE_URL`` > ``AGENTCC_BASE_URL``; no hosted fallback; the FI
key pair is never read as a key and never sent.
"""

from __future__ import annotations

import logging
import warnings

import httpx
import pytest

from ._published_helpers import wire_snapshot
from fi.gateway import (
    AgentCC,
    AgentCCError,
    AsyncAgentCC,
    check_valid_key,
    health_check,
)

GW = "http://127.0.0.1:8090"
FI_KEY = "fi-api-key-value-0123456789"
FI_SECRET = "fi-secret-key-value-0123456789"
COMPLETION = {
    "id": "c",
    "object": "chat.completion",
    "created": 1,
    "model": "m",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}}],
}
ALL_PREFIXES = ("AGENTCC_", "FI_", "OPENAI_")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    for name in list(os.environ):
        if name.startswith(ALL_PREFIXES):
            monkeypatch.delenv(name)


def _client(seen: list[httpx.Request], **kwargs: object) -> AgentCC:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(wire_snapshot(request))
        return httpx.Response(200, json=COMPLETION)

    return AgentCC(
        http_client=httpx.Client(transport=httpx.MockTransport(handler)), **kwargs
    )


def _sent_key(**kwargs: object) -> str:
    seen: list[httpx.Request] = []
    _client(seen, **kwargs).chat.completions.create(model="m", messages=[])
    return seen[0].headers["authorization"]


# -- order -------------------------------------------------------------------


@pytest.mark.parametrize(
    "arg, fi_gateway, agentcc, expected",
    [
        ("arg-key", "fi-gw-key", "acc-key", "arg-key"),
        (None, "fi-gw-key", "acc-key", "fi-gw-key"),
        (None, None, "acc-key", "acc-key"),
        (
            "",
            "fi-gw-key",
            None,
            "fi-gw-key",
        ),  # an empty argument falls through (1.x `or`)
        (None, "", "acc-key", "acc-key"),  # so does an empty variable
    ],
)
def test_key_order(monkeypatch, arg, fi_gateway, agentcc, expected) -> None:
    if fi_gateway is not None:
        monkeypatch.setenv("FI_GATEWAY_API_KEY", fi_gateway)
    if agentcc is not None:
        monkeypatch.setenv("AGENTCC_API_KEY", agentcc)
    assert _sent_key(api_key=arg, base_url=GW) == f"Bearer {expected}"


@pytest.mark.parametrize(
    "arg, fi_gateway, agentcc, expected",
    [
        (
            "http://127.0.0.1:1",
            "http://127.0.0.1:2",
            "http://127.0.0.1:3",
            "http://127.0.0.1:1",
        ),
        (None, "http://127.0.0.1:2/v1", "http://127.0.0.1:3", "http://127.0.0.1:2"),
        (None, None, "http://127.0.0.1:3", "http://127.0.0.1:3"),
        ("", "http://127.0.0.1:2", None, "http://127.0.0.1:2"),
    ],
)
def test_base_url_order(monkeypatch, arg, fi_gateway, agentcc, expected) -> None:
    if fi_gateway is not None:
        monkeypatch.setenv("FI_GATEWAY_BASE_URL", fi_gateway)
    if agentcc is not None:
        monkeypatch.setenv("AGENTCC_BASE_URL", agentcc)
    seen: list[httpx.Request] = []
    _client(seen, api_key="k", base_url=arg).chat.completions.create(
        model="m", messages=[]
    )
    assert str(seen[0].url) == f"{expected}/v1/chat/completions"


# -- missing values ----------------------------------------------------------


def test_a_missing_key_names_the_variable_and_says_what_key_it_is(monkeypatch) -> None:
    monkeypatch.setenv("FI_API_KEY", FI_KEY)  # never read as the gateway key
    with pytest.raises(AgentCCError) as info:
        AgentCC(base_url=GW)
    message = str(info.value)
    assert "FI_GATEWAY_API_KEY" in message
    assert "virtual key" in message and "not your FI_API_KEY" in message
    assert "Keys page" in message
    assert FI_KEY not in message


def test_a_missing_base_url_raises_and_there_is_no_hosted_default() -> None:
    with pytest.raises(AgentCCError) as info:
        AgentCC(api_key="k")
    assert "FI_GATEWAY_BASE_URL" in str(info.value)
    with pytest.raises(AgentCCError):
        AsyncAgentCC(api_key="k")


# -- both names set ----------------------------------------------------------


def test_both_names_differ_fi_gateway_wins_with_one_log_line_per_client(
    monkeypatch, caplog
) -> None:
    monkeypatch.setenv("FI_GATEWAY_API_KEY", "fi-gw-key-secret-value")
    monkeypatch.setenv("AGENTCC_API_KEY", "acc-key-secret-value")
    with caplog.at_level(
        logging.WARNING, logger="fi.gateway"
    ), warnings.catch_warnings():
        warnings.simplefilter(
            "error"
        )  # a -W error suite keeps working: no warning is raised
        assert _sent_key(base_url=GW) == "Bearer fi-gw-key-secret-value"
        assert _sent_key(base_url=GW) == "Bearer fi-gw-key-secret-value"
    lines = [r for r in caplog.records if r.name == "fi.gateway"]
    assert len(lines) == 2  # one per client; no process-wide once-flag
    text = lines[0].getMessage()
    assert "FI_GATEWAY_API_KEY" in text and "AGENTCC_API_KEY" in text
    assert "secret-value" not in text


def test_both_names_equal_logs_nothing(monkeypatch, caplog) -> None:
    monkeypatch.setenv("FI_GATEWAY_BASE_URL", GW)
    monkeypatch.setenv("AGENTCC_BASE_URL", GW)
    monkeypatch.setenv("FI_GATEWAY_API_KEY", "k")
    monkeypatch.setenv("AGENTCC_API_KEY", "k")
    with caplog.at_level(logging.DEBUG, logger="fi.gateway"):
        assert _sent_key() == "Bearer k"
    assert [r for r in caplog.records if r.name == "fi.gateway"] == []


# -- the guard ---------------------------------------------------------------


@pytest.mark.parametrize(
    "name, value", [("FI_API_KEY", FI_KEY), ("FI_SECRET_KEY", FI_SECRET)]
)
@pytest.mark.parametrize(
    "source", ["argument", "FI_GATEWAY_API_KEY", "AGENTCC_API_KEY"]
)
def test_the_fi_key_pair_is_refused_from_any_source(
    monkeypatch, name, value, source
) -> None:
    monkeypatch.setenv(name, value)
    kwargs: dict[str, object] = {"base_url": GW}
    if source == "argument":
        kwargs["api_key"] = value
    else:
        monkeypatch.setenv(source, value)
    with pytest.raises(AgentCCError) as info:
        AgentCC(**kwargs)
    assert name in str(info.value) and value not in str(info.value)
    with pytest.raises(AgentCCError):
        AsyncAgentCC(**kwargs)


def test_the_helpers_refuse_it_without_sending_anything(monkeypatch) -> None:
    monkeypatch.setenv("FI_API_KEY", FI_KEY)
    sent: list[str] = []
    monkeypatch.setattr(
        "fi.gateway._utils.httpx.get", lambda url, **kw: sent.append(url)
    )
    result = health_check(api_key=FI_KEY, base_url=GW)
    assert result["status"] == "error" and "FI_API_KEY" in result["error"]
    with pytest.raises(AgentCCError):
        check_valid_key(FI_KEY, GW)
    assert sent == []


def test_a_different_key_with_the_fi_pair_set_is_fine(monkeypatch) -> None:
    monkeypatch.setenv("FI_API_KEY", FI_KEY)
    monkeypatch.setenv("FI_SECRET_KEY", FI_SECRET)
    assert (
        _sent_key(api_key="gateway-virtual-key", base_url=GW)
        == "Bearer gateway-virtual-key"
    )


# -- nothing else leaves -----------------------------------------------------

FORBIDDEN = (
    "x-api-key",
    "x-secret-key",
    "x-organization-id",
    "openai-organization",
    "openai-project",
)
FORBIDDEN_PREFIXES = ("x-workspace-", "x-omega-")


def _poison_env(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    values = {
        "FI_API_KEY": FI_KEY,
        "FI_SECRET_KEY": FI_SECRET,
        "FI_PLATFORM_TOKEN": "fi-platform-token-0123456789",
        "FI_BASE_URL": "http://127.0.0.1:7001",
        "FI_PLATFORM_BASE_URL": "http://127.0.0.1:7002",
        "FI_WORKSPACE_ID": "ws-0123456789",
        "FI_ORGANIZATION_ID": "org-0123456789",
        "OPENAI_API_KEY": "sk-openai-0123456789",
        "OPENAI_ORG_ID": "org-openai-0123456789",
        "OPENAI_ORGANIZATION": "org-openai-0123456789",
        "OPENAI_PROJECT_ID": "proj-openai-0123456789",
        "OPENAI_BASE_URL": "http://127.0.0.1:7003",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    return values


def test_with_every_fi_and_openai_variable_set_only_the_gateway_key_leaves(
    monkeypatch,
) -> None:
    values = _poison_env(monkeypatch)
    monkeypatch.setenv("FI_GATEWAY_API_KEY", "gateway-virtual-key")
    monkeypatch.setenv("FI_GATEWAY_BASE_URL", GW)
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(wire_snapshot(request))
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"object": "list", "data": []})
        if request.url.path == "/v1/embeddings":
            return httpx.Response(
                200,
                json={
                    "object": "list",
                    "model": "e",
                    "data": [],
                    "usage": {
                        "prompt_tokens": 1,
                        "completion_tokens": 0,
                        "total_tokens": 1,
                    },
                },
            )
        return httpx.Response(200, json=COMPLETION)

    client = AgentCC(http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    client.chat.completions.create(
        model="m", messages=[], session_id="s1", properties={"team": "a"}
    )
    client.embeddings.create(model="e", input="x")
    client.models.list()
    with client.session(name="checkout"):
        client.chat.completions.create(model="m", messages=[])
    assert len(seen) == 4
    for request in seen:
        assert request.url.host == "127.0.0.1" and request.url.port == 8090
        assert request.headers["authorization"] == "Bearer gateway-virtual-key"
        for name, value in request.headers.items():
            assert name.lower() not in FORBIDDEN, name
            assert not name.lower().startswith(FORBIDDEN_PREFIXES), name
            for secret in values.values():
                assert secret not in value, (name, secret)
