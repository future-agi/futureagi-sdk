"""Tests for utility features -- token counting, cost estimation, model info, stream_chunk_builder."""

from __future__ import annotations


def test_model_info_gpt4o():
    from fi.gateway._models_info import get_model_info

    info = get_model_info("gpt-4o")
    assert info is not None
    assert info.max_tokens == 128000
    assert info.input_cost_per_token > 0
    assert info.supports_vision is True
    assert info.supports_function_calling is True


def test_model_info_prefix_match():
    from fi.gateway._models_info import get_model_info

    info = get_model_info("gpt-4o-2024-08-06")
    assert info is not None
    assert info.max_tokens == 128000


def test_model_info_unknown():
    from fi.gateway._models_info import get_model_info

    assert get_model_info("unknown-model-xyz") is None


def test_model_info_claude():
    from fi.gateway._models_info import get_model_info

    info = get_model_info("claude-sonnet-4-20250514")
    assert info is not None
    assert info.max_tokens == 200000


def test_token_counter_text():
    from fi.gateway._tokens import token_counter

    count = token_counter("gpt-4o", text="Hello, world!")
    assert count > 0


def test_token_counter_messages():
    from fi.gateway._tokens import token_counter

    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello!"},
    ]
    count = token_counter("gpt-4o", messages=messages)
    assert count > 0


def test_token_counter_empty():
    from fi.gateway._tokens import token_counter

    assert token_counter("gpt-4o") == 0


def test_get_max_tokens():
    from fi.gateway._tokens import get_max_tokens

    assert get_max_tokens("gpt-4o") == 128000
    assert get_max_tokens("unknown") is None


def test_get_max_output_tokens():
    from fi.gateway._tokens import get_max_output_tokens

    assert get_max_output_tokens("gpt-4o") == 16384
    assert get_max_output_tokens("unknown") is None


def test_completion_cost():
    from fi.gateway._tokens import completion_cost

    cost = completion_cost("gpt-4o", prompt_tokens=1000, completion_tokens=500)
    assert cost is not None
    assert cost > 0
    expected = 1000 * 2.5e-6 + 500 * 10e-6
    assert abs(cost - expected) < 1e-10


def test_completion_cost_unknown_model():
    from fi.gateway._tokens import completion_cost

    assert completion_cost("unknown-model", prompt_tokens=100, completion_tokens=50) is None


def test_completion_cost_from_response():
    from unittest.mock import MagicMock

    from fi.gateway._tokens import completion_cost_from_response

    # With gateway cost
    resp = MagicMock()
    resp.agentcc.cost = 0.05
    assert completion_cost_from_response(resp) == 0.05

    # Without gateway cost, fallback to estimation
    resp2 = MagicMock()
    resp2.agentcc.cost = None
    resp2.model = "gpt-4o"
    resp2.usage.prompt_tokens = 1000
    resp2.usage.completion_tokens = 500
    cost = completion_cost_from_response(resp2)
    assert cost is not None
    assert cost > 0


def test_stream_chunk_builder():
    from fi.gateway._streaming import stream_chunk_builder
    from fi.gateway.types.chat.chat_completion_chunk import ChatCompletionChunk, Delta, StreamChoice

    chunks = [
        ChatCompletionChunk(
            id="c1",
            object="chat.completion.chunk",
            created=1,
            model="gpt-4o",
            choices=[StreamChoice(index=0, delta=Delta(role="assistant"))],
        ),
        ChatCompletionChunk(
            id="c1",
            object="chat.completion.chunk",
            created=1,
            model="gpt-4o",
            choices=[StreamChoice(index=0, delta=Delta(content="Hello"))],
        ),
        ChatCompletionChunk(
            id="c1",
            object="chat.completion.chunk",
            created=1,
            model="gpt-4o",
            choices=[StreamChoice(index=0, delta=Delta(content=" world"), finish_reason="stop")],
        ),
    ]
    result = stream_chunk_builder(chunks)
    assert result.choices[0].message.content == "Hello world"
    assert result.choices[0].finish_reason == "stop"


def test_lazy_imports_from_agentcc():
    """Verify utilities are accessible via agentcc module."""
    import fi.gateway as agentcc

    assert callable(agentcc.token_counter)
    assert callable(agentcc.get_max_tokens)
    assert callable(agentcc.completion_cost)
    assert callable(agentcc.stream_chunk_builder)
    assert agentcc.get_model_info("gpt-4o") is not None
