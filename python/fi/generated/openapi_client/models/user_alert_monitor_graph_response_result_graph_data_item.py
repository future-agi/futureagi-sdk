from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="UserAlertMonitorGraphResponseResultGraphDataItem")


@_attrs_define
class UserAlertMonitorGraphResponseResultGraphDataItem:
    """
    Attributes:
        timestamp (str):
        value (float):
    """

    timestamp: str
    value: float

    def to_dict(self) -> dict[str, Any]:
        timestamp = self.timestamp

        value = self.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "timestamp": timestamp,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        timestamp = d.pop("timestamp")

        value = d.pop("value")

        user_alert_monitor_graph_response_result_graph_data_item = cls(
            timestamp=timestamp,
            value=value,
        )

        return user_alert_monitor_graph_response_result_graph_data_item
