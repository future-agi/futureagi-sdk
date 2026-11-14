"""Tests for developer-experience features: function_to_dict, drop_params, mock_response, cost tracking."""

from __future__ import annotations

import threading

import pytest

from fi.gateway._client import AsyncAgentCC, AgentCC
from fi.gateway._function_utils import function_to_dict

# ---------------------------------------------------------------------------
# function_to_dict
# ---------------------------------------------------------------------------


class TestFunctionToDict:
    def test_basic_function(self) -> None:
        def greet(name: str) -> str:
            """Say hello."""
            return f"Hello, {name}"

        schema = function_to_dict(greet)
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "greet"
        assert schema["function"]["description"] == "Say hello."
        params = schema["function"]["parameters"]
        assert params["type"] == "object"
        assert params["properties"]["name"] == {"type": "string"}
        assert params["required"] == ["name"]

    def test_with_defaults(self) -> None:
        def search(query: str, limit: int = 10) -> list:
            """Search for items."""
            return []

        schema = function_to_dict(search)
        params = schema["function"]["parameters"]
        assert "query" in params["properties"]
        assert "limit" in params["properties"]
        # Only 'query' should be required because 'limit' has a default
        assert params["required"] == ["query"]

    def test_with_docstring(self) -> None:
        def compute(x: float, y: float) -> float:
            """Compute the sum of two numbers."""
            return x + y

        schema = function_to_dict(compute)
        assert schema["function"]["description"] == "Compute the sum of two numbers."

    def test_no_docstring(self) -> None:
        def noop() -> None:
            pass

        schema = function_to_dict(noop)
        assert "description" not in schema["function"]

    def test_various_types(self) -> None:
        def process(
            name: str,
            count: int,
            ratio: float,
            active: bool,
            items: list,
        ) -> dict:
            """Process data."""
            return {}

        schema = function_to_dict(process)
        props = schema["function"]["parameters"]["properties"]
        assert props["name"] == {"type": "string"}
        assert props["count"] == {"type": "integer"}
        assert props["ratio"] == {"type": "number"}
        assert props["active"] == {"type": "boolean"}
        assert props["items"] == {"type": "array"}

    def test_no_annotations(self) -> None:
        def raw(x, y):  # type: ignore[no-untyped-def]
            """Raw function."""
            return x + y

        schema = function_to_dict(raw)
        # Without annotations, should default to string
        props = schema["function"]["parameters"]["properties"]
        assert props["x"] == {"type": "string"}
        assert props["y"] == {"type": "string"}

    def test_no_params(self) -> None:
        def ping() -> str:
            """Ping the server."""
            return "pong"

        schema = function_to_dict(ping)
        params = schema["function"]["parameters"]
        assert params["properties"] == {}
        assert "required" not in params

    def test_dict_return_type(self) -> None:
        def get_data(key: str) -> dict:
            """Get data by key."""
            return {}

        schema = function_to_dict(get_data)
        assert schema["function"]["parameters"]["properties"]["key"] == {"type": "string"}


# ---------------------------------------------------------------------------
# drop_params
# ---------------------------------------------------------------------------


class TestDropParams:
    def test_default_is_false(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert client._drop_params is False

    def test_set_true(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080", drop_params=True)
        assert client._drop_params is True

    def test_with_options_propagates(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080", drop_params=True)
        new = client.with_options(timeout=30.0)
        assert new._drop_params is True

    def test_with_options_overrides(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080", drop_params=True)
        new = client.with_options(drop_params=False)
        assert new._drop_params is False

    def test_async_default_is_false(self) -> None:
        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert client._drop_params is False

    def test_async_set_true(self) -> None:
        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080", drop_params=True)
        assert client._drop_params is True

    def test_async_with_options_propagates(self) -> None:
        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080", drop_params=True)
        new = client.with_options(timeout=30.0)
        assert new._drop_params is True


# ---------------------------------------------------------------------------
# mock_response
# ---------------------------------------------------------------------------


class TestMockResponse:
    def test_sync_mock_response(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            mock_response="This is a mock reply",
        )
        assert result.id == "chatcmpl-mock"
        assert result.object == "chat.completion"
        assert result.model == "gpt-4o"
        assert result.created == 0
        assert len(result.choices) == 1
        assert result.choices[0].message.role == "assistant"
        assert result.choices[0].message.content == "This is a mock reply"
        assert result.choices[0].finish_reason == "stop"
        assert result.usage is not None
        assert result.usage.prompt_tokens == 0
        assert result.usage.completion_tokens == 0
        assert result.usage.total_tokens == 0

    def test_sync_mock_response_no_http(self) -> None:
        """mock_response should work without any network — no base client needed."""
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        # The base client is never initialised
        assert client._base_client is None
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "test"}],
            mock_response="mocked",
        )
        assert result.choices[0].message.content == "mocked"
        # Still no base client — no HTTP was used
        assert client._base_client is None

    @pytest.mark.anyio
    async def test_async_mock_response(self) -> None:
        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080")
        result = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            mock_response="async mock",
        )
        assert result.id == "chatcmpl-mock"
        assert result.choices[0].message.content == "async mock"
        assert result.model == "gpt-4o-mini"

    def test_mock_response_preserves_model(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        result = client.chat.completions.create(
            model="claude-3-opus",
            messages=[{"role": "user", "content": "hi"}],
            mock_response="ok",
        )
        assert result.model == "claude-3-opus"


# ---------------------------------------------------------------------------
# _current_cost / current_cost / reset_cost
# ---------------------------------------------------------------------------


class TestCostTracking:
    def test_initial_cost_is_zero(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert client.current_cost == 0.0

    def test_track_cost(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        client._track_cost(0.01)
        client._track_cost(0.02)
        assert abs(client.current_cost - 0.03) < 1e-9

    def test_reset_cost(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        client._track_cost(1.5)
        assert client.current_cost == 1.5
        client.reset_cost()
        assert client.current_cost == 0.0

    def test_thread_safety(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        errors: list[Exception] = []

        def add_cost() -> None:
            try:
                for _ in range(1000):
                    client._track_cost(0.001)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=add_cost) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        expected = 10 * 1000 * 0.001  # 10.0
        assert abs(client.current_cost - expected) < 1e-6

    def test_async_initial_cost_is_zero(self) -> None:
        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert client.current_cost == 0.0

    def test_async_track_cost(self) -> None:
        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080")
        client._track_cost(0.05)
        assert client.current_cost == 0.05

    def test_async_reset_cost(self) -> None:
        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080")
        client._track_cost(2.0)
        client.reset_cost()
        assert client.current_cost == 0.0


# ---------------------------------------------------------------------------
# Lazy import of function_to_dict from fi.gateway module
# ---------------------------------------------------------------------------


class TestLazyImport:
    def test_import_function_to_dict(self) -> None:
        import fi.gateway as agentcc

        assert hasattr(agentcc, "function_to_dict")
        assert callable(agentcc.function_to_dict)

    def test_function_to_dict_in_all(self) -> None:
        import fi.gateway as agentcc

        assert "function_to_dict" in agentcc.__all__

    def test_lazy_import_works(self) -> None:
        """Verify the lazily-imported function_to_dict actually works."""
        import fi.gateway as agentcc

        def example(x: int) -> str:
            """Example function."""
            return str(x)

        schema = agentcc.function_to_dict(example)
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "example"
