from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserAlertMonitorLogResolveRequest")


@_attrs_define
class UserAlertMonitorLogResolveRequest:
    """
    Attributes:
        log_ids (list[UUID] | Unset):
        select_all (bool | Unset):  Default: False.
        exclude_ids (list[UUID] | Unset):
    """

    log_ids: list[UUID] | Unset = UNSET
    select_all: bool | Unset = False
    exclude_ids: list[UUID] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        log_ids: list[str] | Unset = UNSET
        if not isinstance(self.log_ids, Unset):
            log_ids = []
            for log_ids_item_data in self.log_ids:
                log_ids_item = str(log_ids_item_data)
                log_ids.append(log_ids_item)

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
        if log_ids is not UNSET:
            field_dict["log_ids"] = log_ids
        if select_all is not UNSET:
            field_dict["select_all"] = select_all
        if exclude_ids is not UNSET:
            field_dict["exclude_ids"] = exclude_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _log_ids = d.pop("log_ids", UNSET)
        log_ids: list[UUID] | Unset = UNSET
        if _log_ids is not UNSET:
            log_ids = []
            for log_ids_item_data in _log_ids:
                log_ids_item = UUID(log_ids_item_data)

                log_ids.append(log_ids_item)

        select_all = d.pop("select_all", UNSET)

        _exclude_ids = d.pop("exclude_ids", UNSET)
        exclude_ids: list[UUID] | Unset = UNSET
        if _exclude_ids is not UNSET:
            exclude_ids = []
            for exclude_ids_item_data in _exclude_ids:
                exclude_ids_item = UUID(exclude_ids_item_data)

                exclude_ids.append(exclude_ids_item)

        user_alert_monitor_log_resolve_request = cls(
            log_ids=log_ids,
            select_all=select_all,
            exclude_ids=exclude_ids,
        )

        user_alert_monitor_log_resolve_request.additional_properties = d
        return user_alert_monitor_log_resolve_request

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
