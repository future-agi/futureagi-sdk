from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.workspace_admin_summary import WorkspaceAdminSummary


T = TypeVar("T", bound="WorkspaceListItemResponse")


@_attrs_define
class WorkspaceListItemResponse:
    """
    Attributes:
        id (UUID):
        name (str):
        display_name (str):
        admin_names (list[WorkspaceAdminSummary] | Unset):
        start_data (str | Unset):
        last_update_date (str | Unset):
        invite_link (str | Unset):
        user_ws_level (int | None | Unset):
        user_ws_role (None | str | Unset):
    """

    id: UUID
    name: str
    display_name: str
    admin_names: list[WorkspaceAdminSummary] | Unset = UNSET
    start_data: str | Unset = UNSET
    last_update_date: str | Unset = UNSET
    invite_link: str | Unset = UNSET
    user_ws_level: int | None | Unset = UNSET
    user_ws_role: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        display_name = self.display_name

        admin_names: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.admin_names, Unset):
            admin_names = []
            for admin_names_item_data in self.admin_names:
                admin_names_item = admin_names_item_data.to_dict()
                admin_names.append(admin_names_item)

        start_data = self.start_data

        last_update_date = self.last_update_date

        invite_link = self.invite_link

        user_ws_level: int | None | Unset
        if isinstance(self.user_ws_level, Unset):
            user_ws_level = UNSET
        else:
            user_ws_level = self.user_ws_level

        user_ws_role: None | str | Unset
        if isinstance(self.user_ws_role, Unset):
            user_ws_role = UNSET
        else:
            user_ws_role = self.user_ws_role

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "display_name": display_name,
            }
        )
        if admin_names is not UNSET:
            field_dict["admin_names"] = admin_names
        if start_data is not UNSET:
            field_dict["start_data"] = start_data
        if last_update_date is not UNSET:
            field_dict["last_update_date"] = last_update_date
        if invite_link is not UNSET:
            field_dict["invite_link"] = invite_link
        if user_ws_level is not UNSET:
            field_dict["user_ws_level"] = user_ws_level
        if user_ws_role is not UNSET:
            field_dict["user_ws_role"] = user_ws_role

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.workspace_admin_summary import WorkspaceAdminSummary

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        display_name = d.pop("display_name")

        _admin_names = d.pop("admin_names", UNSET)
        admin_names: list[WorkspaceAdminSummary] | Unset = UNSET
        if _admin_names is not UNSET:
            admin_names = []
            for admin_names_item_data in _admin_names:
                admin_names_item = WorkspaceAdminSummary.from_dict(
                    admin_names_item_data
                )

                admin_names.append(admin_names_item)

        start_data = d.pop("start_data", UNSET)

        last_update_date = d.pop("last_update_date", UNSET)

        invite_link = d.pop("invite_link", UNSET)

        def _parse_user_ws_level(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        user_ws_level = _parse_user_ws_level(d.pop("user_ws_level", UNSET))

        def _parse_user_ws_role(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_ws_role = _parse_user_ws_role(d.pop("user_ws_role", UNSET))

        workspace_list_item_response = cls(
            id=id,
            name=name,
            display_name=display_name,
            admin_names=admin_names,
            start_data=start_data,
            last_update_date=last_update_date,
            invite_link=invite_link,
            user_ws_level=user_ws_level,
            user_ws_role=user_ws_role,
        )

        workspace_list_item_response.additional_properties = d
        return workspace_list_item_response

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
