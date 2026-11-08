"""Tests for advanced features: mock streaming, health check, JSON validation (ported from agentcc 1.0)."""

from __future__ import annotations

import httpx
import pytest
import respx

from fi.gateway._client import AgentCC
from fi.gateway._exceptions import AgentCCError
from fi.gateway._structured import validate_json_response
from fi.gateway._utils import health_check

# ---------------------------------------------------------------------------
# Mock streaming
# ---------------------------------------------------------------------------


class TestMockStreaming:
    def test_mock_response_stream(self) -> None:
        """stream=True with mock_response returns a StreamManager."""
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
        )
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "hi"}],
            mock_response="hello world",
            stream=True,
        )
        # Should be a StreamManager
        from fi.gateway._streaming import StreamManager

        assert isinstance(result, StreamManager)

    def test_mock_response_stream_content(self) -> None:
        """Verify that streaming mock response yields the full content."""
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
        )
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "hi"}],
            mock_response="hello world test",
            stream=True,
        )
        # Collect all text chunks
        texts = []
        with result:
            for text in result.text_stream:
                texts.append(text)

        full_text = "".join(texts)
        assert full_text == "hello world test"


# ---------------------------------------------------------------------------
# health_check
# ---------------------------------------------------------------------------


class TestHealthCheck:
    @respx.mock
    def test_health_check_basic(self) -> None:
        """Mock /healthz endpoint returning 200 (D-09: 1.0 asked for /health)."""
        respx.get("http://localhost:8080/healthz").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        result = health_check(base_url="http://localhost:8080")
        assert result["status"] == "ok"

    @respx.mock
    def test_health_check_returns_latency(self) -> None:
        """Verify latency_ms is present in success response."""
        respx.get("http://localhost:8080/healthz").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        result = health_check(base_url="http://localhost:8080")
        assert "latency_ms" in result
        assert isinstance(result["latency_ms"], float)

    def test_health_check_error(self) -> None:
        """Connection refused -> error status."""
        result = health_check(base_url="http://localhost:1")
        assert result["status"] == "error"
        assert "error" in result


# ---------------------------------------------------------------------------
# validate_json_response
# ---------------------------------------------------------------------------


class TestValidateJsonResponse:
    def test_validate_json_response_valid(self) -> None:
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name", "age"],
        }
        assert validate_json_response('{"name": "Alice", "age": 30}', schema) is True

    def test_validate_json_response_invalid(self) -> None:
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name", "age"],
        }
        # age is a string, not integer
        assert (
            validate_json_response('{"name": "Alice", "age": "thirty"}', schema)
            is False
        )

    def test_validate_json_response_invalid_json(self) -> None:
        schema = {"type": "object"}
        assert validate_json_response("not valid json {{{", schema) is False


# ---------------------------------------------------------------------------
# Lazy imports
# ---------------------------------------------------------------------------


class TestLazyImports:
    def test_health_check_importable(self) -> None:
        import fi.gateway as agentcc

        assert hasattr(agentcc, "health_check")
        assert callable(agentcc.health_check)

    def test_validate_json_response_importable(self) -> None:
        import fi.gateway as agentcc

        assert hasattr(agentcc, "validate_json_response")
        assert callable(agentcc.validate_json_response)


# ---------------------------------------------------------------------------
# JSON schema validation integration
# ---------------------------------------------------------------------------


class TestJsonSchemaValidationIntegration:
    def test_enable_json_schema_validation_stored(self) -> None:
        """enable_json_schema_validation is stored on client."""
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
            enable_json_schema_validation=True,
        )
        assert client._enable_json_schema_validation is True

    def test_enable_json_schema_validation_default_false(self) -> None:
        """Default is False."""
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert client._enable_json_schema_validation is False

    def test_json_schema_validation_passes(self) -> None:
        """Valid JSON response passes validation."""
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
            enable_json_schema_validation=True,
        )
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        response_format = {
            "type": "json_schema",
            "json_schema": {"name": "Test", "schema": schema},
        }
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "hi"}],
            mock_response='{"name": "Alice"}',
            response_format=response_format,
        )
        assert result.choices[0].message.content == '{"name": "Alice"}'

    def test_json_schema_validation_fails(self) -> None:
        """Invalid JSON response raises AgentCCError."""
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
            enable_json_schema_validation=True,
        )
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name", "age"],
        }
        response_format = {
            "type": "json_schema",
            "json_schema": {"name": "Test", "schema": schema},
        }
        with pytest.raises(AgentCCError, match="JSON schema validation failed"):
            client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "hi"}],
                mock_response='{"name": "Alice"}',  # missing required "age"
                response_format=response_format,
            )

    def test_json_schema_validation_not_triggered_without_schema(self) -> None:
        """No response_format -> no validation even if enabled."""
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
            enable_json_schema_validation=True,
        )
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "hi"}],
            mock_response="just text, not json",
        )
        assert result.choices[0].message.content == "just text, not json"

    def test_json_schema_validation_preserved_in_with_options(self) -> None:
        """with_options preserves enable_json_schema_validation."""
        client = AgentCC(
            api_key="sk-test",
            base_url="http://localhost:8080",
            enable_json_schema_validation=True,
        )
        new_client = client.with_options(timeout=30)
        assert new_client._enable_json_schema_validation is True
