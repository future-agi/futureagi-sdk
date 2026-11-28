from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ExperimentComparisonNormalizedMetrics")


@_attrs_define
class ExperimentComparisonNormalizedMetrics:
    """
    Attributes:
        completion_tokens (float | None | Unset):
        total_tokens (float | None | Unset):
        response_time (float | None | Unset):
        score (float | None | Unset):
    """

    completion_tokens: float | None | Unset = UNSET
    total_tokens: float | None | Unset = UNSET
    response_time: float | None | Unset = UNSET
    score: float | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        completion_tokens: float | None | Unset
        if isinstance(self.completion_tokens, Unset):
            completion_tokens = UNSET
        else:
            completion_tokens = self.completion_tokens

        total_tokens: float | None | Unset
        if isinstance(self.total_tokens, Unset):
            total_tokens = UNSET
        else:
            total_tokens = self.total_tokens

        response_time: float | None | Unset
        if isinstance(self.response_time, Unset):
            response_time = UNSET
        else:
            response_time = self.response_time

        score: float | None | Unset
        if isinstance(self.score, Unset):
            score = UNSET
        else:
            score = self.score

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if completion_tokens is not UNSET:
            field_dict["completion_tokens"] = completion_tokens
        if total_tokens is not UNSET:
            field_dict["total_tokens"] = total_tokens
        if response_time is not UNSET:
            field_dict["response_time"] = response_time
        if score is not UNSET:
            field_dict["score"] = score

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_completion_tokens(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        completion_tokens = _parse_completion_tokens(d.pop("completion_tokens", UNSET))

        def _parse_total_tokens(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        total_tokens = _parse_total_tokens(d.pop("total_tokens", UNSET))

        def _parse_response_time(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        response_time = _parse_response_time(d.pop("response_time", UNSET))

        def _parse_score(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        score = _parse_score(d.pop("score", UNSET))

        experiment_comparison_normalized_metrics = cls(
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            response_time=response_time,
            score=score,
        )

        experiment_comparison_normalized_metrics.additional_properties = d
        return experiment_comparison_normalized_metrics

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
