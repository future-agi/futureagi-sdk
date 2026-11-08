from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.run_aggregate_score_status_counts import RunAggregateScoreStatusCounts
    from ..models.run_aggregate_status_counts import RunAggregateStatusCounts


T = TypeVar("T", bound="RunAggregate")


@_attrs_define
class RunAggregate:
    """
    Attributes:
        item_count (int):
        completed_count (int):
        failed_count (int):
        score_count (int):
        score_average (float | None):
        score_min (float | None):
        score_max (float | None):
        pass_count (int | None):
        pass_rate (float | None):
        status_counts (RunAggregateStatusCounts):
        score_status_counts (RunAggregateScoreStatusCounts):
    """

    item_count: int
    completed_count: int
    failed_count: int
    score_count: int
    score_average: float | None
    score_min: float | None
    score_max: float | None
    pass_count: int | None
    pass_rate: float | None
    status_counts: RunAggregateStatusCounts
    score_status_counts: RunAggregateScoreStatusCounts
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        item_count = self.item_count

        completed_count = self.completed_count

        failed_count = self.failed_count

        score_count = self.score_count

        score_average: float | None
        score_average = self.score_average

        score_min: float | None
        score_min = self.score_min

        score_max: float | None
        score_max = self.score_max

        pass_count: int | None
        pass_count = self.pass_count

        pass_rate: float | None
        pass_rate = self.pass_rate

        status_counts = self.status_counts.to_dict()

        score_status_counts = self.score_status_counts.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "item_count": item_count,
                "completed_count": completed_count,
                "failed_count": failed_count,
                "score_count": score_count,
                "score_average": score_average,
                "score_min": score_min,
                "score_max": score_max,
                "pass_count": pass_count,
                "pass_rate": pass_rate,
                "status_counts": status_counts,
                "score_status_counts": score_status_counts,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_aggregate_score_status_counts import (
            RunAggregateScoreStatusCounts,
        )
        from ..models.run_aggregate_status_counts import RunAggregateStatusCounts

        d = dict(src_dict)
        item_count = d.pop("item_count")

        completed_count = d.pop("completed_count")

        failed_count = d.pop("failed_count")

        score_count = d.pop("score_count")

        def _parse_score_average(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        score_average = _parse_score_average(d.pop("score_average"))

        def _parse_score_min(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        score_min = _parse_score_min(d.pop("score_min"))

        def _parse_score_max(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        score_max = _parse_score_max(d.pop("score_max"))

        def _parse_pass_count(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        pass_count = _parse_pass_count(d.pop("pass_count"))

        def _parse_pass_rate(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        pass_rate = _parse_pass_rate(d.pop("pass_rate"))

        status_counts = RunAggregateStatusCounts.from_dict(d.pop("status_counts"))

        score_status_counts = RunAggregateScoreStatusCounts.from_dict(
            d.pop("score_status_counts")
        )

        run_aggregate = cls(
            item_count=item_count,
            completed_count=completed_count,
            failed_count=failed_count,
            score_count=score_count,
            score_average=score_average,
            score_min=score_min,
            score_max=score_max,
            pass_count=pass_count,
            pass_rate=pass_rate,
            status_counts=status_counts,
            score_status_counts=score_status_counts,
        )

        run_aggregate.additional_properties = d
        return run_aggregate

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
