from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.user_alert_monitor_graph_response_result_alert_bar_data_item_status import (
    UserAlertMonitorGraphResponseResultAlertBarDataItemStatus,
)

T = TypeVar("T", bound="UserAlertMonitorGraphResponseResultAlertBarDataItem")


@_attrs_define
class UserAlertMonitorGraphResponseResultAlertBarDataItem:
    """
    Attributes:
        start_timestamp (str):
        end_timestamp (str):
        status (UserAlertMonitorGraphResponseResultAlertBarDataItemStatus):
    """

    start_timestamp: str
    end_timestamp: str
    status: UserAlertMonitorGraphResponseResultAlertBarDataItemStatus

    def to_dict(self) -> dict[str, Any]:
        start_timestamp = self.start_timestamp

        end_timestamp = self.end_timestamp

        status = self.status.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "start_timestamp": start_timestamp,
                "end_timestamp": end_timestamp,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        start_timestamp = d.pop("start_timestamp")

        end_timestamp = d.pop("end_timestamp")

        status = UserAlertMonitorGraphResponseResultAlertBarDataItemStatus(
            d.pop("status")
        )

        user_alert_monitor_graph_response_result_alert_bar_data_item = cls(
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            status=status,
        )

        return user_alert_monitor_graph_response_result_alert_bar_data_item
