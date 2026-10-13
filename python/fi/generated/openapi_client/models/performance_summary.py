from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.performance_summary_test_run_performance_metrics import (
        PerformanceSummaryTestRunPerformanceMetrics,
    )
    from ..models.performance_summary_top_performing_scenarios_item import (
        PerformanceSummaryTopPerformingScenariosItem,
    )


T = TypeVar("T", bound="PerformanceSummary")


@_attrs_define
class PerformanceSummary:
    """
    Attributes:
        test_run_performance_metrics (PerformanceSummaryTestRunPerformanceMetrics): Performance metrics including pass
            rate, total test runs, and latest fail rate
        top_performing_scenarios (list[PerformanceSummaryTopPerformingScenariosItem]): List of top performing scenarios
    """

    test_run_performance_metrics: PerformanceSummaryTestRunPerformanceMetrics
    top_performing_scenarios: list[PerformanceSummaryTopPerformingScenariosItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        test_run_performance_metrics = self.test_run_performance_metrics.to_dict()

        top_performing_scenarios = []
        for top_performing_scenarios_item_data in self.top_performing_scenarios:
            top_performing_scenarios_item = top_performing_scenarios_item_data.to_dict()
            top_performing_scenarios.append(top_performing_scenarios_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "test_run_performance_metrics": test_run_performance_metrics,
                "top_performing_scenarios": top_performing_scenarios,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.performance_summary_test_run_performance_metrics import (
            PerformanceSummaryTestRunPerformanceMetrics,
        )
        from ..models.performance_summary_top_performing_scenarios_item import (
            PerformanceSummaryTopPerformingScenariosItem,
        )

        d = dict(src_dict)
        test_run_performance_metrics = (
            PerformanceSummaryTestRunPerformanceMetrics.from_dict(
                d.pop("test_run_performance_metrics")
            )
        )

        top_performing_scenarios = []
        _top_performing_scenarios = d.pop("top_performing_scenarios")
        for top_performing_scenarios_item_data in _top_performing_scenarios:
            top_performing_scenarios_item = (
                PerformanceSummaryTopPerformingScenariosItem.from_dict(
                    top_performing_scenarios_item_data
                )
            )

            top_performing_scenarios.append(top_performing_scenarios_item)

        performance_summary = cls(
            test_run_performance_metrics=test_run_performance_metrics,
            top_performing_scenarios=top_performing_scenarios,
        )

        performance_summary.additional_properties = d
        return performance_summary

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
