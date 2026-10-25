"""Tests for the testing utilities module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from fi.gateway.testing import (
    Interaction,
    MockAgentCC,
    RecordingAgentCC,
    assert_completion_has_content,
    assert_agentcc_metadata,
    make_completion,
    make_message,
    make_agentcc_metadata,
    make_tool_call,
    make_usage,
    mock_completion,
    mock_error,
)
from fi.gateway.types.chat.chat_completion import ChatCompletion

# --- Fixture tests ---

def test_make_usage_defaults() -> None:
    u = make_usage()
    assert u.prompt_tokens == 10
    assert u.completion_tokens == 20
    assert u.total_tokens == 30


def test_make_usage_custom() -> None:
    u = make_usage(prompt_tokens=5, completion_tokens=15)
    assert u.total_tokens == 20


def test_make_agentcc_metadata_defaults() -> None:
    m = make_agentcc_metadata()
    assert m.request_id == "req-test-001"
    assert m.provider == "openai"
    assert m.latency_ms == 100


def test_make_agentcc_metadata_custom() -> None:
    m = make_agentcc_metadata(provider="anthropic", cost=0.05)
    assert m.provider == "anthropic"
    assert m.cost == 0.05


def test_make_message_defaults() -> None:
    msg = make_message()
    assert msg.role == "assistant"
    assert msg.content == "Hello!"


def test_make_tool_call() -> None:
    tc = make_tool_call(name="search", arguments='{"q":"test"}')
    assert tc.function.name == "search"
    assert tc.type == "function"


def test_make_completion_defaults() -> None:
    comp = make_completion()
    assert isinstance(comp, ChatCompletion)
    assert comp.choices[0].message.content == "Hello!"
    assert comp.usage is not None
    assert comp.usage.total_tokens == 30


def test_make_completion_with_agentcc() -> None:
    meta = make_agentcc_metadata(provider="azure")
    comp = make_completion(agentcc=meta)
    assert comp.agentcc is not None
    assert comp.agentcc.provider == "azure"


def test_make_completion_with_tool_calls() -> None:
    tc = make_tool_call()
    comp = make_completion(tool_calls=[tc])
    assert comp.choices[0].message.tool_calls is not None
    assert len(comp.choices[0].message.tool_calls) == 1


# --- mock_completion / mock_error tests ---

def test_mock_completion_simple() -> None:
    comp = mock_completion("Hi there!", provider="anthropic")
    assert comp.choices[0].message.content == "Hi there!"
    assert comp.agentcc is not None
    assert comp.agentcc.provider == "anthropic"


def test_mock_error() -> None:
    err = mock_error(429, "Rate limited")
    from fi.gateway._exceptions import RateLimitError
    assert isinstance(err, RateLimitError)
    assert err.status_code == 429


# --- MockAgentCC tests ---

def test_mock_agentcc_default_response() -> None:
    client = MockAgentCC()
    result = client.chat.completions.create(model="gpt-4o", messages=[])
    assert isinstance(result, ChatCompletion)
    assert result.choices[0].message.content == "Hello!"


def test_mock_agentcc_custom_response() -> None:
    client = MockAgentCC()
    client.chat.completions.respond_with(mock_completion("Custom!"))
    result = client.chat.completions.create(model="gpt-4o", messages=[])
    assert result.choices[0].message.content == "Custom!"


def test_mock_agentcc_error_response() -> None:
    client = MockAgentCC()
    err = mock_error(500, "Server error")
    client.chat.completions.respond_with(err)
    with pytest.raises(Exception, match="Server error"):
        client.chat.completions.create(model="gpt-4o", messages=[])


def test_mock_agentcc_tracks_calls() -> None:
    client = MockAgentCC()
    client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": "Hi"}])
    assert len(client.chat.completions.calls) == 1
    assert client.chat.completions.calls[0]["model"] == "gpt-4o"


def test_mock_agentcc_context_manager() -> None:
    with MockAgentCC() as client:
        result = client.chat.completions.create(model="gpt-4o", messages=[])
    assert result.choices[0].message.content == "Hello!"


def test_mock_agentcc_multiple_responses() -> None:
    client = MockAgentCC()
    client.chat.completions.respond_with(mock_completion("First"))
    client.chat.completions.respond_with(mock_completion("Second"))
    r1 = client.chat.completions.create(model="gpt-4o", messages=[])
    r2 = client.chat.completions.create(model="gpt-4o", messages=[])
    assert r1.choices[0].message.content == "First"
    assert r2.choices[0].message.content == "Second"


# --- Assertion tests ---

def test_assert_completion_has_content_pass() -> None:
    comp = mock_completion("Hello world")
    assert_completion_has_content(comp, "Hello")


def test_assert_completion_has_content_fail() -> None:
    comp = mock_completion("Hello")
    with pytest.raises(AssertionError):
        assert_completion_has_content(comp, "Goodbye")


def test_assert_agentcc_metadata_pass() -> None:
    comp = mock_completion(provider="openai", cost=0.01)
    assert_agentcc_metadata(comp, provider="openai", cost=0.01)


def test_assert_agentcc_metadata_fail() -> None:
    comp = mock_completion(provider="openai")
    with pytest.raises(AssertionError):
        assert_agentcc_metadata(comp, provider="anthropic")


# --- Recorder tests ---

def test_interaction_creation() -> None:
    i = Interaction(request={"model": "gpt-4o"}, response={"id": "chatcmpl-1"})
    assert i.request["model"] == "gpt-4o"


def test_recorder_save_load() -> None:
    interactions = [
        Interaction(request={"model": "gpt-4o"}, response={"id": "chatcmpl-1"}),
        Interaction(request={"model": "claude"}, response={"id": "chatcmpl-2"}),
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        path = f.name

    # Save manually
    from dataclasses import asdict
    Path(path).write_text(json.dumps([asdict(i) for i in interactions], indent=2))

    # Load
    loaded = RecordingAgentCC.load(path)
    assert len(loaded) == 2
    assert loaded[0].request["model"] == "gpt-4o"
    assert loaded[1].request["model"] == "claude"

    # Cleanup
    Path(path).unlink()
