from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="QueueDefaultQueue")


@_attrs_define
class QueueDefaultQueue:
    """
    Attributes:
        id (UUID):
        name (str):
        status (str):
        is_default (bool):
        description (str | Unset):
        instructions (str | Unset):
    """

    id: UUID
    name: str
    status: str
    is_default: bool
    description: str | Unset = UNSET
    instructions: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        status = self.status

        is_default = self.is_default

        description = self.description

        instructions = self.instructions

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "status": status,
                "is_default": is_default,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if instructions is not UNSET:
            field_dict["instructions"] = instructions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        status = d.pop("status")

        is_default = d.pop("is_default")

        description = d.pop("description", UNSET)

        instructions = d.pop("instructions", UNSET)

        queue_default_queue = cls(
            id=id,
            name=name,
            status=status,
            is_default=is_default,
            description=description,
            instructions=instructions,
        )

        queue_default_queue.additional_properties = d
        return queue_default_queue

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
