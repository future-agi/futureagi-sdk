from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.annotations_labels_type import AnnotationsLabelsType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.annotations_labels_settings import AnnotationsLabelsSettings


T = TypeVar("T", bound="AnnotationsLabels")


@_attrs_define
class AnnotationsLabels:
    """
    Attributes:
        name (str):
        type_ (AnnotationsLabelsType):
        id (UUID | Unset):
        organization (UUID | Unset):
        settings (AnnotationsLabelsSettings | Unset):
        project (UUID | Unset):
        description (None | str | Unset):
        allow_notes (bool | Unset):
        created_at (datetime.datetime | Unset):
        trace_annotations_count (int | Unset):
        annotation_count (int | Unset):
    """

    name: str
    type_: AnnotationsLabelsType
    id: UUID | Unset = UNSET
    organization: UUID | Unset = UNSET
    settings: AnnotationsLabelsSettings | Unset = UNSET
    project: UUID | Unset = UNSET
    description: None | str | Unset = UNSET
    allow_notes: bool | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    trace_annotations_count: int | Unset = UNSET
    annotation_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        type_ = self.type_.value

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        organization: str | Unset = UNSET
        if not isinstance(self.organization, Unset):
            organization = str(self.organization)

        settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.settings, Unset):
            settings = self.settings.to_dict()

        project: str | Unset = UNSET
        if not isinstance(self.project, Unset):
            project = str(self.project)

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        allow_notes = self.allow_notes

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        trace_annotations_count = self.trace_annotations_count

        annotation_count = self.annotation_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "type": type_,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if organization is not UNSET:
            field_dict["organization"] = organization
        if settings is not UNSET:
            field_dict["settings"] = settings
        if project is not UNSET:
            field_dict["project"] = project
        if description is not UNSET:
            field_dict["description"] = description
        if allow_notes is not UNSET:
            field_dict["allow_notes"] = allow_notes
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if trace_annotations_count is not UNSET:
            field_dict["trace_annotations_count"] = trace_annotations_count
        if annotation_count is not UNSET:
            field_dict["annotation_count"] = annotation_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.annotations_labels_settings import AnnotationsLabelsSettings

        d = dict(src_dict)
        name = d.pop("name")

        type_ = AnnotationsLabelsType(d.pop("type"))

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _organization = d.pop("organization", UNSET)
        organization: UUID | Unset
        if isinstance(_organization, Unset):
            organization = UNSET
        else:
            organization = UUID(_organization)

        _settings = d.pop("settings", UNSET)
        settings: AnnotationsLabelsSettings | Unset
        if isinstance(_settings, Unset):
            settings = UNSET
        else:
            settings = AnnotationsLabelsSettings.from_dict(_settings)

        _project = d.pop("project", UNSET)
        project: UUID | Unset
        if isinstance(_project, Unset):
            project = UNSET
        else:
            project = UUID(_project)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        allow_notes = d.pop("allow_notes", UNSET)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        trace_annotations_count = d.pop("trace_annotations_count", UNSET)

        annotation_count = d.pop("annotation_count", UNSET)

        annotations_labels = cls(
            name=name,
            type_=type_,
            id=id,
            organization=organization,
            settings=settings,
            project=project,
            description=description,
            allow_notes=allow_notes,
            created_at=created_at,
            trace_annotations_count=trace_annotations_count,
            annotation_count=annotation_count,
        )

        annotations_labels.additional_properties = d
        return annotations_labels

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
