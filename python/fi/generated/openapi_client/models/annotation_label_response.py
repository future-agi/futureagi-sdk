from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.annotation_label_response_settings import (
        AnnotationLabelResponseSettings,
    )


T = TypeVar("T", bound="AnnotationLabelResponse")


@_attrs_define
class AnnotationLabelResponse:
    """
    Attributes:
        id (UUID):
        name (str):
        type_ (str):
        description (None | str | Unset):
        settings (AnnotationLabelResponseSettings | Unset):
    """

    id: UUID
    name: str
    type_: str
    description: None | str | Unset = UNSET
    settings: AnnotationLabelResponseSettings | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        type_ = self.type_

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.settings, Unset):
            settings = self.settings.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "type": type_,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if settings is not UNSET:
            field_dict["settings"] = settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.annotation_label_response_settings import (
            AnnotationLabelResponseSettings,
        )

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        type_ = d.pop("type")

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        _settings = d.pop("settings", UNSET)
        settings: AnnotationLabelResponseSettings | Unset
        if isinstance(_settings, Unset):
            settings = UNSET
        else:
            settings = AnnotationLabelResponseSettings.from_dict(_settings)

        annotation_label_response = cls(
            id=id,
            name=name,
            type_=type_,
            description=description,
            settings=settings,
        )

        annotation_label_response.additional_properties = d
        return annotation_label_response

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
