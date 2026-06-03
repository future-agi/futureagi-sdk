from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.queue_label_result_settings import QueueLabelResultSettings


T = TypeVar("T", bound="QueueLabelResult")


@_attrs_define
class QueueLabelResult:
    """
    Attributes:
        id (UUID):
        name (str):
        type_ (str):
        settings (QueueLabelResultSettings):
        allow_notes (bool):
        required (bool):
        order (int):
        description (str | Unset):
    """

    id: UUID
    name: str
    type_: str
    settings: QueueLabelResultSettings
    allow_notes: bool
    required: bool
    order: int
    description: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        type_ = self.type_

        settings = self.settings.to_dict()

        allow_notes = self.allow_notes

        required = self.required

        order = self.order

        description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "type": type_,
                "settings": settings,
                "allow_notes": allow_notes,
                "required": required,
                "order": order,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_label_result_settings import QueueLabelResultSettings

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        type_ = d.pop("type")

        settings = QueueLabelResultSettings.from_dict(d.pop("settings"))

        allow_notes = d.pop("allow_notes")

        required = d.pop("required")

        order = d.pop("order")

        description = d.pop("description", UNSET)

        queue_label_result = cls(
            id=id,
            name=name,
            type_=type_,
            settings=settings,
            allow_notes=allow_notes,
            required=required,
            order=order,
            description=description,
        )

        queue_label_result.additional_properties = d
        return queue_label_result

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
