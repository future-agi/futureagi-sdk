from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.queue_analytics_throughput_daily import QueueAnalyticsThroughputDaily


T = TypeVar("T", bound="QueueAnalyticsThroughput")


@_attrs_define
class QueueAnalyticsThroughput:
    """
    Attributes:
        daily (list[QueueAnalyticsThroughputDaily]):
        total_completed (int):
        avg_per_day (float):
    """

    daily: list[QueueAnalyticsThroughputDaily]
    total_completed: int
    avg_per_day: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        daily = []
        for daily_item_data in self.daily:
            daily_item = daily_item_data.to_dict()
            daily.append(daily_item)

        total_completed = self.total_completed

        avg_per_day = self.avg_per_day

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "daily": daily,
                "total_completed": total_completed,
                "avg_per_day": avg_per_day,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_analytics_throughput_daily import (
            QueueAnalyticsThroughputDaily,
        )

        d = dict(src_dict)
        daily = []
        _daily = d.pop("daily")
        for daily_item_data in _daily:
            daily_item = QueueAnalyticsThroughputDaily.from_dict(daily_item_data)

            daily.append(daily_item)

        total_completed = d.pop("total_completed")

        avg_per_day = d.pop("avg_per_day")

        queue_analytics_throughput = cls(
            daily=daily,
            total_completed=total_completed,
            avg_per_day=avg_per_day,
        )

        queue_analytics_throughput.additional_properties = d
        return queue_analytics_throughput

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
