from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.user_alert_monitor_list_item_status import UserAlertMonitorListItemStatus

if TYPE_CHECKING:
    from ..models.user_alert_monitor_list_item_filters import (
        UserAlertMonitorListItemFilters,
    )
    from ..models.user_alert_monitor_trend import UserAlertMonitorTrend


T = TypeVar("T", bound="UserAlertMonitorListItem")


@_attrs_define
class UserAlertMonitorListItem:
    """
    Attributes:
        id (UUID):
        name (str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        metric_type (str):
        filters (UserAlertMonitorListItemFilters):
        status (UserAlertMonitorListItemStatus):
        no_of_alerts (int):
        last_triggered (datetime.datetime | None):
        is_mute (bool):
        trends (list[UserAlertMonitorTrend]):
    """

    id: UUID
    name: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    metric_type: str
    filters: UserAlertMonitorListItemFilters
    status: UserAlertMonitorListItemStatus
    no_of_alerts: int
    last_triggered: datetime.datetime | None
    is_mute: bool
    trends: list[UserAlertMonitorTrend]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        metric_type = self.metric_type

        filters = self.filters.to_dict()

        status = self.status.value

        no_of_alerts = self.no_of_alerts

        last_triggered: None | str
        if isinstance(self.last_triggered, datetime.datetime):
            last_triggered = self.last_triggered.isoformat()
        else:
            last_triggered = self.last_triggered

        is_mute = self.is_mute

        trends = []
        for trends_item_data in self.trends:
            trends_item = trends_item_data.to_dict()
            trends.append(trends_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "created_at": created_at,
                "updated_at": updated_at,
                "metric_type": metric_type,
                "filters": filters,
                "status": status,
                "no_of_alerts": no_of_alerts,
                "last_triggered": last_triggered,
                "is_mute": is_mute,
                "trends": trends,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user_alert_monitor_list_item_filters import (
            UserAlertMonitorListItemFilters,
        )
        from ..models.user_alert_monitor_trend import UserAlertMonitorTrend

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        metric_type = d.pop("metric_type")

        filters = UserAlertMonitorListItemFilters.from_dict(d.pop("filters"))

        status = UserAlertMonitorListItemStatus(d.pop("status"))

        no_of_alerts = d.pop("no_of_alerts")

        def _parse_last_triggered(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_triggered_type_0 = isoparse(data)

                return last_triggered_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        last_triggered = _parse_last_triggered(d.pop("last_triggered"))

        is_mute = d.pop("is_mute")

        trends = []
        _trends = d.pop("trends")
        for trends_item_data in _trends:
            trends_item = UserAlertMonitorTrend.from_dict(trends_item_data)

            trends.append(trends_item)

        user_alert_monitor_list_item = cls(
            id=id,
            name=name,
            created_at=created_at,
            updated_at=updated_at,
            metric_type=metric_type,
            filters=filters,
            status=status,
            no_of_alerts=no_of_alerts,
            last_triggered=last_triggered,
            is_mute=is_mute,
            trends=trends,
        )

        user_alert_monitor_list_item.additional_properties = d
        return user_alert_monitor_list_item

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
