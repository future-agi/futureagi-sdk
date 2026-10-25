"""Tests for the Rerank API resource."""

from __future__ import annotations

import respx

from fi.gateway._client import AsyncAgentCC, AgentCC

GATEWAY = "http://test-gateway:8080"

RERANK_RESPONSE = {
    "id": "rerank-1",
    "results": [
        {"index": 0, "relevance_score": 0.95, "document": "doc about AI"},
        {"index": 2, "relevance_score": 0.80, "document": "doc about ML"},
    ],
    "model": "rerank-english-v3.0",
}

RERANK_RESPONSE_NO_DOCS = {
    "id": "rerank-2",
    "results": [
        {"index": 0, "relevance_score": 0.95},
        {"index": 2, "relevance_score": 0.80},
    ],
    "model": "rerank-english-v3.0",
}

RERANK_RESPONSE_WITH_USAGE = {
    "id": "rerank-3",
    "results": [
        {"index": 1, "relevance_score": 0.99, "document": "relevant doc"},
    ],
    "model": "rerank-english-v3.0",
    "usage": {"prompt_tokens": 20, "total_tokens": 20},
}


class TestRerankCreate:
    @respx.mock
    def test_rerank_create(self) -> None:
        respx.post(f"{GATEWAY}/v1/rerank").respond(
            200,
            json=RERANK_RESPONSE,
            headers={
                "x-agentcc-request-id": "req-1",
                "x-agentcc-provider": "cohere",
            },
        )

        client = AgentCC(api_key="sk-test-key-12345", base_url=GATEWAY)
        result = client.rerank.create(
            model="rerank-english-v3.0",
            query="What is AI?",
            documents=["doc about AI", "doc about cooking", "doc about ML"],
            top_n=2,
            return_documents=True,
        )
        assert len(result.results) == 2
        assert result.results[0].relevance_score == 0.95
        assert result.results[0].index == 0
        assert result.results[0].document == "doc about AI"
        assert result.results[1].relevance_score == 0.80
        assert result.results[1].index == 2
        assert result.results[1].document == "doc about ML"
        assert result.id == "rerank-1"
        assert result.model == "rerank-english-v3.0"
        client.close()

    @respx.mock
    def test_rerank_without_return_documents(self) -> None:
        respx.post(f"{GATEWAY}/v1/rerank").respond(
            200,
            json=RERANK_RESPONSE_NO_DOCS,
            headers={"x-agentcc-request-id": "req-2", "x-agentcc-provider": "cohere"},
        )

        client = AgentCC(api_key="sk-test-key-12345", base_url=GATEWAY)
        result = client.rerank.create(
            model="rerank-english-v3.0",
            query="What is AI?",
            documents=["doc about AI", "doc about cooking", "doc about ML"],
        )
        assert len(result.results) == 2
        assert result.results[0].document is None
        assert result.results[1].document is None
        client.close()

    @respx.mock
    def test_rerank_top_n_param(self) -> None:
        route = respx.post(f"{GATEWAY}/v1/rerank").respond(
            200,
            json=RERANK_RESPONSE_WITH_USAGE,
            headers={"x-agentcc-request-id": "req-3", "x-agentcc-provider": "cohere"},
        )

        client = AgentCC(api_key="sk-test-key-12345", base_url=GATEWAY)
        result = client.rerank.create(
            model="rerank-english-v3.0",
            query="relevant query",
            documents=["irrelevant", "relevant doc", "also irrelevant"],
            top_n=1,
            return_documents=True,
        )
        assert len(result.results) == 1
        assert result.results[0].relevance_score == 0.99
        assert result.usage == {"prompt_tokens": 20, "total_tokens": 20}

        # Verify the request body was correct
        import json

        request_body = json.loads(route.calls[0].request.content)
        assert request_body["top_n"] == 1
        assert request_body["return_documents"] is True
        assert request_body["model"] == "rerank-english-v3.0"
        assert request_body["query"] == "relevant query"
        assert len(request_body["documents"]) == 3
        client.close()


class TestRerankPropertyAccess:
    def test_rerank_property_exists(self) -> None:
        client = AgentCC(api_key="sk-test", base_url=GATEWAY)
        assert hasattr(client, "rerank")

    def test_rerank_property_lazy_init(self) -> None:
        client = AgentCC(api_key="sk-test", base_url=GATEWAY)
        assert type(client.rerank).__qualname__ == "Rerank"

    def test_rerank_property_cached(self) -> None:
        client = AgentCC(api_key="sk-test", base_url=GATEWAY)
        assert client.rerank is client.rerank

    def test_async_rerank_property(self) -> None:
        client = AsyncAgentCC(api_key="sk-test", base_url=GATEWAY)
        assert type(client.rerank).__qualname__ == "AsyncRerank"

    def test_async_rerank_property_cached(self) -> None:
        client = AsyncAgentCC(api_key="sk-test", base_url=GATEWAY)
        assert client.rerank is client.rerank


class TestRerankTypes:
    def test_rerank_result_model(self) -> None:
        from fi.gateway.types.rerank import RerankResult

        r = RerankResult(index=0, relevance_score=0.95, document="hello")
        assert r.index == 0
        assert r.relevance_score == 0.95
        assert r.document == "hello"

    def test_rerank_result_without_document(self) -> None:
        from fi.gateway.types.rerank import RerankResult

        r = RerankResult(index=1, relevance_score=0.5)
        assert r.document is None

    def test_rerank_response_model(self) -> None:
        from fi.gateway.types.rerank import RerankResponse, RerankResult

        resp = RerankResponse(
            id="rerank-1",
            results=[RerankResult(index=0, relevance_score=0.9)],
            model="rerank-english-v3.0",
        )
        assert resp.id == "rerank-1"
        assert len(resp.results) == 1
        assert resp.model == "rerank-english-v3.0"
        assert resp.usage is None

    def test_rerank_response_defaults(self) -> None:
        from fi.gateway.types.rerank import RerankResponse

        resp = RerankResponse()
        assert resp.id is None
        assert resp.results == []
        assert resp.model is None
        assert resp.usage is None

    def test_rerank_response_extra_fields(self) -> None:
        from fi.gateway.types.rerank import RerankResponse

        resp = RerankResponse(id="r1", custom_field="custom_value")
        assert resp.custom_field == "custom_value"

    def test_rerank_result_extra_fields(self) -> None:
        from fi.gateway.types.rerank import RerankResult

        r = RerankResult(index=0, relevance_score=0.8, custom="val")
        assert r.custom == "val"


class TestRerankExports:
    def test_types_export(self) -> None:
        from fi.gateway.types import RerankResponse, RerankResult

        assert RerankResponse is not None
        assert RerankResult is not None

    def test_resources_export(self) -> None:
        from fi.gateway.resources import AsyncRerank, Rerank

        assert Rerank is not None
        assert AsyncRerank is not None
