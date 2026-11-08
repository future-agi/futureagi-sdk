"""Exercise real LangChain and LlamaIndex clients against MockAgentCC, not stubs of them."""

import asyncio
import json
from pathlib import Path
import socket

import pytest
from fi.gateway import AgentCCError
from pytest_socket import SocketConnectBlockedError

import langchain_chat
import llamaindex_chat


@pytest.mark.parametrize("example", [langchain_chat, llamaindex_chat])
@pytest.mark.parametrize("async_mode", [True, False], ids=["async", "sync"])
def test_framework_reaches_mock(gateway, example, async_mode):
    mock, requests = gateway
    answer = asyncio.run(example.ask("Hello")) if async_mode else example.ask_sync("Hello")
    assert answer == "Hello from the mock gateway."
    assert len(requests) == len(mock.chat.completions.calls) == 1
    path, raw_headers, body = requests[0]
    headers = {key.lower(): value for key, value in raw_headers.items()}
    assert path == "/v1/chat/completions"
    assert headers["authorization"] == "Bearer mock-personal-gateway-key"
    assert headers["x-agentcc-session-id"] == (
        "example-langchain" if example is langchain_chat else "example-llamaindex"
    )
    assert body["model"] == "example-model"
    assert body["messages"][-1] == {"role": "user", "content": "Hello"}
    assert not body.get("stream")
    assert "x-agentcc-config" not in headers


@pytest.mark.parametrize("example", [langchain_chat, llamaindex_chat])
def test_missing_gateway_key_never_uses_provider_key(gateway, monkeypatch, example):
    monkeypatch.delenv("FI_GATEWAY_API_KEY")
    with pytest.raises(AgentCCError):
        example.make_chat()
    assert gateway[1] == []


@pytest.mark.parametrize("example", [langchain_chat, llamaindex_chat])
def test_platform_key_pair_refused_before_network(gateway, monkeypatch, example):
    monkeypatch.setenv("FI_API_KEY", "mock-personal-gateway-key")
    monkeypatch.setenv("FI_SECRET_KEY", "mock-platform-secret")
    with pytest.raises(AgentCCError):
        example.make_chat()
    assert gateway[1] == []


def test_example_inventory_has_language_twins_or_explicit_absence():
    root = Path(__file__).resolve().parents[1]
    inventory = json.loads((root / "examples.json").read_text())
    assert inventory["availability"] == "source-preview-only"
    assert inventory["backendQualification"] == "not-evaluated"
    assert len(inventory["examples"]) == 5
    for example in inventory["examples"]:
        for language in ("python", "typescript"):
            entries = example[language]
            if entries == "NOT-OFFERED":
                assert example["reason"]
            else:
                assert entries
                for entry in entries:
                    assert (root / entry.split(":")[0]).is_file()


def test_external_socket_is_blocked():
    with socket.socket() as sock:
        with pytest.raises(SocketConnectBlockedError):
            sock.connect(("192.0.2.1", 443))
