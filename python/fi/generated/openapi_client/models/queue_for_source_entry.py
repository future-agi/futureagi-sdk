from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.queue_for_source_entry_existing_label_notes import (
        QueueForSourceEntryExistingLabelNotes,
    )
    from ..models.queue_for_source_entry_existing_scores import (
        QueueForSourceEntryExistingScores,
    )
    from ..models.queue_for_source_entry_span_notes_item import (
        QueueForSourceEntrySpanNotesItem,
    )
    from ..models.queue_for_source_item import QueueForSourceItem
    from ..models.queue_for_source_queue import QueueForSourceQueue
    from ..models.queue_label_result import QueueLabelResult


T = TypeVar("T", bound="QueueForSourceEntry")


@_attrs_define
class QueueForSourceEntry:
    """
    Attributes:
        queue (QueueForSourceQueue):
        item (QueueForSourceItem):
        labels (list[QueueLabelResult]):
        existing_scores (QueueForSourceEntryExistingScores):
        existing_notes (str):
        existing_label_notes (QueueForSourceEntryExistingLabelNotes):
        span_notes (list[QueueForSourceEntrySpanNotesItem]):
        span_notes_source_id (None | str | Unset):
    """

    queue: QueueForSourceQueue
    item: QueueForSourceItem
    labels: list[QueueLabelResult]
    existing_scores: QueueForSourceEntryExistingScores
    existing_notes: str
    existing_label_notes: QueueForSourceEntryExistingLabelNotes
    span_notes: list[QueueForSourceEntrySpanNotesItem]
    span_notes_source_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        queue = self.queue.to_dict()

        item = self.item.to_dict()

        labels = []
        for labels_item_data in self.labels:
            labels_item = labels_item_data.to_dict()
            labels.append(labels_item)

        existing_scores = self.existing_scores.to_dict()

        existing_notes = self.existing_notes

        existing_label_notes = self.existing_label_notes.to_dict()

        span_notes = []
        for span_notes_item_data in self.span_notes:
            span_notes_item = span_notes_item_data.to_dict()
            span_notes.append(span_notes_item)

        span_notes_source_id: None | str | Unset
        if isinstance(self.span_notes_source_id, Unset):
            span_notes_source_id = UNSET
        else:
            span_notes_source_id = self.span_notes_source_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "queue": queue,
                "item": item,
                "labels": labels,
                "existing_scores": existing_scores,
                "existing_notes": existing_notes,
                "existing_label_notes": existing_label_notes,
                "span_notes": span_notes,
            }
        )
        if span_notes_source_id is not UNSET:
            field_dict["span_notes_source_id"] = span_notes_source_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_for_source_entry_existing_label_notes import (
            QueueForSourceEntryExistingLabelNotes,
        )
        from ..models.queue_for_source_entry_existing_scores import (
            QueueForSourceEntryExistingScores,
        )
        from ..models.queue_for_source_entry_span_notes_item import (
            QueueForSourceEntrySpanNotesItem,
        )
        from ..models.queue_for_source_item import QueueForSourceItem
        from ..models.queue_for_source_queue import QueueForSourceQueue
        from ..models.queue_label_result import QueueLabelResult

        d = dict(src_dict)
        queue = QueueForSourceQueue.from_dict(d.pop("queue"))

        item = QueueForSourceItem.from_dict(d.pop("item"))

        labels = []
        _labels = d.pop("labels")
        for labels_item_data in _labels:
            labels_item = QueueLabelResult.from_dict(labels_item_data)

            labels.append(labels_item)

        existing_scores = QueueForSourceEntryExistingScores.from_dict(
            d.pop("existing_scores")
        )

        existing_notes = d.pop("existing_notes")

        existing_label_notes = QueueForSourceEntryExistingLabelNotes.from_dict(
            d.pop("existing_label_notes")
        )

        span_notes = []
        _span_notes = d.pop("span_notes")
        for span_notes_item_data in _span_notes:
            span_notes_item = QueueForSourceEntrySpanNotesItem.from_dict(
                span_notes_item_data
            )

            span_notes.append(span_notes_item)

        def _parse_span_notes_source_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        span_notes_source_id = _parse_span_notes_source_id(
            d.pop("span_notes_source_id", UNSET)
        )

        queue_for_source_entry = cls(
            queue=queue,
            item=item,
            labels=labels,
            existing_scores=existing_scores,
            existing_notes=existing_notes,
            existing_label_notes=existing_label_notes,
            span_notes=span_notes,
            span_notes_source_id=span_notes_source_id,
        )

        queue_for_source_entry.additional_properties = d
        return queue_for_source_entry

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
