from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.score import Score


T = TypeVar("T", bound="BulkCreateScoresResult")


@_attrs_define
class BulkCreateScoresResult:
    """
    Attributes:
        scores (list[Score]):
        errors (list[str]):
    """

    scores: list[Score]
    errors: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        scores = []
        for scores_item_data in self.scores:
            scores_item = scores_item_data.to_dict()
            scores.append(scores_item)

        errors = self.errors

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "scores": scores,
                "errors": errors,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.score import Score

        d = dict(src_dict)
        scores = []
        _scores = d.pop("scores")
        for scores_item_data in _scores:
            scores_item = Score.from_dict(scores_item_data)

            scores.append(scores_item)

        errors = cast(list[str], d.pop("errors"))

        bulk_create_scores_result = cls(
            scores=scores,
            errors=errors,
        )

        bulk_create_scores_result.additional_properties = d
        return bulk_create_scores_result

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
