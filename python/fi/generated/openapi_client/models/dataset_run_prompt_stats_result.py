from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.dataset_run_prompt_stats_prompt import DatasetRunPromptStatsPrompt


T = TypeVar("T", bound="DatasetRunPromptStatsResult")


@_attrs_define
class DatasetRunPromptStatsResult:
    """
    Attributes:
        avg_tokens (float):
        avg_cost (float):
        avg_time (float):
        prompts (list[DatasetRunPromptStatsPrompt]):
    """

    avg_tokens: float
    avg_cost: float
    avg_time: float
    prompts: list[DatasetRunPromptStatsPrompt]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        avg_tokens = self.avg_tokens

        avg_cost = self.avg_cost

        avg_time = self.avg_time

        prompts = []
        for prompts_item_data in self.prompts:
            prompts_item = prompts_item_data.to_dict()
            prompts.append(prompts_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "avg_tokens": avg_tokens,
                "avg_cost": avg_cost,
                "avg_time": avg_time,
                "prompts": prompts,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_run_prompt_stats_prompt import DatasetRunPromptStatsPrompt

        d = dict(src_dict)
        avg_tokens = d.pop("avg_tokens")

        avg_cost = d.pop("avg_cost")

        avg_time = d.pop("avg_time")

        prompts = []
        _prompts = d.pop("prompts")
        for prompts_item_data in _prompts:
            prompts_item = DatasetRunPromptStatsPrompt.from_dict(prompts_item_data)

            prompts.append(prompts_item)

        dataset_run_prompt_stats_result = cls(
            avg_tokens=avg_tokens,
            avg_cost=avg_cost,
            avg_time=avg_time,
            prompts=prompts,
        )

        dataset_run_prompt_stats_result.additional_properties = d
        return dataset_run_prompt_stats_result

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
