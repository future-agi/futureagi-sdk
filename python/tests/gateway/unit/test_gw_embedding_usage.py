"""``embeddings.create`` reads the usage an embeddings answer carries.

An OpenAI-shaped embeddings answer, which is what the gateway returns, has ``usage:
{"prompt_tokens", "total_tokens"}`` and no ``completion_tokens``. agentcc 1.x typed it
as the chat ``Usage``, which requires ``completion_tokens``, so every such answer
raised a bare pydantic ``ValidationError``. ``EmbeddingResponse.usage`` is now an
``EmbeddingUsage``: ``completion_tokens`` defaults to 0 and it is still a ``Usage``.
"""

from __future__ import annotations

from typing import Any

import httpx

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway.types import EmbeddingResponse, EmbeddingUsage, Usage

GW = "http://127.0.0.1:8090"
DATA = [{"object": "embedding", "index": 0, "embedding": [0.25, -0.5, 0.125]}]
OPENAI_SHAPED = {
    "object": "list",
    "data": DATA,
    "model": "text-embedding-3-small",
    "usage": {"prompt_tokens": 2, "total_tokens": 2},
}
WITH_COMPLETION_TOKENS = {
    **OPENAI_SHAPED,
    "usage": {"prompt_tokens": 2, "completion_tokens": 0, "total_tokens": 2},
}
HEADERS = {"x-agentcc-request-id": "req-e", "x-agentcc-cost": "0.001"}


def _sync(body: dict[str, Any]) -> AgentCC:
    return AgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=body, headers=HEADERS)
            )
        ),
    )


def test_an_openai_shaped_answer_parses() -> None:
    result = _sync(OPENAI_SHAPED).embeddings.create(model="e", input="hi")
    assert isinstance(result, EmbeddingResponse)
    assert result.data[0].embedding == [0.25, -0.5, 0.125]
    assert isinstance(result.usage, EmbeddingUsage)
    assert isinstance(result.usage, Usage)
    assert (
        result.usage.prompt_tokens,
        result.usage.completion_tokens,
        result.usage.total_tokens,
    ) == (2, 0, 2)
    assert result.agentcc is not None and result.agentcc.request_id == "req-e"


def test_an_answer_that_carries_completion_tokens_still_parses() -> None:
    result = _sync(WITH_COMPLETION_TOKENS).embeddings.create(model="e", input="hi")
    assert result.usage is not None and result.usage.completion_tokens == 0


def test_an_answer_without_usage_and_extra_usage_fields() -> None:
    no_usage = {k: v for k, v in OPENAI_SHAPED.items() if k != "usage"}
    assert _sync(no_usage).embeddings.create(model="e", input="hi").usage is None
    extra = {
        **OPENAI_SHAPED,
        "usage": {
            "prompt_tokens": 2,
            "total_tokens": 2,
            "prompt_tokens_details": {"cached_tokens": 1},
            "cost": 0.5,
        },
    }
    usage = _sync(extra).embeddings.create(model="e", input="hi").usage
    assert usage is not None
    assert usage.prompt_tokens_details == {"cached_tokens": 1}
    assert usage.model_extra == {"cost": 0.5}


def test_the_schema_keeps_the_other_usage_fields_required() -> None:
    schema = EmbeddingUsage.model_json_schema()
    assert set(schema["required"]) == {"prompt_tokens", "total_tokens"}
    assert schema["properties"]["completion_tokens"]["default"] == 0
    assert set(Usage.model_json_schema()["required"]) == {
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
    }


async def test_the_async_client_parses_it_too() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=OPENAI_SHAPED, headers=HEADERS)

    client = AsyncAgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    result = await client.embeddings.create(model="e", input=["a", "b"])
    assert isinstance(result.usage, EmbeddingUsage)
    assert result.usage.completion_tokens == 0
    assert client.current_cost == 0.001
