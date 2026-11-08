from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.queue_analytics_annotator_performance import (
        QueueAnalyticsAnnotatorPerformance,
    )
    from ..models.queue_analytics_result_label_distribution import (
        QueueAnalyticsResultLabelDistribution,
    )
    from ..models.queue_analytics_result_status_breakdown import (
        QueueAnalyticsResultStatusBreakdown,
    )
    from ..models.queue_analytics_throughput import QueueAnalyticsThroughput


T = TypeVar("T", bound="QueueAnalyticsResult")


@_attrs_define
class QueueAnalyticsResult:
    """
    Attributes:
        throughput (QueueAnalyticsThroughput):
        annotator_performance (list[QueueAnalyticsAnnotatorPerformance]):
        label_distribution (QueueAnalyticsResultLabelDistribution):
        status_breakdown (QueueAnalyticsResultStatusBreakdown):
        total (int):
    """

    throughput: QueueAnalyticsThroughput
    annotator_performance: list[QueueAnalyticsAnnotatorPerformance]
    label_distribution: QueueAnalyticsResultLabelDistribution
    status_breakdown: QueueAnalyticsResultStatusBreakdown
    total: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        throughput = self.throughput.to_dict()

        annotator_performance = []
        for annotator_performance_item_data in self.annotator_performance:
            annotator_performance_item = annotator_performance_item_data.to_dict()
            annotator_performance.append(annotator_performance_item)

        label_distribution = self.label_distribution.to_dict()

        status_breakdown = self.status_breakdown.to_dict()

        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "throughput": throughput,
                "annotator_performance": annotator_performance,
                "label_distribution": label_distribution,
                "status_breakdown": status_breakdown,
                "total": total,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_analytics_annotator_performance import (
            QueueAnalyticsAnnotatorPerformance,
        )
        from ..models.queue_analytics_result_label_distribution import (
            QueueAnalyticsResultLabelDistribution,
        )
        from ..models.queue_analytics_result_status_breakdown import (
            QueueAnalyticsResultStatusBreakdown,
        )
        from ..models.queue_analytics_throughput import QueueAnalyticsThroughput

        d = dict(src_dict)
        throughput = QueueAnalyticsThroughput.from_dict(d.pop("throughput"))

        annotator_performance = []
        _annotator_performance = d.pop("annotator_performance")
        for annotator_performance_item_data in _annotator_performance:
            annotator_performance_item = QueueAnalyticsAnnotatorPerformance.from_dict(
                annotator_performance_item_data
            )

            annotator_performance.append(annotator_performance_item)

        label_distribution = QueueAnalyticsResultLabelDistribution.from_dict(
            d.pop("label_distribution")
        )

        status_breakdown = QueueAnalyticsResultStatusBreakdown.from_dict(
            d.pop("status_breakdown")
        )

        total = d.pop("total")

        queue_analytics_result = cls(
            throughput=throughput,
            annotator_performance=annotator_performance,
            label_distribution=label_distribution,
            status_breakdown=status_breakdown,
            total=total,
        )

        queue_analytics_result.additional_properties = d
        return queue_analytics_result

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
