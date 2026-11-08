from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user_alert_monitor_metric_option import UserAlertMonitorMetricOption


T = TypeVar("T", bound="UserAlertMonitorMetricOptionsResponse")


@_attrs_define
class UserAlertMonitorMetricOptionsResponse:
    """
    Attributes:
        status (bool | Unset):  Default: True.
        result (list[UserAlertMonitorMetricOption] | Unset):
    """

    status: bool | Unset = True
    result: list[UserAlertMonitorMetricOption] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        result: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.result, Unset):
            result = []
            for result_item_data in self.result:
                result_item = result_item_data.to_dict()
                result.append(result_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if status is not UNSET:
            field_dict["status"] = status
        if result is not UNSET:
            field_dict["result"] = result

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user_alert_monitor_metric_option import (
            UserAlertMonitorMetricOption,
        )

        d = dict(src_dict)
        status = d.pop("status", UNSET)

        _result = d.pop("result", UNSET)
        result: list[UserAlertMonitorMetricOption] | Unset = UNSET
        if _result is not UNSET:
            result = []
            for result_item_data in _result:
                result_item = UserAlertMonitorMetricOption.from_dict(result_item_data)

                result.append(result_item)

        user_alert_monitor_metric_options_response = cls(
            status=status,
            result=result,
        )

        user_alert_monitor_metric_options_response.additional_properties = d
        return user_alert_monitor_metric_options_response

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
