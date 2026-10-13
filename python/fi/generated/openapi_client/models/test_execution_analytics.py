from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.test_execution_analytics_evaluation_categories_over_test_runs import (
        TestExecutionAnalyticsEvaluationCategoriesOverTestRuns,
    )
    from ..models.test_execution_analytics_fail_rate_over_test_runs import (
        TestExecutionAnalyticsFailRateOverTestRuns,
    )
    from ..models.test_execution_analytics_metadata import (
        TestExecutionAnalyticsMetadata,
    )


T = TypeVar("T", bound="TestExecutionAnalytics")


@_attrs_define
class TestExecutionAnalytics:
    """
    Attributes:
        fail_rate_over_test_runs (TestExecutionAnalyticsFailRateOverTestRuns): Fail rate data for scatter plot chart
        evaluation_categories_over_test_runs (TestExecutionAnalyticsEvaluationCategoriesOverTestRuns): Evaluation
            categories data for line graph chart
        metadata (TestExecutionAnalyticsMetadata): Metadata about the analytics data
    """

    fail_rate_over_test_runs: TestExecutionAnalyticsFailRateOverTestRuns
    evaluation_categories_over_test_runs: (
        TestExecutionAnalyticsEvaluationCategoriesOverTestRuns
    )
    metadata: TestExecutionAnalyticsMetadata
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        fail_rate_over_test_runs = self.fail_rate_over_test_runs.to_dict()

        evaluation_categories_over_test_runs = (
            self.evaluation_categories_over_test_runs.to_dict()
        )

        metadata = self.metadata.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "fail_rate_over_test_runs": fail_rate_over_test_runs,
                "evaluation_categories_over_test_runs": evaluation_categories_over_test_runs,
                "metadata": metadata,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.test_execution_analytics_evaluation_categories_over_test_runs import (
            TestExecutionAnalyticsEvaluationCategoriesOverTestRuns,
        )
        from ..models.test_execution_analytics_fail_rate_over_test_runs import (
            TestExecutionAnalyticsFailRateOverTestRuns,
        )
        from ..models.test_execution_analytics_metadata import (
            TestExecutionAnalyticsMetadata,
        )

        d = dict(src_dict)
        fail_rate_over_test_runs = TestExecutionAnalyticsFailRateOverTestRuns.from_dict(
            d.pop("fail_rate_over_test_runs")
        )

        evaluation_categories_over_test_runs = (
            TestExecutionAnalyticsEvaluationCategoriesOverTestRuns.from_dict(
                d.pop("evaluation_categories_over_test_runs")
            )
        )

        metadata = TestExecutionAnalyticsMetadata.from_dict(d.pop("metadata"))

        test_execution_analytics = cls(
            fail_rate_over_test_runs=fail_rate_over_test_runs,
            evaluation_categories_over_test_runs=evaluation_categories_over_test_runs,
            metadata=metadata,
        )

        test_execution_analytics.additional_properties = d
        return test_execution_analytics

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
