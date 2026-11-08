from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.workspace_member_row_type import WorkspaceMemberRowType
from ..types import UNSET, Unset

T = TypeVar("T", bound="WorkspaceMemberRow")


@_attrs_define
class WorkspaceMemberRow:
    """
    Attributes:
        id (UUID):
        name (str):
        email (str):
        status (str):
        created_at (str):
        type_ (WorkspaceMemberRowType):
        ws_level (int | None | Unset):
        ws_role (None | str | Unset):
        org_level (int | None | Unset):
        org_role (None | str | Unset):
        auto_access (bool | Unset):
        invite_link (str | Unset): Accept-invite link for a pending invite. Present on OSS deployments only, where SMTP
            may not be configured; omitted on Cloud/EE, on active-member rows, and on Admin+ invites when the caller is only
            a workspace admin.
    """

    id: UUID
    name: str
    email: str
    status: str
    created_at: str
    type_: WorkspaceMemberRowType
    ws_level: int | None | Unset = UNSET
    ws_role: None | str | Unset = UNSET
    org_level: int | None | Unset = UNSET
    org_role: None | str | Unset = UNSET
    auto_access: bool | Unset = UNSET
    invite_link: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        email = self.email

        status = self.status

        created_at = self.created_at

        type_ = self.type_.value

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

        auto_access = self.auto_access

        invite_link = self.invite_link

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
        if ws_level is not UNSET:
            field_dict["ws_level"] = ws_level
        if ws_role is not UNSET:
            field_dict["ws_role"] = ws_role
        if org_level is not UNSET:
            field_dict["org_level"] = org_level
        if org_role is not UNSET:
            field_dict["org_role"] = org_role
        if auto_access is not UNSET:
            field_dict["auto_access"] = auto_access
        if invite_link is not UNSET:
            field_dict["invite_link"] = invite_link

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        email = d.pop("email")

        status = d.pop("status")

        created_at = d.pop("created_at")

        type_ = WorkspaceMemberRowType(d.pop("type"))

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

        auto_access = d.pop("auto_access", UNSET)

        invite_link = d.pop("invite_link", UNSET)

        workspace_member_row = cls(
            id=id,
            name=name,
            email=email,
            status=status,
            created_at=created_at,
            type_=type_,
            ws_level=ws_level,
            ws_role=ws_role,
            org_level=org_level,
            org_role=org_role,
            auto_access=auto_access,
            invite_link=invite_link,
        )

        workspace_member_row.additional_properties = d
        return workspace_member_row

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
