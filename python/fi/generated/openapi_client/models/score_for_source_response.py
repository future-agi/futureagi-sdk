from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.score import Score
    from ..models.score_for_source_response_span_notes_item import (
        ScoreForSourceResponseSpanNotesItem,
    )


T = TypeVar("T", bound="ScoreForSourceResponse")


@_attrs_define
class ScoreForSourceResponse:
    """
    Attributes:
        result (list[Score]):
        status (bool | Unset):  Default: True.
        span_notes (list[ScoreForSourceResponseSpanNotesItem] | Unset):
    """

    result: list[Score]
    status: bool | Unset = True
    span_notes: list[ScoreForSourceResponseSpanNotesItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = []
        for result_item_data in self.result:
            result_item = result_item_data.to_dict()
            result.append(result_item)

        status = self.status

        span_notes: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.span_notes, Unset):
            span_notes = []
            for span_notes_item_data in self.span_notes:
                span_notes_item = span_notes_item_data.to_dict()
                span_notes.append(span_notes_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "result": result,
            }
        )
        if status is not UNSET:
            field_dict["status"] = status
        if span_notes is not UNSET:
            field_dict["span_notes"] = span_notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.score import Score
        from ..models.score_for_source_response_span_notes_item import (
            ScoreForSourceResponseSpanNotesItem,
        )

        d = dict(src_dict)
        result = []
        _result = d.pop("result")
        for result_item_data in _result:
            result_item = Score.from_dict(result_item_data)

            result.append(result_item)

        status = d.pop("status", UNSET)

        _span_notes = d.pop("span_notes", UNSET)
        span_notes: list[ScoreForSourceResponseSpanNotesItem] | Unset = UNSET
        if _span_notes is not UNSET:
            span_notes = []
            for span_notes_item_data in _span_notes:
                span_notes_item = ScoreForSourceResponseSpanNotesItem.from_dict(
                    span_notes_item_data
                )

                span_notes.append(span_notes_item)

        score_for_source_response = cls(
            result=result,
            status=status,
            span_notes=span_notes,
        )

        score_for_source_response.additional_properties = d
        return score_for_source_response

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
