"""Tests for the OpenAI compatibility layer."""

from __future__ import annotations

from fi.gateway._compat import patch_openai


def test_patch_openai_returns_agentcc() -> None:
    from fi.gateway._client import AgentCC

    client = patch_openai(api_key="sk-test", base_url="http://localhost:8080")
    assert isinstance(client, AgentCC)


def test_patch_openai_ignores_existing_client() -> None:
    from fi.gateway._client import AgentCC

    fake_openai_client = object()
    client = patch_openai(fake_openai_client, api_key="sk-test", base_url="http://localhost:8080")
    assert isinstance(client, AgentCC)


def test_patch_openai_has_chat_completions() -> None:
    client = patch_openai(api_key="sk-test", base_url="http://localhost:8080")
    assert hasattr(client, "chat")
    assert hasattr(client.chat, "completions")


def test_patch_openai_passes_kwargs() -> None:
    client = patch_openai(api_key="sk-test", base_url="http://localhost:8080", max_retries=5)
    assert client._max_retries == 5
