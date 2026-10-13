from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.run_prompt_column_preview_result_cost import (
        RunPromptColumnPreviewResultCost,
    )
    from ..models.run_prompt_column_preview_result_responses_item import (
        RunPromptColumnPreviewResultResponsesItem,
    )
    from ..models.run_prompt_column_preview_result_token_usage import (
        RunPromptColumnPreviewResultTokenUsage,
    )


T = TypeVar("T", bound="RunPromptColumnPreviewResult")


@_attrs_define
class RunPromptColumnPreviewResult:
    """
    Attributes:
        responses (list[RunPromptColumnPreviewResultResponsesItem]):
        token_usage (RunPromptColumnPreviewResultTokenUsage):
        cost (RunPromptColumnPreviewResultCost):
    """

    responses: list[RunPromptColumnPreviewResultResponsesItem]
    token_usage: RunPromptColumnPreviewResultTokenUsage
    cost: RunPromptColumnPreviewResultCost
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        responses = []
        for responses_item_data in self.responses:
            responses_item = responses_item_data.to_dict()
            responses.append(responses_item)

        token_usage = self.token_usage.to_dict()

        cost = self.cost.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "responses": responses,
                "token_usage": token_usage,
                "cost": cost,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_prompt_column_preview_result_cost import (
            RunPromptColumnPreviewResultCost,
        )
        from ..models.run_prompt_column_preview_result_responses_item import (
            RunPromptColumnPreviewResultResponsesItem,
        )
        from ..models.run_prompt_column_preview_result_token_usage import (
            RunPromptColumnPreviewResultTokenUsage,
        )

        d = dict(src_dict)
        responses = []
        _responses = d.pop("responses")
        for responses_item_data in _responses:
            responses_item = RunPromptColumnPreviewResultResponsesItem.from_dict(
                responses_item_data
            )

            responses.append(responses_item)

        token_usage = RunPromptColumnPreviewResultTokenUsage.from_dict(
            d.pop("token_usage")
        )

        cost = RunPromptColumnPreviewResultCost.from_dict(d.pop("cost"))

        run_prompt_column_preview_result = cls(
            responses=responses,
            token_usage=token_usage,
            cost=cost,
        )

        run_prompt_column_preview_result.additional_properties = d
        return run_prompt_column_preview_result

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
