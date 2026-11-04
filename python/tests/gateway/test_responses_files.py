"""Tests for Responses and Files API resources."""

from __future__ import annotations

import pytest
import respx

from fi.gateway._client import AsyncAgentCC, AgentCC

# --- Response fixtures ---

RESPONSE_OBJECT = {
    "id": "resp-001",
    "object": "response",
    "model": "gpt-4o",
    "created_at": 1700000000,
    "status": "completed",
    "output": [
        {
            "type": "message",
            "content": [
                {"type": "output_text", "text": "Hello, world!"}
            ],
        }
    ],
    "usage": {
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
    },
    "metadata": {"session": "abc"},
    "error": None,
}

RESPONSE_WITH_TOOLS = {
    "id": "resp-002",
    "object": "response",
    "model": "gpt-4o",
    "created_at": 1700000001,
    "status": "completed",
    "output": [
        {
            "type": "message",
            "content": [
                {"type": "output_text", "text": "Using tools now."}
            ],
        }
    ],
    "usage": {
        "input_tokens": 20,
        "output_tokens": 10,
        "total_tokens": 30,
    },
    "metadata": None,
    "error": None,
}

FILE_OBJECT = {
    "id": "file-abc123",
    "object": "file",
    "bytes": 1024,
    "created_at": 1700000000,
    "filename": "training.jsonl",
    "purpose": "fine-tune",
    "status": "processed",
    "status_details": None,
}

FILE_LIST = {
    "data": [FILE_OBJECT],
    "object": "list",
}

FILE_DELETED = {
    "id": "file-abc123",
    "object": "file",
    "deleted": True,
}


# --- Lazy property access tests ---


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


# --- Responses sync tests ---


class TestResponses:
    @respx.mock
    def test_responses_create_basic(self) -> None:
        respx.post("http://gateway.test/v1/responses").respond(200, json=RESPONSE_OBJECT)
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
        route = respx.post("http://gateway.test/v1/responses").respond(200, json=RESPONSE_WITH_TOOLS)
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
        route = respx.post("http://gateway.test/v1/responses").respond(200, json=RESPONSE_OBJECT)
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
        route = respx.post("http://gateway.test/v1/responses").respond(200, json=RESPONSE_OBJECT)
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
        route = respx.post("http://gateway.test/v1/responses").respond(200, json=RESPONSE_OBJECT)
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
        respx.get("http://gateway.test/v1/responses/resp-001").respond(200, json=RESPONSE_OBJECT)
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


# --- Files sync tests ---


