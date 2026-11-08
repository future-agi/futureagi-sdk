from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.experiment_comparison_weights_scores import (
        ExperimentComparisonWeightsScores,
    )


T = TypeVar("T", bound="ExperimentComparisonWeights")


@_attrs_define
class ExperimentComparisonWeights:
    """
    Attributes:
        response_time (float | None | Unset):
        scores (ExperimentComparisonWeightsScores | Unset):
        total_tokens (float | None | Unset):
        completion_tokens (float | None | Unset):
    """

    response_time: float | None | Unset = UNSET
    scores: ExperimentComparisonWeightsScores | Unset = UNSET
    total_tokens: float | None | Unset = UNSET
    completion_tokens: float | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        response_time: float | None | Unset
        if isinstance(self.response_time, Unset):
            response_time = UNSET
        else:
            response_time = self.response_time

        scores: dict[str, Any] | Unset = UNSET
        if not isinstance(self.scores, Unset):
            scores = self.scores.to_dict()

        total_tokens: float | None | Unset
        if isinstance(self.total_tokens, Unset):
            total_tokens = UNSET
        else:
            total_tokens = self.total_tokens

        completion_tokens: float | None | Unset
        if isinstance(self.completion_tokens, Unset):
            completion_tokens = UNSET
        else:
            completion_tokens = self.completion_tokens

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if response_time is not UNSET:
            field_dict["response_time"] = response_time
        if scores is not UNSET:
            field_dict["scores"] = scores
        if total_tokens is not UNSET:
            field_dict["total_tokens"] = total_tokens
        if completion_tokens is not UNSET:
            field_dict["completion_tokens"] = completion_tokens

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.experiment_comparison_weights_scores import (
            ExperimentComparisonWeightsScores,
        )

        d = dict(src_dict)

        def _parse_response_time(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        response_time = _parse_response_time(d.pop("response_time", UNSET))

        _scores = d.pop("scores", UNSET)
        scores: ExperimentComparisonWeightsScores | Unset
        if isinstance(_scores, Unset):
            scores = UNSET
        else:
            scores = ExperimentComparisonWeightsScores.from_dict(_scores)

        def _parse_total_tokens(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        total_tokens = _parse_total_tokens(d.pop("total_tokens", UNSET))

        def _parse_completion_tokens(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        completion_tokens = _parse_completion_tokens(d.pop("completion_tokens", UNSET))

        experiment_comparison_weights = cls(
            response_time=response_time,
            scores=scores,
            total_tokens=total_tokens,
            completion_tokens=completion_tokens,
        )

        experiment_comparison_weights.additional_properties = d
        return experiment_comparison_weights

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
