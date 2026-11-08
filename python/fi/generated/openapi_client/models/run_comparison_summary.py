from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.run_aggregate import RunAggregate
    from ..models.run_case_comparison import RunCaseComparison
    from ..models.run_comparison_summary_status_counts import (
        RunComparisonSummaryStatusCounts,
    )


T = TypeVar("T", bound="RunComparisonSummary")


@_attrs_define
class RunComparisonSummary:
    """
    Attributes:
        baseline (RunAggregate):
        candidate (RunAggregate):
        cases (list[RunCaseComparison]):
        status_counts (RunComparisonSummaryStatusCounts):
        comparable_count (int):
    """

    baseline: RunAggregate
    candidate: RunAggregate
    cases: list[RunCaseComparison]
    status_counts: RunComparisonSummaryStatusCounts
    comparable_count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        baseline = self.baseline.to_dict()

        candidate = self.candidate.to_dict()

        cases = []
        for cases_item_data in self.cases:
            cases_item = cases_item_data.to_dict()
            cases.append(cases_item)

        status_counts = self.status_counts.to_dict()

        comparable_count = self.comparable_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "baseline": baseline,
                "candidate": candidate,
                "cases": cases,
                "status_counts": status_counts,
                "comparable_count": comparable_count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_aggregate import RunAggregate
        from ..models.run_case_comparison import RunCaseComparison
        from ..models.run_comparison_summary_status_counts import (
            RunComparisonSummaryStatusCounts,
        )

        d = dict(src_dict)
        baseline = RunAggregate.from_dict(d.pop("baseline"))

        candidate = RunAggregate.from_dict(d.pop("candidate"))

        cases = []
        _cases = d.pop("cases")
        for cases_item_data in _cases:
            cases_item = RunCaseComparison.from_dict(cases_item_data)

            cases.append(cases_item)

        status_counts = RunComparisonSummaryStatusCounts.from_dict(
            d.pop("status_counts")
        )

        comparable_count = d.pop("comparable_count")

        run_comparison_summary = cls(
            baseline=baseline,
            candidate=candidate,
            cases=cases,
            status_counts=status_counts,
            comparable_count=comparable_count,
        )

        run_comparison_summary.additional_properties = d
        return run_comparison_summary

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
