from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.observe_graph_data_result_metric_statistic import (
    ObserveGraphDataResultMetricStatistic,
)
from ..models.observe_graph_data_result_query_applied_filter_version import (
    ObserveGraphDataResultQueryAppliedFilterVersion,
)
from ..models.observe_graph_data_result_query_error_code import (
    ObserveGraphDataResultQueryErrorCode,
)
from ..models.observe_graph_data_result_query_provenance import (
    ObserveGraphDataResultQueryProvenance,
)
from ..models.observe_graph_data_result_query_sampling_strategy import (
    ObserveGraphDataResultQuerySamplingStrategy,
)
from ..models.observe_graph_data_result_query_status import (
    ObserveGraphDataResultQueryStatus,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.observe_graph_data_point import ObserveGraphDataPoint


T = TypeVar("T", bound="ObserveGraphDataResult")


@_attrs_define
class ObserveGraphDataResult:
    """
    Attributes:
        metric_name (str):
        data (list[ObserveGraphDataPoint]): Graph points. A sampled series is published only with complete declared
            stratum coverage; degraded reads never publish points.
        name (str | Unset):
        metric_statistic (ObserveGraphDataResultMetricStatistic | Unset): Statistic of the published system-metric
            series per bucket. Latency is always the mean (avg) of span latency, filtered or not. Absent for eval and
            annotation series.
        query_complete (bool | Unset):
        query_exact (bool | Unset):
        query_provenance (ObserveGraphDataResultQueryProvenance | Unset):
        query_status (ObserveGraphDataResultQueryStatus | Unset):
        query_error_code (ObserveGraphDataResultQueryErrorCode | Unset):
        query_window_start (str | Unset):
        query_window_end (str | Unset):
        query_applied_filter_version (ObserveGraphDataResultQueryAppliedFilterVersion | Unset):
        query_applied_filter_sha256 (str | Unset):
        query_applied_filter_count (int | Unset):
        query_sample_size (int | Unset):
        query_count (int | Unset):
        query_elapsed_ms (float | Unset):
        query_rows_returned (int | Unset):
        query_result_bytes (int | Unset):
        query_total_rows_lower_bound (int | Unset):
        query_sampled (bool | Unset):
        query_completed_at (datetime.datetime | Unset):
        query_cached (bool | Unset):
        query_refresh_failed (bool | Unset):
        query_refreshing (bool | Unset):
        query_snapshot_version_ceiling (int | Unset):
        query_sampling_strategy (ObserveGraphDataResultQuerySamplingStrategy | Unset):
        query_sampling_strata (int | Unset):
        query_sampling_strata_completed (int | Unset):
    """

    metric_name: str
    data: list[ObserveGraphDataPoint]
    name: str | Unset = UNSET
    metric_statistic: ObserveGraphDataResultMetricStatistic | Unset = UNSET
    query_complete: bool | Unset = UNSET
    query_exact: bool | Unset = UNSET
    query_provenance: ObserveGraphDataResultQueryProvenance | Unset = UNSET
    query_status: ObserveGraphDataResultQueryStatus | Unset = UNSET
    query_error_code: ObserveGraphDataResultQueryErrorCode | Unset = UNSET
    query_window_start: str | Unset = UNSET
    query_window_end: str | Unset = UNSET
    query_applied_filter_version: (
        ObserveGraphDataResultQueryAppliedFilterVersion | Unset
    ) = UNSET
    query_applied_filter_sha256: str | Unset = UNSET
    query_applied_filter_count: int | Unset = UNSET
    query_sample_size: int | Unset = UNSET
    query_count: int | Unset = UNSET
    query_elapsed_ms: float | Unset = UNSET
    query_rows_returned: int | Unset = UNSET
    query_result_bytes: int | Unset = UNSET
    query_total_rows_lower_bound: int | Unset = UNSET
    query_sampled: bool | Unset = UNSET
    query_completed_at: datetime.datetime | Unset = UNSET
    query_cached: bool | Unset = UNSET
    query_refresh_failed: bool | Unset = UNSET
    query_refreshing: bool | Unset = UNSET
    query_snapshot_version_ceiling: int | Unset = UNSET
    query_sampling_strategy: ObserveGraphDataResultQuerySamplingStrategy | Unset = UNSET
    query_sampling_strata: int | Unset = UNSET
    query_sampling_strata_completed: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        metric_name = self.metric_name

        data = []
        for data_item_data in self.data:
            data_item = data_item_data.to_dict()
            data.append(data_item)

        name = self.name

        metric_statistic: str | Unset = UNSET
        if not isinstance(self.metric_statistic, Unset):
            metric_statistic = self.metric_statistic.value

        query_complete = self.query_complete

        query_exact = self.query_exact

        query_provenance: str | Unset = UNSET
        if not isinstance(self.query_provenance, Unset):
            query_provenance = self.query_provenance.value

        query_status: str | Unset = UNSET
        if not isinstance(self.query_status, Unset):
            query_status = self.query_status.value

        query_error_code: str | Unset = UNSET
        if not isinstance(self.query_error_code, Unset):
            query_error_code = self.query_error_code.value

        query_window_start = self.query_window_start

        query_window_end = self.query_window_end

        query_applied_filter_version: str | Unset = UNSET
        if not isinstance(self.query_applied_filter_version, Unset):
            query_applied_filter_version = self.query_applied_filter_version.value

        query_applied_filter_sha256 = self.query_applied_filter_sha256

        query_applied_filter_count = self.query_applied_filter_count

        query_sample_size = self.query_sample_size

        query_count = self.query_count

        query_elapsed_ms = self.query_elapsed_ms

        query_rows_returned = self.query_rows_returned

        query_result_bytes = self.query_result_bytes

        query_total_rows_lower_bound = self.query_total_rows_lower_bound

        query_sampled = self.query_sampled

        query_completed_at: str | Unset = UNSET
        if not isinstance(self.query_completed_at, Unset):
            query_completed_at = self.query_completed_at.isoformat()

        query_cached = self.query_cached

        query_refresh_failed = self.query_refresh_failed

        query_refreshing = self.query_refreshing

        query_snapshot_version_ceiling = self.query_snapshot_version_ceiling

        query_sampling_strategy: str | Unset = UNSET
        if not isinstance(self.query_sampling_strategy, Unset):
            query_sampling_strategy = self.query_sampling_strategy.value

        query_sampling_strata = self.query_sampling_strata

        query_sampling_strata_completed = self.query_sampling_strata_completed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "metric_name": metric_name,
                "data": data,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if metric_statistic is not UNSET:
            field_dict["metric_statistic"] = metric_statistic
        if query_complete is not UNSET:
            field_dict["query_complete"] = query_complete
        if query_exact is not UNSET:
            field_dict["query_exact"] = query_exact
        if query_provenance is not UNSET:
            field_dict["query_provenance"] = query_provenance
        if query_status is not UNSET:
            field_dict["query_status"] = query_status
        if query_error_code is not UNSET:
            field_dict["query_error_code"] = query_error_code
        if query_window_start is not UNSET:
            field_dict["query_window_start"] = query_window_start
        if query_window_end is not UNSET:
            field_dict["query_window_end"] = query_window_end
        if query_applied_filter_version is not UNSET:
            field_dict["query_applied_filter_version"] = query_applied_filter_version
        if query_applied_filter_sha256 is not UNSET:
            field_dict["query_applied_filter_sha256"] = query_applied_filter_sha256
        if query_applied_filter_count is not UNSET:
            field_dict["query_applied_filter_count"] = query_applied_filter_count
        if query_sample_size is not UNSET:
            field_dict["query_sample_size"] = query_sample_size
        if query_count is not UNSET:
            field_dict["query_count"] = query_count
        if query_elapsed_ms is not UNSET:
            field_dict["query_elapsed_ms"] = query_elapsed_ms
        if query_rows_returned is not UNSET:
            field_dict["query_rows_returned"] = query_rows_returned
        if query_result_bytes is not UNSET:
            field_dict["query_result_bytes"] = query_result_bytes
        if query_total_rows_lower_bound is not UNSET:
            field_dict["query_total_rows_lower_bound"] = query_total_rows_lower_bound
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
        if query_snapshot_version_ceiling is not UNSET:
            field_dict["query_snapshot_version_ceiling"] = (
                query_snapshot_version_ceiling
            )
        if query_sampling_strategy is not UNSET:
            field_dict["query_sampling_strategy"] = query_sampling_strategy
        if query_sampling_strata is not UNSET:
            field_dict["query_sampling_strata"] = query_sampling_strata
        if query_sampling_strata_completed is not UNSET:
            field_dict["query_sampling_strata_completed"] = (
                query_sampling_strata_completed
            )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.observe_graph_data_point import ObserveGraphDataPoint

        d = dict(src_dict)
        metric_name = d.pop("metric_name")

        data = []
        _data = d.pop("data")
        for data_item_data in _data:
            data_item = ObserveGraphDataPoint.from_dict(data_item_data)

            data.append(data_item)

        name = d.pop("name", UNSET)

        _metric_statistic = d.pop("metric_statistic", UNSET)
        metric_statistic: ObserveGraphDataResultMetricStatistic | Unset
        if isinstance(_metric_statistic, Unset):
            metric_statistic = UNSET
        else:
            metric_statistic = ObserveGraphDataResultMetricStatistic(_metric_statistic)

        query_complete = d.pop("query_complete", UNSET)

        query_exact = d.pop("query_exact", UNSET)

        _query_provenance = d.pop("query_provenance", UNSET)
        query_provenance: ObserveGraphDataResultQueryProvenance | Unset
        if isinstance(_query_provenance, Unset):
            query_provenance = UNSET
        else:
            query_provenance = ObserveGraphDataResultQueryProvenance(_query_provenance)

        _query_status = d.pop("query_status", UNSET)
        query_status: ObserveGraphDataResultQueryStatus | Unset
        if isinstance(_query_status, Unset):
            query_status = UNSET
        else:
            query_status = ObserveGraphDataResultQueryStatus(_query_status)

        _query_error_code = d.pop("query_error_code", UNSET)
        query_error_code: ObserveGraphDataResultQueryErrorCode | Unset
        if isinstance(_query_error_code, Unset):
            query_error_code = UNSET
        else:
            query_error_code = ObserveGraphDataResultQueryErrorCode(_query_error_code)

        query_window_start = d.pop("query_window_start", UNSET)

        query_window_end = d.pop("query_window_end", UNSET)

        _query_applied_filter_version = d.pop("query_applied_filter_version", UNSET)
        query_applied_filter_version: (
            ObserveGraphDataResultQueryAppliedFilterVersion | Unset
        )
        if isinstance(_query_applied_filter_version, Unset):
            query_applied_filter_version = UNSET
        else:
            query_applied_filter_version = (
                ObserveGraphDataResultQueryAppliedFilterVersion(
                    _query_applied_filter_version
                )
            )

        query_applied_filter_sha256 = d.pop("query_applied_filter_sha256", UNSET)

        query_applied_filter_count = d.pop("query_applied_filter_count", UNSET)

        query_sample_size = d.pop("query_sample_size", UNSET)

        query_count = d.pop("query_count", UNSET)

        query_elapsed_ms = d.pop("query_elapsed_ms", UNSET)

        query_rows_returned = d.pop("query_rows_returned", UNSET)

        query_result_bytes = d.pop("query_result_bytes", UNSET)

        query_total_rows_lower_bound = d.pop("query_total_rows_lower_bound", UNSET)

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

        query_snapshot_version_ceiling = d.pop("query_snapshot_version_ceiling", UNSET)

        _query_sampling_strategy = d.pop("query_sampling_strategy", UNSET)
        query_sampling_strategy: ObserveGraphDataResultQuerySamplingStrategy | Unset
        if isinstance(_query_sampling_strategy, Unset):
            query_sampling_strategy = UNSET
        else:
            query_sampling_strategy = ObserveGraphDataResultQuerySamplingStrategy(
                _query_sampling_strategy
            )

        query_sampling_strata = d.pop("query_sampling_strata", UNSET)

        query_sampling_strata_completed = d.pop(
            "query_sampling_strata_completed", UNSET
        )

        observe_graph_data_result = cls(
            metric_name=metric_name,
            data=data,
            name=name,
            metric_statistic=metric_statistic,
            query_complete=query_complete,
            query_exact=query_exact,
            query_provenance=query_provenance,
            query_status=query_status,
            query_error_code=query_error_code,
            query_window_start=query_window_start,
            query_window_end=query_window_end,
            query_applied_filter_version=query_applied_filter_version,
            query_applied_filter_sha256=query_applied_filter_sha256,
            query_applied_filter_count=query_applied_filter_count,
            query_sample_size=query_sample_size,
            query_count=query_count,
            query_elapsed_ms=query_elapsed_ms,
            query_rows_returned=query_rows_returned,
            query_result_bytes=query_result_bytes,
            query_total_rows_lower_bound=query_total_rows_lower_bound,
            query_sampled=query_sampled,
            query_completed_at=query_completed_at,
            query_cached=query_cached,
            query_refresh_failed=query_refresh_failed,
            query_refreshing=query_refreshing,
            query_snapshot_version_ceiling=query_snapshot_version_ceiling,
            query_sampling_strategy=query_sampling_strategy,
            query_sampling_strata=query_sampling_strata,
            query_sampling_strata_completed=query_sampling_strata_completed,
        )

        observe_graph_data_result.additional_properties = d
        return observe_graph_data_result

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
