from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="WorkspaceSummary")


@_attrs_define
class WorkspaceSummary:
    """
    Attributes:
        id (UUID):
        name (str):
        display_name (str):
        description (str | Unset):
        is_default (bool | Unset):
    """

    id: UUID
    name: str
    display_name: str
    description: str | Unset = UNSET
    is_default: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        display_name = self.display_name

        description = self.description

        is_default = self.is_default

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "display_name": display_name,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if is_default is not UNSET:
            field_dict["is_default"] = is_default

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        display_name = d.pop("display_name")

        description = d.pop("description", UNSET)

        is_default = d.pop("is_default", UNSET)

        workspace_summary = cls(
            id=id,
            name=name,
            display_name=display_name,
            description=description,
            is_default=is_default,
        )

        workspace_summary.additional_properties = d
        return workspace_summary

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
