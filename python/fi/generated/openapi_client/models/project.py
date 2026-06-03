from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.project_model_type import ProjectModelType
from ..models.project_source import ProjectSource
from ..models.project_trace_type import ProjectTraceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.project_config import ProjectConfig
    from ..models.project_metadata import ProjectMetadata
    from ..models.project_session_config import ProjectSessionConfig
    from ..models.project_tags import ProjectTags


T = TypeVar("T", bound="Project")


@_attrs_define
class Project:
    """
    Attributes:
        model_type (ProjectModelType):
        name (str):
        trace_type (ProjectTraceType):
        id (UUID | Unset):
        metadata (ProjectMetadata | Unset):
        organization (UUID | Unset):
        workspace (None | Unset | UUID):
        created_at (datetime.datetime | Unset):
        updated_at (datetime.datetime | Unset):
        config (ProjectConfig | Unset): Any valid JSON value.
        source (ProjectSource | Unset):
        session_config (ProjectSessionConfig | Unset): Any valid JSON value.
        tags (ProjectTags | Unset): Any valid JSON value.
    """

    model_type: ProjectModelType
    name: str
    trace_type: ProjectTraceType
    id: UUID | Unset = UNSET
    metadata: ProjectMetadata | Unset = UNSET
    organization: UUID | Unset = UNSET
    workspace: None | Unset | UUID = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    config: ProjectConfig | Unset = UNSET
    source: ProjectSource | Unset = UNSET
    session_config: ProjectSessionConfig | Unset = UNSET
    tags: ProjectTags | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        model_type = self.model_type.value

        name = self.name

        trace_type = self.trace_type.value

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        organization: str | Unset = UNSET
        if not isinstance(self.organization, Unset):
            organization = str(self.organization)

        workspace: None | str | Unset
        if isinstance(self.workspace, Unset):
            workspace = UNSET
        elif isinstance(self.workspace, UUID):
            workspace = str(self.workspace)
        else:
            workspace = self.workspace

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config, Unset):
            config = self.config.to_dict()

        source: str | Unset = UNSET
        if not isinstance(self.source, Unset):
            source = self.source.value

        session_config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.session_config, Unset):
            session_config = self.session_config.to_dict()

        tags: dict[str, Any] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "model_type": model_type,
                "name": name,
                "trace_type": trace_type,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if organization is not UNSET:
            field_dict["organization"] = organization
        if workspace is not UNSET:
            field_dict["workspace"] = workspace
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if config is not UNSET:
            field_dict["config"] = config
        if source is not UNSET:
            field_dict["source"] = source
        if session_config is not UNSET:
            field_dict["session_config"] = session_config
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.project_config import ProjectConfig
        from ..models.project_metadata import ProjectMetadata
        from ..models.project_session_config import ProjectSessionConfig
        from ..models.project_tags import ProjectTags

        d = dict(src_dict)
        model_type = ProjectModelType(d.pop("model_type"))

        name = d.pop("name")

        trace_type = ProjectTraceType(d.pop("trace_type"))

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _metadata = d.pop("metadata", UNSET)
        metadata: ProjectMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = ProjectMetadata.from_dict(_metadata)

        _organization = d.pop("organization", UNSET)
        organization: UUID | Unset
        if isinstance(_organization, Unset):
            organization = UNSET
        else:
            organization = UUID(_organization)

        def _parse_workspace(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                workspace_type_0 = UUID(data)

                return workspace_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        workspace = _parse_workspace(d.pop("workspace", UNSET))

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        _config = d.pop("config", UNSET)
        config: ProjectConfig | Unset
        if isinstance(_config, Unset):
            config = UNSET
        else:
            config = ProjectConfig.from_dict(_config)

        _source = d.pop("source", UNSET)
        source: ProjectSource | Unset
        if isinstance(_source, Unset):
            source = UNSET
        else:
            source = ProjectSource(_source)

        _session_config = d.pop("session_config", UNSET)
        session_config: ProjectSessionConfig | Unset
        if isinstance(_session_config, Unset):
            session_config = UNSET
        else:
            session_config = ProjectSessionConfig.from_dict(_session_config)

        _tags = d.pop("tags", UNSET)
        tags: ProjectTags | Unset
        if isinstance(_tags, Unset):
            tags = UNSET
        else:
            tags = ProjectTags.from_dict(_tags)

        project = cls(
            model_type=model_type,
            name=name,
            trace_type=trace_type,
            id=id,
            metadata=metadata,
            organization=organization,
            workspace=workspace,
            created_at=created_at,
            updated_at=updated_at,
            config=config,
            source=source,
            session_config=session_config,
            tags=tags,
        )

        project.additional_properties = d
        return project

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