class TestFiles:
    @respx.mock
    def test_files_create(self) -> None:
        respx.post("http://gateway.test/v1/files").respond(200, json=FILE_OBJECT)
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.files.create(file="dummy-file-content", purpose="fine-tune")
        assert type(result).__qualname__ == "FileObject"
        assert result.id == "file-abc123"
        assert result.filename == "training.jsonl"
        assert result.purpose == "fine-tune"
        assert result.bytes == 1024

    @respx.mock
    def test_files_list(self) -> None:
        respx.get("http://gateway.test/v1/files").respond(200, json=FILE_LIST)
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.files.list()
        assert type(result).__qualname__ == "FileList"
        assert result.object == "list"
        assert len(result.data) == 1
        assert result.data[0].id == "file-abc123"

    @respx.mock
    def test_files_list_with_purpose_filter(self) -> None:
        respx.get("http://gateway.test/v1/files?purpose=fine-tune").respond(200, json=FILE_LIST)
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.files.list(purpose="fine-tune")
        assert len(result.data) == 1
        assert result.data[0].purpose == "fine-tune"

    @respx.mock
    def test_files_retrieve(self) -> None:
        respx.get("http://gateway.test/v1/files/file-abc123").respond(200, json=FILE_OBJECT)
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.files.retrieve("file-abc123")
        assert type(result).__qualname__ == "FileObject"
        assert result.id == "file-abc123"
        assert result.status == "processed"

    @respx.mock
    def test_files_content_returns_bytes(self) -> None:
        raw_content = b"line1\nline2\nline3"
        respx.get("http://gateway.test/v1/files/file-abc123/content").respond(
            200, content=raw_content
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.files.content("file-abc123")
        assert isinstance(result, bytes)
        assert result == raw_content

    @respx.mock
    def test_files_delete(self) -> None:
        respx.delete("http://gateway.test/v1/files/file-abc123").respond(200, json=FILE_DELETED)
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.files.delete("file-abc123")
        assert type(result).__qualname__ == "FileDeleted"
        assert result.id == "file-abc123"
        assert result.deleted is True


# --- Async Responses tests ---


class TestAsyncResponses:
    @respx.mock
    @pytest.mark.anyio
    async def test_async_responses_create_basic(self) -> None:
        respx.post("http://gateway.test/v1/responses").respond(200, json=RESPONSE_OBJECT)
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = await client.responses.create(model="gpt-4o", input="Say hello")
        assert type(result).__qualname__ == "ResponseObject"
        assert result.id == "resp-001"
        assert result.model == "gpt-4o"

    @respx.mock
    @pytest.mark.anyio
    async def test_async_responses_retrieve(self) -> None:
        respx.get("http://gateway.test/v1/responses/resp-001").respond(200, json=RESPONSE_OBJECT)
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


# --- Async Files tests ---


class TestAsyncFiles:
    @respx.mock
    @pytest.mark.anyio
    async def test_async_files_create(self) -> None:
        respx.post("http://gateway.test/v1/files").respond(200, json=FILE_OBJECT)
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = await client.files.create(file="dummy", purpose="fine-tune")
        assert type(result).__qualname__ == "FileObject"
        assert result.id == "file-abc123"

    @respx.mock
    @pytest.mark.anyio
    async def test_async_files_list(self) -> None:
        respx.get("http://gateway.test/v1/files").respond(200, json=FILE_LIST)
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = await client.files.list()
        assert len(result.data) == 1

    @respx.mock
    @pytest.mark.anyio
    async def test_async_files_retrieve(self) -> None:
        respx.get("http://gateway.test/v1/files/file-abc123").respond(200, json=FILE_OBJECT)
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = await client.files.retrieve("file-abc123")
        assert result.id == "file-abc123"

    @respx.mock
    @pytest.mark.anyio
    async def test_async_files_content_returns_bytes(self) -> None:
        raw_content = b"binary-data-here"
        respx.get("http://gateway.test/v1/files/file-abc123/content").respond(
            200, content=raw_content
        )
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = await client.files.content("file-abc123")
        assert isinstance(result, bytes)
        assert result == raw_content

    @respx.mock
    @pytest.mark.anyio
    async def test_async_files_delete(self) -> None:
        respx.delete("http://gateway.test/v1/files/file-abc123").respond(200, json=FILE_DELETED)
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = await client.files.delete("file-abc123")
        assert result.deleted is True


# --- Type validation tests ---


class TestTypes:
    def test_response_object_extra_allow(self) -> None:
        from fi.gateway.types.responses import ResponseObject

        obj = ResponseObject(id="r1", extra_field="value")
        assert obj.id == "r1"
        assert obj.extra_field == "value"  # type: ignore[attr-defined]

    def test_file_object_extra_allow(self) -> None:
        from fi.gateway.types.files import FileObject

        obj = FileObject(id="f1", extra_field="value")
        assert obj.id == "f1"
        assert obj.extra_field == "value"  # type: ignore[attr-defined]

    def test_response_usage(self) -> None:
        from fi.gateway.types.responses import ResponseUsage

        usage = ResponseUsage(input_tokens=10, output_tokens=5, total_tokens=15)
        assert usage.input_tokens == 10
        assert usage.output_tokens == 5
        assert usage.total_tokens == 15

    def test_content_part_defaults(self) -> None:
        from fi.gateway.types.responses import ContentPart

        part = ContentPart(text="hello")
        assert part.type == "output_text"
        assert part.text == "hello"

    def test_response_stream_event(self) -> None:
        from fi.gateway.types.responses import ResponseStreamEvent

        event = ResponseStreamEvent(type="response.created", response=None)
        assert event.type == "response.created"
        assert event.response is None

    def test_file_list(self) -> None:
        from fi.gateway.types.files import FileList, FileObject

        fl = FileList(data=[FileObject(id="f1"), FileObject(id="f2")])
        assert len(fl.data) == 2
        assert fl.object == "list"

    def test_file_deleted(self) -> None:
        from fi.gateway.types.files import FileDeleted

        fd = FileDeleted(id="f1", deleted=True)
        assert fd.deleted is True
        assert fd.object == "file"


# --- Type exports tests ---


class TestTypeExports:
    def test_response_types_in_types_module(self) -> None:
        from fi.gateway.types import (
            ContentPart,
            ResponseObject,
            ResponseOutput,
            ResponseStreamEvent,
            ResponseUsage,
        )

        assert ResponseObject is not None
        assert ResponseOutput is not None
        assert ContentPart is not None
        assert ResponseUsage is not None
        assert ResponseStreamEvent is not None

    def test_file_types_in_types_module(self) -> None:
        from fi.gateway.types import FileDeleted, FileList, FileObject

        assert FileObject is not None
        assert FileList is not None
        assert FileDeleted is not None

    def test_resource_classes_in_resources_module(self) -> None:
        from fi.gateway.resources import (
            AsyncFiles,
            AsyncResponses,
            Files,
            Responses,
        )

        assert Responses is not None
        assert AsyncResponses is not None
        assert Files is not None
        assert AsyncFiles is not None
