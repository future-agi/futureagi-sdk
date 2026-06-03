from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserAlertMonitorMetricOption")


@_attrs_define
class UserAlertMonitorMetricOption:
    """
    Attributes:
        id (str | Unset):
        name (str | Unset):
        metric_type (str | Unset):
        output_type (str | Unset):
    """

    id: str | Unset = UNSET
    name: str | Unset = UNSET
    metric_type: str | Unset = UNSET
    output_type: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        metric_type = self.metric_type

        output_type = self.output_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if metric_type is not UNSET:
            field_dict["metric_type"] = metric_type
        if output_type is not UNSET:
            field_dict["output_type"] = output_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        metric_type = d.pop("metric_type", UNSET)

        output_type = d.pop("output_type", UNSET)

        user_alert_monitor_metric_option = cls(
            id=id,
            name=name,
            metric_type=metric_type,
            output_type=output_type,
        )

        user_alert_monitor_metric_option.additional_properties = d
        return user_alert_monitor_metric_option

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
