"""Custom assertion helpers for AgentCC responses."""

from __future__ import annotations

from typing import Any


def assert_completion_has_content(completion: Any, expected: str) -> None:
    """Assert that the completion's first choice message contains expected content."""
    actual = completion.choices[0].message.content
    assert actual is not None, "Completion message content is None"
    assert expected in actual, f"Expected '{expected}' in content, got: '{actual}'"


def assert_completion_valid(response: Any) -> None:
    """Assert a ChatCompletion response has valid structure."""
    assert response is not None, "Response is None"
    assert hasattr(response, "id"), "Response missing 'id'"
    assert hasattr(response, "choices"), "Response missing 'choices'"
    assert len(response.choices) > 0, "Response has no choices"
    assert response.choices[0].message is not None, "First choice has no message"
    assert response.choices[0].message.content is not None, "Message content is None"


def assert_stream_valid(chunks: list[Any]) -> None:
    """Assert a list of stream chunks is valid."""
    assert len(chunks) > 0, "No chunks received"
    last = chunks[-1]
    assert hasattr(last, "choices"), "Last chunk missing 'choices'"
    if last.choices:
        assert last.choices[0].finish_reason is not None, "Last chunk missing finish_reason"


def assert_agentcc_metadata(
    completion: Any,
    *,
    provider: str | None = None,
    cost: float | None = None,
    cache_status: str | None = None,
) -> None:
    """Assert AgentCCMetadata fields on a completion."""
    meta = getattr(completion, "agentcc", None)
    assert meta is not None, "Completion has no .agentcc metadata"
    if provider is not None:
        assert meta.provider == provider, f"Expected provider={provider}, got {meta.provider}"
    if cost is not None:
        assert meta.cost == cost, f"Expected cost={cost}, got {meta.cost}"
    if cache_status is not None:
        assert meta.cache_status == cache_status, f"Expected cache_status={cache_status}, got {meta.cache_status}"


def assert_usage_valid(response: Any) -> None:
    """Assert token usage is present and valid."""
    assert hasattr(response, "usage"), "Response missing 'usage'"
    assert response.usage is not None, "Usage is None"
    assert response.usage.total_tokens > 0, "total_tokens is 0"


def assert_cost_tracked(response: Any) -> None:
    """Assert cost was tracked in AgentCC metadata."""
    assert hasattr(response, "agentcc"), "Response missing 'agentcc' metadata"
    if response.agentcc:
        assert response.agentcc.cost is not None, "Cost not tracked"


def assert_guardrail_blocked(exc: Any, guardrail_name: str | None = None) -> None:
    """Assert that an exception is a guardrail block."""
    from fi.gateway._exceptions import GuardrailBlockedError
    assert isinstance(exc, GuardrailBlockedError), f"Expected GuardrailBlockedError, got {type(exc).__name__}"
    if guardrail_name is not None:
        assert exc.guardrail_name == guardrail_name, f"Expected guardrail_name={guardrail_name}, got {exc.guardrail_name}"
