from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.eval_usage_stats_response_result_completeness import (
    EvalUsageStatsResponseResultCompleteness,
)
from ..models.eval_usage_stats_response_result_query_status import (
    EvalUsageStatsResponseResultQueryStatus,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_usage_chart_point import EvalUsageChartPoint
    from ..models.eval_usage_pagination import EvalUsagePagination
    from ..models.eval_usage_stats import EvalUsageStats
    from ..models.eval_usage_table_row import EvalUsageTableRow


T = TypeVar("T", bound="EvalUsageStatsResponseResult")


@_attrs_define
class EvalUsageStatsResponseResult:
    """
    Attributes:
        template_id (UUID):
        is_composite (bool):
        stats (EvalUsageStats):
        chart (list[EvalUsageChartPoint]):
        table (list[EvalUsageTableRow]):
        logs (EvalUsagePagination):
        completeness (EvalUsageStatsResponseResultCompleteness | Unset):
        unavailable_fields (list[str] | Unset):
        query_complete (bool | Unset):
        query_status (EvalUsageStatsResponseResultQueryStatus | Unset):
        query_sampled (bool | Unset):
        query_completed_at (datetime.datetime | Unset):
        query_cached (bool | Unset):
        query_refresh_failed (bool | Unset):
        query_refreshing (bool | Unset):
    """

    template_id: UUID
    is_composite: bool
    stats: EvalUsageStats
    chart: list[EvalUsageChartPoint]
    table: list[EvalUsageTableRow]
    logs: EvalUsagePagination
    completeness: EvalUsageStatsResponseResultCompleteness | Unset = UNSET
    unavailable_fields: list[str] | Unset = UNSET
    query_complete: bool | Unset = UNSET
    query_status: EvalUsageStatsResponseResultQueryStatus | Unset = UNSET
    query_sampled: bool | Unset = UNSET
    query_completed_at: datetime.datetime | Unset = UNSET
    query_cached: bool | Unset = UNSET
    query_refresh_failed: bool | Unset = UNSET
    query_refreshing: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        template_id = str(self.template_id)

        is_composite = self.is_composite

        stats = self.stats.to_dict()

        chart = []
        for chart_item_data in self.chart:
            chart_item = chart_item_data.to_dict()
            chart.append(chart_item)

        table = []
        for table_item_data in self.table:
            table_item = table_item_data.to_dict()
            table.append(table_item)

        logs = self.logs.to_dict()

        completeness: str | Unset = UNSET
        if not isinstance(self.completeness, Unset):
            completeness = self.completeness.value

        unavailable_fields: list[str] | Unset = UNSET
        if not isinstance(self.unavailable_fields, Unset):
            unavailable_fields = self.unavailable_fields

        query_complete = self.query_complete

        query_status: str | Unset = UNSET
        if not isinstance(self.query_status, Unset):
            query_status = self.query_status.value

        query_sampled = self.query_sampled

        query_completed_at: str | Unset = UNSET
        if not isinstance(self.query_completed_at, Unset):
            query_completed_at = self.query_completed_at.isoformat()

        query_cached = self.query_cached

        query_refresh_failed = self.query_refresh_failed

        query_refreshing = self.query_refreshing

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "template_id": template_id,
                "is_composite": is_composite,
                "stats": stats,
                "chart": chart,
                "table": table,
                "logs": logs,
            }
        )
        if completeness is not UNSET:
            field_dict["completeness"] = completeness
        if unavailable_fields is not UNSET:
            field_dict["unavailable_fields"] = unavailable_fields
        if query_complete is not UNSET:
            field_dict["query_complete"] = query_complete
        if query_status is not UNSET:
            field_dict["query_status"] = query_status
        if query_sampled is not UNSET:
            field_dict["query_sampled"] = query_sampled
        if query_completed_at is not UNSET:
            field_dict["query_completed_at"] = query_completed_at
        if query_cached is not UNSET:
            field_dict["query_cached"] = query_cached
        if query_refresh_failed is not UNSET:
            field_dict["query_refresh_failed"] = query_refresh_failed
        if query_refreshing is not UNSET:
            field_dict["query_refreshing"] = query_refreshing

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_usage_chart_point import EvalUsageChartPoint
        from ..models.eval_usage_pagination import EvalUsagePagination
        from ..models.eval_usage_stats import EvalUsageStats
        from ..models.eval_usage_table_row import EvalUsageTableRow

        d = dict(src_dict)
        template_id = UUID(d.pop("template_id"))

        is_composite = d.pop("is_composite")

        stats = EvalUsageStats.from_dict(d.pop("stats"))

        chart = []
        _chart = d.pop("chart")
        for chart_item_data in _chart:
            chart_item = EvalUsageChartPoint.from_dict(chart_item_data)

            chart.append(chart_item)

        table = []
        _table = d.pop("table")
        for table_item_data in _table:
            table_item = EvalUsageTableRow.from_dict(table_item_data)

            table.append(table_item)

        logs = EvalUsagePagination.from_dict(d.pop("logs"))

        _completeness = d.pop("completeness", UNSET)
        completeness: EvalUsageStatsResponseResultCompleteness | Unset
        if isinstance(_completeness, Unset):
            completeness = UNSET
        else:
            completeness = EvalUsageStatsResponseResultCompleteness(_completeness)

        unavailable_fields = cast(list[str], d.pop("unavailable_fields", UNSET))

        query_complete = d.pop("query_complete", UNSET)

        _query_status = d.pop("query_status", UNSET)
        query_status: EvalUsageStatsResponseResultQueryStatus | Unset
        if isinstance(_query_status, Unset):
            query_status = UNSET
        else:
            query_status = EvalUsageStatsResponseResultQueryStatus(_query_status)

        query_sampled = d.pop("query_sampled", UNSET)

        _query_completed_at = d.pop("query_completed_at", UNSET)
        query_completed_at: datetime.datetime | Unset
        if isinstance(_query_completed_at, Unset):
            query_completed_at = UNSET
        else:
            query_completed_at = isoparse(_query_completed_at)

        query_cached = d.pop("query_cached", UNSET)

        query_refresh_failed = d.pop("query_refresh_failed", UNSET)

        query_refreshing = d.pop("query_refreshing", UNSET)

        eval_usage_stats_response_result = cls(
            template_id=template_id,
            is_composite=is_composite,
            stats=stats,
            chart=chart,
            table=table,
            logs=logs,
            completeness=completeness,
            unavailable_fields=unavailable_fields,
            query_complete=query_complete,
            query_status=query_status,
            query_sampled=query_sampled,
            query_completed_at=query_completed_at,
            query_cached=query_cached,
            query_refresh_failed=query_refresh_failed,
            query_refreshing=query_refreshing,
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
