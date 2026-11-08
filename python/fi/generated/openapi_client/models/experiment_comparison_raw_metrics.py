from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ExperimentComparisonRawMetrics")


@_attrs_define
class ExperimentComparisonRawMetrics:
    """
    Attributes:
        avg_completion_tokens (float | None | Unset):
        avg_total_tokens (float | None | Unset):
        avg_response_time (float | None | Unset):
        avg_score (float | None | Unset):
    """

    avg_completion_tokens: float | None | Unset = UNSET
    avg_total_tokens: float | None | Unset = UNSET
    avg_response_time: float | None | Unset = UNSET
    avg_score: float | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        avg_completion_tokens: float | None | Unset
        if isinstance(self.avg_completion_tokens, Unset):
            avg_completion_tokens = UNSET
        else:
            avg_completion_tokens = self.avg_completion_tokens

        avg_total_tokens: float | None | Unset
        if isinstance(self.avg_total_tokens, Unset):
            avg_total_tokens = UNSET
        else:
            avg_total_tokens = self.avg_total_tokens

        avg_response_time: float | None | Unset
        if isinstance(self.avg_response_time, Unset):
            avg_response_time = UNSET
        else:
            avg_response_time = self.avg_response_time

        avg_score: float | None | Unset
        if isinstance(self.avg_score, Unset):
            avg_score = UNSET
        else:
            avg_score = self.avg_score

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if avg_completion_tokens is not UNSET:
            field_dict["avg_completion_tokens"] = avg_completion_tokens
        if avg_total_tokens is not UNSET:
            field_dict["avg_total_tokens"] = avg_total_tokens
        if avg_response_time is not UNSET:
            field_dict["avg_response_time"] = avg_response_time
        if avg_score is not UNSET:
            field_dict["avg_score"] = avg_score

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_avg_completion_tokens(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        avg_completion_tokens = _parse_avg_completion_tokens(
            d.pop("avg_completion_tokens", UNSET)
        )

        def _parse_avg_total_tokens(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        avg_total_tokens = _parse_avg_total_tokens(d.pop("avg_total_tokens", UNSET))

        def _parse_avg_response_time(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        avg_response_time = _parse_avg_response_time(d.pop("avg_response_time", UNSET))

        def _parse_avg_score(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        avg_score = _parse_avg_score(d.pop("avg_score", UNSET))

        experiment_comparison_raw_metrics = cls(
            avg_completion_tokens=avg_completion_tokens,
            avg_total_tokens=avg_total_tokens,
            avg_response_time=avg_response_time,
            avg_score=avg_score,
        )

        experiment_comparison_raw_metrics.additional_properties = d
        return experiment_comparison_raw_metrics

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
