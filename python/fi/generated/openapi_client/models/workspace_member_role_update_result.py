from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="WorkspaceMemberRoleUpdateResult")


@_attrs_define
class WorkspaceMemberRoleUpdateResult:
    """
    Attributes:
        message (str):
        user_id (UUID):
        ws_level (int):
        ws_role (str):
    """

    message: str
    user_id: UUID
    ws_level: int
    ws_role: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        user_id = str(self.user_id)

        ws_level = self.ws_level

        ws_role = self.ws_role

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "user_id": user_id,
                "ws_level": ws_level,
                "ws_role": ws_role,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message")

        user_id = UUID(d.pop("user_id"))

        ws_level = d.pop("ws_level")

        ws_role = d.pop("ws_role")

        workspace_member_role_update_result = cls(
            message=message,
            user_id=user_id,
            ws_level=ws_level,
            ws_role=ws_role,
        )

        workspace_member_role_update_result.additional_properties = d
        return workspace_member_role_update_result

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
