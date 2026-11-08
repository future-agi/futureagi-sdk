"""Tests for data-plane resources — Models, Batches."""

from __future__ import annotations

import pytest
import respx

from fi.gateway._client import AgentCC, AsyncAgentCC

# --- Response fixtures ---

MODELS_LIST_RESPONSE = {
    "object": "list",
    "data": [
        {
            "id": "gpt-4o",
            "object": "model",
            "created": 1700000000,
            "owned_by": "openai",
        },
        {
            "id": "claude-3-opus",
            "object": "model",
            "created": 1700000001,
            "owned_by": "anthropic",
        },
    ],
}

MODEL_RESPONSE = {
    "id": "gpt-4o",
    "object": "model",
    "created": 1700000000,
    "owned_by": "openai",
}

BATCH_CREATE_RESPONSE = {
    "batch_id": "batch-001",
    "status": "queued",
    "total": 3,
    "max_concurrency": 5,
    "created_at": "2026-01-01T00:00:00Z",
}

BATCH_COMPLETED_RESPONSE = {
    "batch_id": "batch-001",
    "status": "completed",
    "total": 3,
    "results": [{"id": "r1"}, {"id": "r2"}, {"id": "r3"}],
    "summary": {"succeeded": 3, "failed": 0},
}


class TestPropertyAccess:
    def test_models_property(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert type(client.models).__qualname__ == "Models"

    def test_models_cached(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert client.models is client.models

    def test_async_models_property(self) -> None:
        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert type(client.models).__qualname__ == "AsyncModels"


class TestModels:
    @pytest.mark.filterwarnings("default:^futureagi:fi.gateway._deprecation.AgentCCDeprecationWarning")
    @respx.mock
    def test_list_models(self) -> None:
        respx.get("http://gateway.test/v1/models").respond(
            200, json=MODELS_LIST_RESPONSE
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.models.list()
        assert type(result).__qualname__ == "ModelList"
        assert len(result.data) == 2
        assert result.data[0].id == "gpt-4o"

    @pytest.mark.filterwarnings("default:^futureagi:fi.gateway._deprecation.AgentCCDeprecationWarning")
    @respx.mock
    def test_retrieve_model(self) -> None:
        respx.get("http://gateway.test/v1/models/gpt-4o").respond(
            200, json=MODEL_RESPONSE
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.models.retrieve("gpt-4o")
        assert type(result).__qualname__ == "Model"
        assert result.id == "gpt-4o"


class TestAsyncModels:
    @pytest.mark.filterwarnings("default:^futureagi:fi.gateway._deprecation.AgentCCDeprecationWarning")
    @respx.mock
    @pytest.mark.anyio
    async def test_async_list_models(self) -> None:
        respx.get("http://gateway.test/v1/models").respond(
            200, json=MODELS_LIST_RESPONSE
        )
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = await client.models.list()
        assert len(result.data) == 2

    @pytest.mark.filterwarnings("default:^futureagi:fi.gateway._deprecation.AgentCCDeprecationWarning")
    @respx.mock
    @pytest.mark.anyio
    async def test_async_retrieve_model(self) -> None:
        respx.get("http://gateway.test/v1/models/gpt-4o").respond(
            200, json=MODEL_RESPONSE
        )
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = await client.models.retrieve("gpt-4o")
        assert result.id == "gpt-4o"
