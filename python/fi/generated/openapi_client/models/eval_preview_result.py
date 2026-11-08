from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.eval_preview_result_responses_item import (
        EvalPreviewResultResponsesItem,
    )


T = TypeVar("T", bound="EvalPreviewResult")


@_attrs_define
class EvalPreviewResult:
    """
    Attributes:
        responses (list[EvalPreviewResultResponsesItem]):
    """

    responses: list[EvalPreviewResultResponsesItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        responses = []
        for responses_item_data in self.responses:
            responses_item = responses_item_data.to_dict()
            responses.append(responses_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "responses": responses,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_preview_result_responses_item import (
            EvalPreviewResultResponsesItem,
        )

        d = dict(src_dict)
        responses = []
        _responses = d.pop("responses")
        for responses_item_data in _responses:
            responses_item = EvalPreviewResultResponsesItem.from_dict(
                responses_item_data
            )

            responses.append(responses_item)

        eval_preview_result = cls(
            responses=responses,
        )

        eval_preview_result.additional_properties = d
        return eval_preview_result

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
