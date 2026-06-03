from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MemberWorkspaceAccess")


@_attrs_define
class MemberWorkspaceAccess:
    """
    Attributes:
        workspace_id (UUID):
        workspace_name (str):
        ws_level (int):
        ws_role (str):
        auto_access (bool | Unset):
    """

    workspace_id: UUID
    workspace_name: str
    ws_level: int
    ws_role: str
    auto_access: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        workspace_id = str(self.workspace_id)

        workspace_name = self.workspace_name

        ws_level = self.ws_level

        ws_role = self.ws_role

        auto_access = self.auto_access

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "workspace_id": workspace_id,
                "workspace_name": workspace_name,
                "ws_level": ws_level,
                "ws_role": ws_role,
            }
        )
        if auto_access is not UNSET:
            field_dict["auto_access"] = auto_access

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        workspace_id = UUID(d.pop("workspace_id"))

        workspace_name = d.pop("workspace_name")

        ws_level = d.pop("ws_level")

        ws_role = d.pop("ws_role")

        auto_access = d.pop("auto_access", UNSET)

        member_workspace_access = cls(
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            ws_level=ws_level,
            ws_role=ws_role,
            auto_access=auto_access,
        )

        member_workspace_access.additional_properties = d
        return member_workspace_access

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
