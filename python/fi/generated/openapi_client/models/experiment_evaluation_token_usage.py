from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ExperimentEvaluationTokenUsage")


@_attrs_define
class ExperimentEvaluationTokenUsage:
    """
    Attributes:
        avg_completion_tokens (float):
        avg_prompt_tokens (float):
        avg_total_tokens (float):
        total_tokens (int):
    """

    avg_completion_tokens: float
    avg_prompt_tokens: float
    avg_total_tokens: float
    total_tokens: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        avg_completion_tokens = self.avg_completion_tokens

        avg_prompt_tokens = self.avg_prompt_tokens

        avg_total_tokens = self.avg_total_tokens

        total_tokens = self.total_tokens

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "avg_completion_tokens": avg_completion_tokens,
                "avg_prompt_tokens": avg_prompt_tokens,
                "avg_total_tokens": avg_total_tokens,
                "total_tokens": total_tokens,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        avg_completion_tokens = d.pop("avg_completion_tokens")

        avg_prompt_tokens = d.pop("avg_prompt_tokens")

        avg_total_tokens = d.pop("avg_total_tokens")

        total_tokens = d.pop("total_tokens")

        experiment_evaluation_token_usage = cls(
            avg_completion_tokens=avg_completion_tokens,
            avg_prompt_tokens=avg_prompt_tokens,
            avg_total_tokens=avg_total_tokens,
            total_tokens=total_tokens,
        )

        experiment_evaluation_token_usage.additional_properties = d
        return experiment_evaluation_token_usage

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
