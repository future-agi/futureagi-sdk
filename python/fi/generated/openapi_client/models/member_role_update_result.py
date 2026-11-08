from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.member_role_update_result_changes import MemberRoleUpdateResultChanges


T = TypeVar("T", bound="MemberRoleUpdateResult")


@_attrs_define
class MemberRoleUpdateResult:
    """
    Attributes:
        message (str):
        changes (MemberRoleUpdateResultChanges):
    """

    message: str
    changes: MemberRoleUpdateResultChanges
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        changes = self.changes.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "changes": changes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.member_role_update_result_changes import (
            MemberRoleUpdateResultChanges,
        )

        d = dict(src_dict)
        message = d.pop("message")

        changes = MemberRoleUpdateResultChanges.from_dict(d.pop("changes"))

        member_role_update_result = cls(
            message=message,
            changes=changes,
        )

        member_role_update_result.additional_properties = d
        return member_role_update_result

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
