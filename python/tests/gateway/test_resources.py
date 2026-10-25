"""Tests for data-plane resources — Models, Batches."""

from __future__ import annotations

import pytest
import respx

from fi.gateway._client import AsyncAgentCC, AgentCC

# --- Response fixtures ---

MODELS_LIST_RESPONSE = {
    "object": "list",
    "data": [
        {"id": "gpt-4o", "object": "model", "created": 1700000000, "owned_by": "openai"},
        {"id": "claude-3-opus", "object": "model", "created": 1700000001, "owned_by": "anthropic"},
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

    def test_batches_property(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert type(client.batches).__qualname__ == "Batches"

    def test_async_models_property(self) -> None:
        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert type(client.models).__qualname__ == "AsyncModels"

    def test_async_batches_property(self) -> None:
        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert type(client.batches).__qualname__ == "AsyncBatches"


class TestModels:
    @respx.mock
    def test_list_models(self) -> None:
        respx.get("http://gateway.test/v1/models").respond(200, json=MODELS_LIST_RESPONSE)
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.models.list()
        assert type(result).__qualname__ == "ModelList"
        assert len(result.data) == 2
        assert result.data[0].id == "gpt-4o"

    @respx.mock
    def test_retrieve_model(self) -> None:
        respx.get("http://gateway.test/v1/models/gpt-4o").respond(200, json=MODEL_RESPONSE)
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.models.retrieve("gpt-4o")
        assert type(result).__qualname__ == "Model"
        assert result.id == "gpt-4o"


class TestBatches:
    @respx.mock
    def test_create_batch(self) -> None:
        respx.post("http://gateway.test/v1/batches").respond(200, json=BATCH_CREATE_RESPONSE)
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.batches.create(
            requests=[{"model": "gpt-4o", "messages": [{"role": "user", "content": "Hi"}]}],
        )
        assert result.batch_id == "batch-001"
        assert result.status == "queued"

    @respx.mock
    def test_retrieve_batch(self) -> None:
        respx.get("http://gateway.test/v1/batches/batch-001").respond(200, json=BATCH_COMPLETED_RESPONSE)
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.batches.retrieve("batch-001")
        assert result.status == "completed"

    @respx.mock
    def test_cancel_batch(self) -> None:
        respx.post("http://gateway.test/v1/batches/batch-001/cancel").respond(
            200, json={"batch_id": "batch-001", "status": "cancelled", "total": 3}
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.batches.cancel("batch-001")
        assert result.status == "cancelled"


class TestAsyncModels:
    @respx.mock
    @pytest.mark.anyio
    async def test_async_list_models(self) -> None:
        respx.get("http://gateway.test/v1/models").respond(200, json=MODELS_LIST_RESPONSE)
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = await client.models.list()
        assert len(result.data) == 2

    @respx.mock
    @pytest.mark.anyio
    async def test_async_retrieve_model(self) -> None:
        respx.get("http://gateway.test/v1/models/gpt-4o").respond(200, json=MODEL_RESPONSE)
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = await client.models.retrieve("gpt-4o")
        assert result.id == "gpt-4o"
