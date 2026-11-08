"""Response and file types and public exports."""
from __future__ import annotations
import pytest
import respx
from fi.gateway import AgentCC, AsyncAgentCC
from ._responses_files_fixtures import RESPONSE_OBJECT, RESPONSE_WITH_TOOLS, FILE_OBJECT, FILE_LIST, FILE_DELETED


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
        from fi.gateway.resources import AsyncFiles, AsyncResponses, Files, Responses

        assert Responses is not None
        assert AsyncResponses is not None
        assert Files is not None
        assert AsyncFiles is not None
