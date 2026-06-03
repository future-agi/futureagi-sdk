from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.bulk_create_scores_source_type import BulkCreateScoresSourceType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.bulk_create_score_item import BulkCreateScoreItem


T = TypeVar("T", bound="BulkCreateScores")


@_attrs_define
class BulkCreateScores:
    """
    Attributes:
        source_type (BulkCreateScoresSourceType):
        source_id (str):
        scores (list[BulkCreateScoreItem]):
        notes (str | Unset):  Default: ''.
        span_notes (None | str | Unset):
        span_notes_source_id (None | str | Unset):
        queue_item_id (None | Unset | UUID):
    """

    source_type: BulkCreateScoresSourceType
    source_id: str
    scores: list[BulkCreateScoreItem]
    notes: str | Unset = ""
    span_notes: None | str | Unset = UNSET
    span_notes_source_id: None | str | Unset = UNSET
    queue_item_id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_type = self.source_type.value

        source_id = self.source_id

        scores = []
        for scores_item_data in self.scores:
            scores_item = scores_item_data.to_dict()
            scores.append(scores_item)

        notes = self.notes

        span_notes: None | str | Unset
        if isinstance(self.span_notes, Unset):
            span_notes = UNSET
        else:
            span_notes = self.span_notes

        span_notes_source_id: None | str | Unset
        if isinstance(self.span_notes_source_id, Unset):
            span_notes_source_id = UNSET
        else:
            span_notes_source_id = self.span_notes_source_id

        queue_item_id: None | str | Unset
        if isinstance(self.queue_item_id, Unset):
            queue_item_id = UNSET
        elif isinstance(self.queue_item_id, UUID):
            queue_item_id = str(self.queue_item_id)
        else:
            queue_item_id = self.queue_item_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "source_type": source_type,
                "source_id": source_id,
                "scores": scores,
            }
        )
        if notes is not UNSET:
            field_dict["notes"] = notes
        if span_notes is not UNSET:
            field_dict["span_notes"] = span_notes
        if span_notes_source_id is not UNSET:
            field_dict["span_notes_source_id"] = span_notes_source_id
        if queue_item_id is not UNSET:
            field_dict["queue_item_id"] = queue_item_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.bulk_create_score_item import BulkCreateScoreItem

        d = dict(src_dict)
        source_type = BulkCreateScoresSourceType(d.pop("source_type"))

        source_id = d.pop("source_id")

        scores = []
        _scores = d.pop("scores")
        for scores_item_data in _scores:
            scores_item = BulkCreateScoreItem.from_dict(scores_item_data)

            scores.append(scores_item)

        notes = d.pop("notes", UNSET)

        def _parse_span_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        span_notes = _parse_span_notes(d.pop("span_notes", UNSET))

        def _parse_span_notes_source_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        span_notes_source_id = _parse_span_notes_source_id(
            d.pop("span_notes_source_id", UNSET)
        )

        def _parse_queue_item_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                queue_item_id_type_0 = UUID(data)

                return queue_item_id_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UUID, data)

        queue_item_id = _parse_queue_item_id(d.pop("queue_item_id", UNSET))

        bulk_create_scores = cls(
            source_type=source_type,
            source_id=source_id,
            scores=scores,
            notes=notes,
            span_notes=span_notes,
            span_notes_source_id=span_notes_source_id,
            queue_item_id=queue_item_id,
        )

        bulk_create_scores.additional_properties = d
        return bulk_create_scores

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
