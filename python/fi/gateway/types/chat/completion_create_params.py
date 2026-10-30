"""CompletionCreateParams — input TypedDict for chat completion requests."""

from __future__ import annotations

from typing import Any

from typing_extensions import Required, TypedDict

from fi.gateway.types.chat.chat_completion_message import ChatCompletionMessageParam


class StreamOptions(TypedDict, total=False):
    include_usage: bool


class CompletionCreateParams(TypedDict, total=False):
    """Parameters for creating a chat completion.

    Standard OpenAI-compatible params plus AgentCC-specific extensions.
    """

    # --- Standard OpenAI params ---
    model: Required[str]
    messages: Required[list[ChatCompletionMessageParam]]
    temperature: float | None
    top_p: float | None
    n: int | None
    stream: bool | None
    stream_options: StreamOptions | None
    stop: str | list[str] | None
    max_tokens: int | None
    max_completion_tokens: int | None
    presence_penalty: float | None
    frequency_penalty: float | None
    logit_bias: dict[str, int] | None
    logprobs: bool | None
    top_logprobs: int | None
    user: str | None
    seed: int | None
    tools: list[dict[str, Any]] | None
    tool_choice: str | dict[str, Any] | None
    response_format: dict[str, Any] | None
    service_tier: str | None

    # --- AgentCC-specific params ---
    session_id: str | None
    trace_id: str | None
    request_metadata: dict[str, str] | None
    request_timeout: int | None
    cache_ttl: str | None
    cache_namespace: str | None
    cache_force_refresh: bool | None
    cache_control: str | None
    guardrail_policy: str | None
    extra_headers: dict[str, str] | None
    extra_body: dict[str, Any] | None
