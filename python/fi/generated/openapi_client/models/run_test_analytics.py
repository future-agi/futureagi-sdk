from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_test_analytics_evaluation_score_trends_item import (
        RunTestAnalyticsEvaluationScoreTrendsItem,
    )
    from ..models.run_test_analytics_fail_rate_trends_item import (
        RunTestAnalyticsFailRateTrendsItem,
    )
    from ..models.run_test_analytics_performance_comparison_item import (
        RunTestAnalyticsPerformanceComparisonItem,
    )
    from ..models.run_test_analytics_run_test_info import RunTestAnalyticsRunTestInfo
    from ..models.run_test_analytics_summary_stats import RunTestAnalyticsSummaryStats


T = TypeVar("T", bound="RunTestAnalytics")


@_attrs_define
class RunTestAnalytics:
    """
    Attributes:
        run_test_info (RunTestAnalyticsRunTestInfo): Run test metadata
        fail_rate_trends (list[RunTestAnalyticsFailRateTrendsItem]): Fail-rate trend points
        evaluation_score_trends (list[RunTestAnalyticsEvaluationScoreTrendsItem]): Evaluation score trend points
        performance_comparison (list[RunTestAnalyticsPerformanceComparisonItem]): Per-execution performance rows
        summary_stats (RunTestAnalyticsSummaryStats | Unset): Aggregate performance summary
    """

    run_test_info: RunTestAnalyticsRunTestInfo
    fail_rate_trends: list[RunTestAnalyticsFailRateTrendsItem]
    evaluation_score_trends: list[RunTestAnalyticsEvaluationScoreTrendsItem]
    performance_comparison: list[RunTestAnalyticsPerformanceComparisonItem]
    summary_stats: RunTestAnalyticsSummaryStats | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        run_test_info = self.run_test_info.to_dict()

        fail_rate_trends = []
        for fail_rate_trends_item_data in self.fail_rate_trends:
            fail_rate_trends_item = fail_rate_trends_item_data.to_dict()
            fail_rate_trends.append(fail_rate_trends_item)

        evaluation_score_trends = []
        for evaluation_score_trends_item_data in self.evaluation_score_trends:
            evaluation_score_trends_item = evaluation_score_trends_item_data.to_dict()
            evaluation_score_trends.append(evaluation_score_trends_item)

        performance_comparison = []
        for performance_comparison_item_data in self.performance_comparison:
            performance_comparison_item = performance_comparison_item_data.to_dict()
            performance_comparison.append(performance_comparison_item)

        summary_stats: dict[str, Any] | Unset = UNSET
        if not isinstance(self.summary_stats, Unset):
            summary_stats = self.summary_stats.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "run_test_info": run_test_info,
                "fail_rate_trends": fail_rate_trends,
                "evaluation_score_trends": evaluation_score_trends,
                "performance_comparison": performance_comparison,
            }
        )
        if summary_stats is not UNSET:
            field_dict["summary_stats"] = summary_stats

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_test_analytics_evaluation_score_trends_item import (
            RunTestAnalyticsEvaluationScoreTrendsItem,
        )
        from ..models.run_test_analytics_fail_rate_trends_item import (
            RunTestAnalyticsFailRateTrendsItem,
        )
        from ..models.run_test_analytics_performance_comparison_item import (
            RunTestAnalyticsPerformanceComparisonItem,
        )
        from ..models.run_test_analytics_run_test_info import (
            RunTestAnalyticsRunTestInfo,
        )
        from ..models.run_test_analytics_summary_stats import (
            RunTestAnalyticsSummaryStats,
        )

        d = dict(src_dict)
        run_test_info = RunTestAnalyticsRunTestInfo.from_dict(d.pop("run_test_info"))

        fail_rate_trends = []
        _fail_rate_trends = d.pop("fail_rate_trends")
        for fail_rate_trends_item_data in _fail_rate_trends:
            fail_rate_trends_item = RunTestAnalyticsFailRateTrendsItem.from_dict(
                fail_rate_trends_item_data
            )

            fail_rate_trends.append(fail_rate_trends_item)

        evaluation_score_trends = []
        _evaluation_score_trends = d.pop("evaluation_score_trends")
        for evaluation_score_trends_item_data in _evaluation_score_trends:
            evaluation_score_trends_item = (
                RunTestAnalyticsEvaluationScoreTrendsItem.from_dict(
                    evaluation_score_trends_item_data
                )
            )

            evaluation_score_trends.append(evaluation_score_trends_item)

        performance_comparison = []
        _performance_comparison = d.pop("performance_comparison")
        for performance_comparison_item_data in _performance_comparison:
            performance_comparison_item = (
                RunTestAnalyticsPerformanceComparisonItem.from_dict(
                    performance_comparison_item_data
                )
            )

            performance_comparison.append(performance_comparison_item)

        _summary_stats = d.pop("summary_stats", UNSET)
        summary_stats: RunTestAnalyticsSummaryStats | Unset
        if isinstance(_summary_stats, Unset):
            summary_stats = UNSET
        else:
            summary_stats = RunTestAnalyticsSummaryStats.from_dict(_summary_stats)

        run_test_analytics = cls(
            run_test_info=run_test_info,
            fail_rate_trends=fail_rate_trends,
            evaluation_score_trends=evaluation_score_trends,
            performance_comparison=performance_comparison,
            summary_stats=summary_stats,
        )

        run_test_analytics.additional_properties = d
        return run_test_analytics

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
