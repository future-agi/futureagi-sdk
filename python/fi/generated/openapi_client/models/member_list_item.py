from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.member_list_item_type import MemberListItemType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.member_workspace_access import MemberWorkspaceAccess


T = TypeVar("T", bound="MemberListItem")


@_attrs_define
class MemberListItem:
    """
    Attributes:
        id (UUID):
        name (str):
        email (str):
        status (str):
        created_at (str):
        type_ (MemberListItemType):
        org_level (int | None | Unset):
        org_role (None | str | Unset):
        ws_level (int | None | Unset):
        ws_role (None | str | Unset):
        workspaces (list[MemberWorkspaceAccess] | Unset):
        auto_access (bool | Unset):
    """

    id: UUID
    name: str
    email: str
    status: str
    created_at: str
    type_: MemberListItemType
    org_level: int | None | Unset = UNSET
    org_role: None | str | Unset = UNSET
    ws_level: int | None | Unset = UNSET
    ws_role: None | str | Unset = UNSET
    workspaces: list[MemberWorkspaceAccess] | Unset = UNSET
    auto_access: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        email = self.email

        status = self.status

        created_at = self.created_at

        type_ = self.type_.value

        org_level: int | None | Unset
        if isinstance(self.org_level, Unset):
            org_level = UNSET
        else:
            org_level = self.org_level

        org_role: None | str | Unset
        if isinstance(self.org_role, Unset):
            org_role = UNSET
        else:
            org_role = self.org_role

        ws_level: int | None | Unset
        if isinstance(self.ws_level, Unset):
            ws_level = UNSET
        else:
            ws_level = self.ws_level

        ws_role: None | str | Unset
        if isinstance(self.ws_role, Unset):
            ws_role = UNSET
        else:
            ws_role = self.ws_role

        workspaces: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.workspaces, Unset):
            workspaces = []
            for workspaces_item_data in self.workspaces:
                workspaces_item = workspaces_item_data.to_dict()
                workspaces.append(workspaces_item)

        auto_access = self.auto_access

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "email": email,
                "status": status,
                "created_at": created_at,
                "type": type_,
            }
        )
        if org_level is not UNSET:
            field_dict["org_level"] = org_level
        if org_role is not UNSET:
            field_dict["org_role"] = org_role
        if ws_level is not UNSET:
            field_dict["ws_level"] = ws_level
        if ws_role is not UNSET:
            field_dict["ws_role"] = ws_role
        if workspaces is not UNSET:
            field_dict["workspaces"] = workspaces
        if auto_access is not UNSET:
            field_dict["auto_access"] = auto_access

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.member_workspace_access import MemberWorkspaceAccess

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        email = d.pop("email")

        status = d.pop("status")

        created_at = d.pop("created_at")

        type_ = MemberListItemType(d.pop("type"))

        def _parse_org_level(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        org_level = _parse_org_level(d.pop("org_level", UNSET))

        def _parse_org_role(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        org_role = _parse_org_role(d.pop("org_role", UNSET))

        def _parse_ws_level(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        ws_level = _parse_ws_level(d.pop("ws_level", UNSET))

        def _parse_ws_role(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ws_role = _parse_ws_role(d.pop("ws_role", UNSET))

        _workspaces = d.pop("workspaces", UNSET)
        workspaces: list[MemberWorkspaceAccess] | Unset = UNSET
        if _workspaces is not UNSET:
            workspaces = []
            for workspaces_item_data in _workspaces:
                workspaces_item = MemberWorkspaceAccess.from_dict(workspaces_item_data)

                workspaces.append(workspaces_item)

        auto_access = d.pop("auto_access", UNSET)

        member_list_item = cls(
            id=id,
            name=name,
            email=email,
            status=status,
            created_at=created_at,
            type_=type_,
            org_level=org_level,
            org_role=org_role,
            ws_level=ws_level,
            ws_role=ws_role,
            workspaces=workspaces,
            auto_access=auto_access,
        )

        member_list_item.additional_properties = d
        return member_list_item

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
