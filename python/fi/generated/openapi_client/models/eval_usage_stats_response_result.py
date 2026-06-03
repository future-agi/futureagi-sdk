from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.eval_usage_chart_point import EvalUsageChartPoint
    from ..models.eval_usage_logs import EvalUsageLogs
    from ..models.eval_usage_stats import EvalUsageStats


T = TypeVar("T", bound="EvalUsageStatsResponseResult")


@_attrs_define
class EvalUsageStatsResponseResult:
    """
    Attributes:
        template_id (UUID):
        is_composite (bool):
        stats (EvalUsageStats):
        chart (list[EvalUsageChartPoint]):
        logs (EvalUsageLogs):
    """

    template_id: UUID
    is_composite: bool
    stats: EvalUsageStats
    chart: list[EvalUsageChartPoint]
    logs: EvalUsageLogs
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        template_id = str(self.template_id)

        is_composite = self.is_composite

        stats = self.stats.to_dict()

        chart = []
        for chart_item_data in self.chart:
            chart_item = chart_item_data.to_dict()
            chart.append(chart_item)

        logs = self.logs.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "template_id": template_id,
                "is_composite": is_composite,
                "stats": stats,
                "chart": chart,
                "logs": logs,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_usage_chart_point import EvalUsageChartPoint
        from ..models.eval_usage_logs import EvalUsageLogs
        from ..models.eval_usage_stats import EvalUsageStats

        d = dict(src_dict)
        template_id = UUID(d.pop("template_id"))

        is_composite = d.pop("is_composite")

        stats = EvalUsageStats.from_dict(d.pop("stats"))

        chart = []
        _chart = d.pop("chart")
        for chart_item_data in _chart:
            chart_item = EvalUsageChartPoint.from_dict(chart_item_data)

            chart.append(chart_item)

        logs = EvalUsageLogs.from_dict(d.pop("logs"))

        eval_usage_stats_response_result = cls(
            template_id=template_id,
            is_composite=is_composite,
            stats=stats,
            chart=chart,
            logs=logs,
        )

        eval_usage_stats_response_result.additional_properties = d
        return eval_usage_stats_response_result

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
