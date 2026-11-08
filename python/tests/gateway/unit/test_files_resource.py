"""File resource sync and async requests."""
from __future__ import annotations
import pytest
import respx
from fi.gateway import AgentCC, AsyncAgentCC
from ._responses_files_fixtures import RESPONSE_OBJECT, RESPONSE_WITH_TOOLS, FILE_OBJECT, FILE_LIST, FILE_DELETED


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
        respx.get("http://gateway.test/v1/files?purpose=fine-tune").respond(
            200, json=FILE_LIST
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.files.list(purpose="fine-tune")
        assert len(result.data) == 1
        assert result.data[0].purpose == "fine-tune"

    @respx.mock
    def test_files_retrieve(self) -> None:
        respx.get("http://gateway.test/v1/files/file-abc123").respond(
            200, json=FILE_OBJECT
        )
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
        respx.delete("http://gateway.test/v1/files/file-abc123").respond(
            200, json=FILE_DELETED
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = client.files.delete("file-abc123")
        assert type(result).__qualname__ == "FileDeleted"
        assert result.id == "file-abc123"
        assert result.deleted is True


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
        respx.get("http://gateway.test/v1/files/file-abc123").respond(
            200, json=FILE_OBJECT
        )
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
        respx.delete("http://gateway.test/v1/files/file-abc123").respond(
            200, json=FILE_DELETED
        )
        client = AsyncAgentCC(api_key="sk-test", base_url="http://gateway.test")
        result = await client.files.delete("file-abc123")
        assert result.deleted is True
