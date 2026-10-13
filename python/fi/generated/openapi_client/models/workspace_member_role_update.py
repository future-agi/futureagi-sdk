from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.workspace_member_role_update_ws_level import (
    WorkspaceMemberRoleUpdateWsLevel,
)

T = TypeVar("T", bound="WorkspaceMemberRoleUpdate")


@_attrs_define
class WorkspaceMemberRoleUpdate:
    """
    Attributes:
        user_id (UUID):
        ws_level (WorkspaceMemberRoleUpdateWsLevel):
    """

    user_id: UUID
    ws_level: WorkspaceMemberRoleUpdateWsLevel
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = str(self.user_id)

        ws_level = self.ws_level.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "ws_level": ws_level,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_id = UUID(d.pop("user_id"))

        ws_level = WorkspaceMemberRoleUpdateWsLevel(d.pop("ws_level"))

        workspace_member_role_update = cls(
            user_id=user_id,
            ws_level=ws_level,
        )

        workspace_member_role_update.additional_properties = d
        return workspace_member_role_update

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
