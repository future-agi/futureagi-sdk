from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="TrialAggregate")


@_attrs_define
class TrialAggregate:
    """
    Attributes:
        recorded_trial_count (int):
        missing_trial_count (int):
        assessed_trial_count (int):
        score_average (float | None):
        score_min (float | None):
        score_max (float | None):
        score_stddev (float | None):
    """

    recorded_trial_count: int
    missing_trial_count: int
    assessed_trial_count: int
    score_average: float | None
    score_min: float | None
    score_max: float | None
    score_stddev: float | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        recorded_trial_count = self.recorded_trial_count

        missing_trial_count = self.missing_trial_count

        assessed_trial_count = self.assessed_trial_count

        score_average: float | None
        score_average = self.score_average

        score_min: float | None
        score_min = self.score_min

        score_max: float | None
        score_max = self.score_max

        score_stddev: float | None
        score_stddev = self.score_stddev

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "recorded_trial_count": recorded_trial_count,
                "missing_trial_count": missing_trial_count,
                "assessed_trial_count": assessed_trial_count,
                "score_average": score_average,
                "score_min": score_min,
                "score_max": score_max,
                "score_stddev": score_stddev,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        recorded_trial_count = d.pop("recorded_trial_count")

        missing_trial_count = d.pop("missing_trial_count")

        assessed_trial_count = d.pop("assessed_trial_count")

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

        def _parse_score_stddev(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        score_stddev = _parse_score_stddev(d.pop("score_stddev"))

        trial_aggregate = cls(
            recorded_trial_count=recorded_trial_count,
            missing_trial_count=missing_trial_count,
            assessed_trial_count=assessed_trial_count,
            score_average=score_average,
            score_min=score_min,
            score_max=score_max,
            score_stddev=score_stddev,
        )

        trial_aggregate.additional_properties = d
        return trial_aggregate

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
