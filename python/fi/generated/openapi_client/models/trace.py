from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.trace_error import TraceError
    from ..models.trace_input import TraceInput
    from ..models.trace_metadata import TraceMetadata
    from ..models.trace_output import TraceOutput
    from ..models.trace_tags import TraceTags


T = TypeVar("T", bound="Trace")


@_attrs_define
class Trace:
    """
    Attributes:
        project (UUID):
        id (UUID | Unset):
        project_version (UUID | Unset):
        name (None | str | Unset):
        metadata (TraceMetadata | Unset):
        input_ (TraceInput | Unset):
        output (TraceOutput | Unset):
        error (TraceError | Unset):
        session (UUID | Unset):
        external_id (None | str | Unset):
        tags (TraceTags | Unset):
    """

    project: UUID
    id: UUID | Unset = UNSET
    project_version: UUID | Unset = UNSET
    name: None | str | Unset = UNSET
    metadata: TraceMetadata | Unset = UNSET
    input_: TraceInput | Unset = UNSET
    output: TraceOutput | Unset = UNSET
    error: TraceError | Unset = UNSET
    session: UUID | Unset = UNSET
    external_id: None | str | Unset = UNSET
    tags: TraceTags | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project = str(self.project)

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        project_version: str | Unset = UNSET
        if not isinstance(self.project_version, Unset):
            project_version = str(self.project_version)

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        input_: dict[str, Any] | Unset = UNSET
        if not isinstance(self.input_, Unset):
            input_ = self.input_.to_dict()

        output: dict[str, Any] | Unset = UNSET
        if not isinstance(self.output, Unset):
            output = self.output.to_dict()

        error: dict[str, Any] | Unset = UNSET
        if not isinstance(self.error, Unset):
            error = self.error.to_dict()

        session: str | Unset = UNSET
        if not isinstance(self.session, Unset):
            session = str(self.session)

        external_id: None | str | Unset
        if isinstance(self.external_id, Unset):
            external_id = UNSET
        else:
            external_id = self.external_id

        tags: dict[str, Any] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "project": project,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if project_version is not UNSET:
            field_dict["project_version"] = project_version
        if name is not UNSET:
            field_dict["name"] = name
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if input_ is not UNSET:
            field_dict["input"] = input_
        if output is not UNSET:
            field_dict["output"] = output
        if error is not UNSET:
            field_dict["error"] = error
        if session is not UNSET:
            field_dict["session"] = session
        if external_id is not UNSET:
            field_dict["external_id"] = external_id
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_error import TraceError
        from ..models.trace_input import TraceInput
        from ..models.trace_metadata import TraceMetadata
        from ..models.trace_output import TraceOutput
        from ..models.trace_tags import TraceTags

        d = dict(src_dict)
        project = UUID(d.pop("project"))

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _project_version = d.pop("project_version", UNSET)
        project_version: UUID | Unset
        if isinstance(_project_version, Unset):
            project_version = UNSET
        else:
            project_version = UUID(_project_version)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        _metadata = d.pop("metadata", UNSET)
        metadata: TraceMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = TraceMetadata.from_dict(_metadata)

        _input_ = d.pop("input", UNSET)
        input_: TraceInput | Unset
        if isinstance(_input_, Unset):
            input_ = UNSET
        else:
            input_ = TraceInput.from_dict(_input_)

        _output = d.pop("output", UNSET)
        output: TraceOutput | Unset
        if isinstance(_output, Unset):
            output = UNSET
        else:
            output = TraceOutput.from_dict(_output)

        _error = d.pop("error", UNSET)
        error: TraceError | Unset
        if isinstance(_error, Unset):
            error = UNSET
        else:
            error = TraceError.from_dict(_error)

        _session = d.pop("session", UNSET)
        session: UUID | Unset
        if isinstance(_session, Unset):
            session = UNSET
        else:
            session = UUID(_session)

        def _parse_external_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        external_id = _parse_external_id(d.pop("external_id", UNSET))

        _tags = d.pop("tags", UNSET)
        tags: TraceTags | Unset
        if isinstance(_tags, Unset):
            tags = UNSET
        else:
            tags = TraceTags.from_dict(_tags)

        trace = cls(
            project=project,
            id=id,
            project_version=project_version,
            name=name,
            metadata=metadata,
            input_=input_,
            output=output,
            error=error,
            session=session,
            external_id=external_id,
            tags=tags,
        )

        trace.additional_properties = d
        return trace

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
