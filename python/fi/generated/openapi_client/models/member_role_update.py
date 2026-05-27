from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.member_role_update_org_level import MemberRoleUpdateOrgLevel
from ..models.member_role_update_ws_level import MemberRoleUpdateWsLevel
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.workspace_access_input import WorkspaceAccessInput


T = TypeVar("T", bound="MemberRoleUpdate")


@_attrs_define
class MemberRoleUpdate:
    """
    Attributes:
        user_id (UUID):
        org_level (MemberRoleUpdateOrgLevel | Unset):
        ws_level (MemberRoleUpdateWsLevel | Unset):
        workspace_id (None | Unset | UUID): Required when updating ws_level.
        workspace_access (list[WorkspaceAccessInput] | Unset): List of {workspace_id, level} for explicit workspace
            grants on demotion.
    """

    user_id: UUID
    org_level: MemberRoleUpdateOrgLevel | Unset = UNSET
    ws_level: MemberRoleUpdateWsLevel | Unset = UNSET
    workspace_id: None | Unset | UUID = UNSET
    workspace_access: list[WorkspaceAccessInput] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = str(self.user_id)

        org_level: int | Unset = UNSET
        if not isinstance(self.org_level, Unset):
            org_level = self.org_level.value

        ws_level: int | Unset = UNSET
        if not isinstance(self.ws_level, Unset):
            ws_level = self.ws_level.value

        workspace_id: None | str | Unset
        if isinstance(self.workspace_id, Unset):
            workspace_id = UNSET
        elif isinstance(self.workspace_id, UUID):
            workspace_id = str(self.workspace_id)
        else:
            workspace_id = self.workspace_id

        workspace_access: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.workspace_access, Unset):
            workspace_access = []
            for workspace_access_item_data in self.workspace_access:
                workspace_access_item = workspace_access_item_data.to_dict()
                workspace_access.append(workspace_access_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
            }
        )
        if org_level is not UNSET:
            field_dict["org_level"] = org_level
        if ws_level is not UNSET:
            field_dict["ws_level"] = ws_level
        if workspace_id is not UNSET:
            field_dict["workspace_id"] = workspace_id
        if workspace_access is not UNSET:
            field_dict["workspace_access"] = workspace_access

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.workspace_access_input import WorkspaceAccessInput

        d = dict(src_dict)
        user_id = UUID(d.pop("user_id"))

        _org_level = d.pop("org_level", UNSET)
        org_level: MemberRoleUpdateOrgLevel | Unset
        if isinstance(_org_level, Unset):
            org_level = UNSET
        else:
            org_level = MemberRoleUpdateOrgLevel(_org_level)

        _ws_level = d.pop("ws_level", UNSET)
        ws_level: MemberRoleUpdateWsLevel | Unset
        if isinstance(_ws_level, Unset):
            ws_level = UNSET
        else:
            ws_level = MemberRoleUpdateWsLevel(_ws_level)

        def _parse_workspace_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                workspace_id_type_0 = UUID(data)

                return workspace_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        workspace_id = _parse_workspace_id(d.pop("workspace_id", UNSET))

        _workspace_access = d.pop("workspace_access", UNSET)
        workspace_access: list[WorkspaceAccessInput] | Unset = UNSET
        if _workspace_access is not UNSET:
            workspace_access = []
            for workspace_access_item_data in _workspace_access:
                workspace_access_item = WorkspaceAccessInput.from_dict(
                    workspace_access_item_data
                )

                workspace_access.append(workspace_access_item)

        member_role_update = cls(
            user_id=user_id,
            org_level=org_level,
            ws_level=ws_level,
            workspace_id=workspace_id,
            workspace_access=workspace_access,
        )

        member_role_update.additional_properties = d
        return member_role_update

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
