"""Response requests and lazy resource access."""
from __future__ import annotations
import pytest
import respx
from fi.gateway import AgentCC, AsyncAgentCC
from ._responses_files_fixtures import RESPONSE_OBJECT, RESPONSE_WITH_TOOLS, FILE_OBJECT, FILE_LIST, FILE_DELETED


class TestPropertyAccess:
    def test_responses_accessible_via_client(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert type(client.responses).__qualname__ == "Responses"

    def test_responses_cached(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert client.responses is client.responses

    def test_files_accessible_via_client(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert type(client.files).__qualname__ == "Files"

    def test_files_cached(self) -> None:
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert client.files is client.files

    def test_async_responses_accessible_via_client(self) -> None:
        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert type(client.responses).__qualname__ == "AsyncResponses"

    def test_async_files_accessible_via_client(self) -> None:
        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert type(client.files).__qualname__ == "AsyncFiles"


class TestResponses:
    @respx.mock
    def test_responses_create_basic(self) -> None:
        respx.post("http://gateway.test/v1/responses").respond(
            200, json=RESPONSE_OBJECT
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.responses.create(model="gpt-4o", input="Say hello")
        assert type(result).__qualname__ == "ResponseObject"
        assert result.id == "resp-001"
        assert result.object == "response"
        assert result.model == "gpt-4o"
        assert result.status == "completed"
        assert len(result.output) == 1
        assert result.output[0].content[0].text == "Hello, world!"

    @respx.mock
    def test_responses_create_with_tools(self) -> None:
        route = respx.post("http://gateway.test/v1/responses").respond(
            200, json=RESPONSE_WITH_TOOLS
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        tools = [{"type": "function", "function": {"name": "get_weather"}}]
        result = client.responses.create(
            model="gpt-4o",
            input="What is the weather?",
            tools=tools,
            tool_choice="auto",
        )
        assert result.id == "resp-002"
        # Verify tools were sent in request body
        import json

        request_body = json.loads(route.calls[0].request.content)
        assert request_body["tools"] == tools
        assert request_body["tool_choice"] == "auto"

    @respx.mock
    def test_responses_create_with_instructions(self) -> None:
        route = respx.post("http://gateway.test/v1/responses").respond(
            200, json=RESPONSE_OBJECT
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.responses.create(
            model="gpt-4o",
            input="Hello",
            instructions="You are a helpful assistant.",
        )
        assert result.id == "resp-001"
        import json

        request_body = json.loads(route.calls[0].request.content)
        assert request_body["instructions"] == "You are a helpful assistant."

    @respx.mock
    def test_responses_create_with_previous_response_id(self) -> None:
        route = respx.post("http://gateway.test/v1/responses").respond(
            200, json=RESPONSE_OBJECT
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.responses.create(
            model="gpt-4o",
            input="Continue",
            previous_response_id="resp-000",
        )
        assert result.id == "resp-001"
        import json

        request_body = json.loads(route.calls[0].request.content)
        assert request_body["previous_response_id"] == "resp-000"

    @respx.mock
    def test_responses_create_all_params(self) -> None:
        route = respx.post("http://gateway.test/v1/responses").respond(
            200, json=RESPONSE_OBJECT
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.responses.create(
            model="gpt-4o",
            input=[{"role": "user", "content": "Hi"}],
            instructions="Be concise.",
            tools=[{"type": "function", "function": {"name": "search"}}],
            tool_choice="auto",
            temperature=0.7,
            top_p=0.9,
            max_output_tokens=100,
            previous_response_id="resp-prev",
            store=False,
            metadata={"tag": "test"},
        )
        assert result.id == "resp-001"
        import json

        request_body = json.loads(route.calls[0].request.content)
        assert request_body["model"] == "gpt-4o"
        assert request_body["instructions"] == "Be concise."
        assert request_body["temperature"] == 0.7
        assert request_body["top_p"] == 0.9
        assert request_body["max_output_tokens"] == 100
        assert request_body["previous_response_id"] == "resp-prev"
        assert request_body["store"] is False
        assert request_body["metadata"] == {"tag": "test"}

    @respx.mock
    def test_responses_retrieve(self) -> None:
        respx.get("http://gateway.test/v1/responses/resp-001").respond(
            200, json=RESPONSE_OBJECT
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.responses.retrieve("resp-001")
        assert type(result).__qualname__ == "ResponseObject"
        assert result.id == "resp-001"
        assert result.model == "gpt-4o"
        assert result.usage is not None
        assert result.usage.total_tokens == 15

    @respx.mock
    def test_responses_delete(self) -> None:
        respx.delete("http://gateway.test/v1/responses/resp-001").respond(204)
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        # delete should return None without error
        result = client.responses.delete("resp-001")
        assert result is None


class TestAsyncResponses:
    @respx.mock
    @pytest.mark.anyio
    async def test_async_responses_create_basic(self) -> None:
        respx.post("http://gateway.test/v1/responses").respond(
            200, json=RESPONSE_OBJECT
        )
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = await client.responses.create(model="gpt-4o", input="Say hello")
        assert type(result).__qualname__ == "ResponseObject"
        assert result.id == "resp-001"
        assert result.model == "gpt-4o"

    @respx.mock
    @pytest.mark.anyio
    async def test_async_responses_retrieve(self) -> None:
        respx.get("http://gateway.test/v1/responses/resp-001").respond(
            200, json=RESPONSE_OBJECT
        )
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = await client.responses.retrieve("resp-001")
        assert result.id == "resp-001"

    @respx.mock
    @pytest.mark.anyio
    async def test_async_responses_delete(self) -> None:
        respx.delete("http://gateway.test/v1/responses/resp-001").respond(204)
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = await client.responses.delete("resp-001")
        assert result is None
