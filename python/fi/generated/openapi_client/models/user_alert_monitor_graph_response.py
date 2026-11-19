from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user_alert_monitor_graph_response_result import (
        UserAlertMonitorGraphResponseResult,
    )


T = TypeVar("T", bound="UserAlertMonitorGraphResponse")


@_attrs_define
class UserAlertMonitorGraphResponse:
    """
    Attributes:
        result (UserAlertMonitorGraphResponseResult): Static monitors return an array of graph points; percentage-change
            monitors return graph_data and alert_bar_data arrays.
        status (bool | Unset):  Default: True.
    """

    result: UserAlertMonitorGraphResponseResult
    status: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = self.result.to_dict()

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "result": result,
            }
        )
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user_alert_monitor_graph_response_result import (
            UserAlertMonitorGraphResponseResult,
        )

        d = dict(src_dict)
        result = UserAlertMonitorGraphResponseResult.from_dict(d.pop("result"))

        status = d.pop("status", UNSET)

        user_alert_monitor_graph_response = cls(
            result=result,
            status=status,
        )

        user_alert_monitor_graph_response.additional_properties = d
        return user_alert_monitor_graph_response

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
