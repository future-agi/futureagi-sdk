from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.user_alert_monitor_graph_response_result_alert_bar_data_item import (
        UserAlertMonitorGraphResponseResultAlertBarDataItem,
    )
    from ..models.user_alert_monitor_graph_response_result_graph_data_item import (
        UserAlertMonitorGraphResponseResultGraphDataItem,
    )


T = TypeVar("T", bound="UserAlertMonitorGraphResponseResult")


@_attrs_define
class UserAlertMonitorGraphResponseResult:
    """Static monitors return an array of graph points; percentage-change monitors return graph_data and alert_bar_data
    arrays.

        Attributes:
            graph_data (list[UserAlertMonitorGraphResponseResultGraphDataItem]):
            alert_bar_data (list[UserAlertMonitorGraphResponseResultAlertBarDataItem]):
    """

    graph_data: list[UserAlertMonitorGraphResponseResultGraphDataItem]
    alert_bar_data: list[UserAlertMonitorGraphResponseResultAlertBarDataItem]

    def to_dict(self) -> dict[str, Any]:
        graph_data = []
        for graph_data_item_data in self.graph_data:
            graph_data_item = graph_data_item_data.to_dict()
            graph_data.append(graph_data_item)

        alert_bar_data = []
        for alert_bar_data_item_data in self.alert_bar_data:
            alert_bar_data_item = alert_bar_data_item_data.to_dict()
            alert_bar_data.append(alert_bar_data_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "graph_data": graph_data,
                "alert_bar_data": alert_bar_data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user_alert_monitor_graph_response_result_alert_bar_data_item import (
            UserAlertMonitorGraphResponseResultAlertBarDataItem,
        )
        from ..models.user_alert_monitor_graph_response_result_graph_data_item import (
            UserAlertMonitorGraphResponseResultGraphDataItem,
        )

        d = dict(src_dict)
        graph_data = []
        _graph_data = d.pop("graph_data")
        for graph_data_item_data in _graph_data:
            graph_data_item = (
                UserAlertMonitorGraphResponseResultGraphDataItem.from_dict(
                    graph_data_item_data
                )
            )

            graph_data.append(graph_data_item)

        alert_bar_data = []
        _alert_bar_data = d.pop("alert_bar_data")
        for alert_bar_data_item_data in _alert_bar_data:
            alert_bar_data_item = (
                UserAlertMonitorGraphResponseResultAlertBarDataItem.from_dict(
                    alert_bar_data_item_data
                )
            )

            alert_bar_data.append(alert_bar_data_item)

        user_alert_monitor_graph_response_result = cls(
            graph_data=graph_data,
            alert_bar_data=alert_bar_data,
        )

        return user_alert_monitor_graph_response_result
