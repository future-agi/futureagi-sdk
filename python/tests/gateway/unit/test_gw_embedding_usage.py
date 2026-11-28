"""``embeddings.create`` reads the usage an embeddings answer carries.

The gateway returns embeddings usage with ``prompt_tokens`` and ``total_tokens``
and may omit ``completion_tokens``. ``EmbeddingResponse.usage`` is an
``EmbeddingUsage``, a subclass of ``Usage`` that defaults ``completion_tokens``
to 0.
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
HEADERS = {"x-agentcc-request-id": "01ARZ3NDEKTSV4RRFFQ69G5FAV", "x-agentcc-cost": "0.001"}


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
    assert result.agentcc is not None and result.agentcc.request_id == "01ARZ3NDEKTSV4RRFFQ69G5FAV"


def test_an_answer_that_carries_completion_tokens_parses() -> None:
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
        "total_tokens",
    }
    assert Usage.model_json_schema()["properties"]["completion_tokens"]["default"] == 0
    assert Usage(prompt_tokens=2, total_tokens=2).completion_tokens == 0


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
