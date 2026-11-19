from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="TrialDeltaAggregate")


@_attrs_define
class TrialDeltaAggregate:
    """
    Attributes:
        paired_trial_count (int):
        delta_average (float | None):
        delta_stddev (float | None):
    """

    paired_trial_count: int
    delta_average: float | None
    delta_stddev: float | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        paired_trial_count = self.paired_trial_count

        delta_average: float | None
        delta_average = self.delta_average

        delta_stddev: float | None
        delta_stddev = self.delta_stddev

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "paired_trial_count": paired_trial_count,
                "delta_average": delta_average,
                "delta_stddev": delta_stddev,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        paired_trial_count = d.pop("paired_trial_count")

        def _parse_delta_average(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        delta_average = _parse_delta_average(d.pop("delta_average"))

        def _parse_delta_stddev(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        delta_stddev = _parse_delta_stddev(d.pop("delta_stddev"))

        trial_delta_aggregate = cls(
            paired_trial_count=paired_trial_count,
            delta_average=delta_average,
            delta_stddev=delta_stddev,
        )

        trial_delta_aggregate.additional_properties = d
        return trial_delta_aggregate

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
