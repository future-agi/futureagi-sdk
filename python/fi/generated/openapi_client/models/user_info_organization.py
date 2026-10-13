from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserInfoOrganization")


@_attrs_define
class UserInfoOrganization:
    """
    Attributes:
        id (UUID):
        name (str):
        display_name (str):
        ws_enabled (bool | Unset):
    """

    id: UUID
    name: str
    display_name: str
    ws_enabled: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        display_name = self.display_name

        ws_enabled = self.ws_enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "display_name": display_name,
            }
        )
        if ws_enabled is not UNSET:
            field_dict["ws_enabled"] = ws_enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        display_name = d.pop("display_name")

        ws_enabled = d.pop("ws_enabled", UNSET)

        user_info_organization = cls(
            id=id,
            name=name,
            display_name=display_name,
            ws_enabled=ws_enabled,
        )

        user_info_organization.additional_properties = d
        return user_info_organization

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
