from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserAlertMonitorBulkMuteRequest")


@_attrs_define
class UserAlertMonitorBulkMuteRequest:
    """
    Attributes:
        ids (list[UUID] | Unset):
        is_mute (bool | Unset):  Default: True.
        select_all (bool | Unset):  Default: False.
        exclude_ids (list[UUID] | Unset):
    """

    ids: list[UUID] | Unset = UNSET
    is_mute: bool | Unset = True
    select_all: bool | Unset = False
    exclude_ids: list[UUID] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ids: list[str] | Unset = UNSET
        if not isinstance(self.ids, Unset):
            ids = []
            for ids_item_data in self.ids:
                ids_item = str(ids_item_data)
                ids.append(ids_item)

        is_mute = self.is_mute

        select_all = self.select_all

        exclude_ids: list[str] | Unset = UNSET
        if not isinstance(self.exclude_ids, Unset):
            exclude_ids = []
            for exclude_ids_item_data in self.exclude_ids:
                exclude_ids_item = str(exclude_ids_item_data)
                exclude_ids.append(exclude_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if ids is not UNSET:
            field_dict["ids"] = ids
        if is_mute is not UNSET:
            field_dict["is_mute"] = is_mute
        if select_all is not UNSET:
            field_dict["select_all"] = select_all
        if exclude_ids is not UNSET:
            field_dict["exclude_ids"] = exclude_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _ids = d.pop("ids", UNSET)
        ids: list[UUID] | Unset = UNSET
        if _ids is not UNSET:
            ids = []
            for ids_item_data in _ids:
                ids_item = UUID(ids_item_data)

                ids.append(ids_item)

        is_mute = d.pop("is_mute", UNSET)

        select_all = d.pop("select_all", UNSET)

        _exclude_ids = d.pop("exclude_ids", UNSET)
        exclude_ids: list[UUID] | Unset = UNSET
        if _exclude_ids is not UNSET:
            exclude_ids = []
            for exclude_ids_item_data in _exclude_ids:
                exclude_ids_item = UUID(exclude_ids_item_data)

                exclude_ids.append(exclude_ids_item)

        user_alert_monitor_bulk_mute_request = cls(
            ids=ids,
            is_mute=is_mute,
            select_all=select_all,
            exclude_ids=exclude_ids,
        )

        user_alert_monitor_bulk_mute_request.additional_properties = d
        return user_alert_monitor_bulk_mute_request

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
