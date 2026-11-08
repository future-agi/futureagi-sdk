from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.queue_annotate_detail_result_annotations_item import (
        QueueAnnotateDetailResultAnnotationsItem,
    )
    from ..models.queue_annotate_detail_result_item import QueueAnnotateDetailResultItem
    from ..models.queue_annotate_detail_result_labels_item import (
        QueueAnnotateDetailResultLabelsItem,
    )
    from ..models.queue_annotate_detail_result_progress import (
        QueueAnnotateDetailResultProgress,
    )
    from ..models.queue_annotate_detail_result_queue import (
        QueueAnnotateDetailResultQueue,
    )
    from ..models.queue_annotate_detail_result_review_comments_item import (
        QueueAnnotateDetailResultReviewCommentsItem,
    )
    from ..models.queue_annotate_detail_result_review_threads_item import (
        QueueAnnotateDetailResultReviewThreadsItem,
    )
    from ..models.queue_annotate_detail_result_span_notes_item import (
        QueueAnnotateDetailResultSpanNotesItem,
    )


T = TypeVar("T", bound="QueueAnnotateDetailResult")


@_attrs_define
class QueueAnnotateDetailResult:
    """
    Attributes:
        item (QueueAnnotateDetailResultItem):
        queue (QueueAnnotateDetailResultQueue):
        labels (list[QueueAnnotateDetailResultLabelsItem]):
        annotations (list[QueueAnnotateDetailResultAnnotationsItem]):
        review_comments (list[QueueAnnotateDetailResultReviewCommentsItem]):
        review_threads (list[QueueAnnotateDetailResultReviewThreadsItem]):
        existing_notes (str):
        span_notes (list[QueueAnnotateDetailResultSpanNotesItem]):
        progress (QueueAnnotateDetailResultProgress):
        span_notes_source_id (None | str | Unset):
        next_item_id (None | str | Unset):
        prev_item_id (None | str | Unset):
    """

    item: QueueAnnotateDetailResultItem
    queue: QueueAnnotateDetailResultQueue
    labels: list[QueueAnnotateDetailResultLabelsItem]
    annotations: list[QueueAnnotateDetailResultAnnotationsItem]
    review_comments: list[QueueAnnotateDetailResultReviewCommentsItem]
    review_threads: list[QueueAnnotateDetailResultReviewThreadsItem]
    existing_notes: str
    span_notes: list[QueueAnnotateDetailResultSpanNotesItem]
    progress: QueueAnnotateDetailResultProgress
    span_notes_source_id: None | str | Unset = UNSET
    next_item_id: None | str | Unset = UNSET
    prev_item_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        item = self.item.to_dict()

        queue = self.queue.to_dict()

        labels = []
        for labels_item_data in self.labels:
            labels_item = labels_item_data.to_dict()
            labels.append(labels_item)

        annotations = []
        for annotations_item_data in self.annotations:
            annotations_item = annotations_item_data.to_dict()
            annotations.append(annotations_item)

        review_comments = []
        for review_comments_item_data in self.review_comments:
            review_comments_item = review_comments_item_data.to_dict()
            review_comments.append(review_comments_item)

        review_threads = []
        for review_threads_item_data in self.review_threads:
            review_threads_item = review_threads_item_data.to_dict()
            review_threads.append(review_threads_item)

        existing_notes = self.existing_notes

        span_notes = []
        for span_notes_item_data in self.span_notes:
            span_notes_item = span_notes_item_data.to_dict()
            span_notes.append(span_notes_item)

        progress = self.progress.to_dict()

        span_notes_source_id: None | str | Unset
        if isinstance(self.span_notes_source_id, Unset):
            span_notes_source_id = UNSET
        else:
            span_notes_source_id = self.span_notes_source_id

        next_item_id: None | str | Unset
        if isinstance(self.next_item_id, Unset):
            next_item_id = UNSET
        else:
            next_item_id = self.next_item_id

        prev_item_id: None | str | Unset
        if isinstance(self.prev_item_id, Unset):
            prev_item_id = UNSET
        else:
            prev_item_id = self.prev_item_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "item": item,
                "queue": queue,
                "labels": labels,
                "annotations": annotations,
                "review_comments": review_comments,
                "review_threads": review_threads,
                "existing_notes": existing_notes,
                "span_notes": span_notes,
                "progress": progress,
            }
        )
        if span_notes_source_id is not UNSET:
            field_dict["span_notes_source_id"] = span_notes_source_id
        if next_item_id is not UNSET:
            field_dict["next_item_id"] = next_item_id
        if prev_item_id is not UNSET:
            field_dict["prev_item_id"] = prev_item_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_annotate_detail_result_annotations_item import (
            QueueAnnotateDetailResultAnnotationsItem,
        )
        from ..models.queue_annotate_detail_result_item import (
            QueueAnnotateDetailResultItem,
        )
        from ..models.queue_annotate_detail_result_labels_item import (
            QueueAnnotateDetailResultLabelsItem,
        )
        from ..models.queue_annotate_detail_result_progress import (
            QueueAnnotateDetailResultProgress,
        )
        from ..models.queue_annotate_detail_result_queue import (
            QueueAnnotateDetailResultQueue,
        )
        from ..models.queue_annotate_detail_result_review_comments_item import (
            QueueAnnotateDetailResultReviewCommentsItem,
        )
        from ..models.queue_annotate_detail_result_review_threads_item import (
            QueueAnnotateDetailResultReviewThreadsItem,
        )
        from ..models.queue_annotate_detail_result_span_notes_item import (
            QueueAnnotateDetailResultSpanNotesItem,
        )

        d = dict(src_dict)
        item = QueueAnnotateDetailResultItem.from_dict(d.pop("item"))

        queue = QueueAnnotateDetailResultQueue.from_dict(d.pop("queue"))

        labels = []
        _labels = d.pop("labels")
        for labels_item_data in _labels:
            labels_item = QueueAnnotateDetailResultLabelsItem.from_dict(
                labels_item_data
            )

            labels.append(labels_item)

        annotations = []
        _annotations = d.pop("annotations")
        for annotations_item_data in _annotations:
            annotations_item = QueueAnnotateDetailResultAnnotationsItem.from_dict(
                annotations_item_data
            )

            annotations.append(annotations_item)

        review_comments = []
        _review_comments = d.pop("review_comments")
        for review_comments_item_data in _review_comments:
            review_comments_item = (
                QueueAnnotateDetailResultReviewCommentsItem.from_dict(
                    review_comments_item_data
                )
            )

            review_comments.append(review_comments_item)

        review_threads = []
        _review_threads = d.pop("review_threads")
        for review_threads_item_data in _review_threads:
            review_threads_item = QueueAnnotateDetailResultReviewThreadsItem.from_dict(
                review_threads_item_data
            )

            review_threads.append(review_threads_item)

        existing_notes = d.pop("existing_notes")

        span_notes = []
        _span_notes = d.pop("span_notes")
        for span_notes_item_data in _span_notes:
            span_notes_item = QueueAnnotateDetailResultSpanNotesItem.from_dict(
                span_notes_item_data
            )

            span_notes.append(span_notes_item)

        progress = QueueAnnotateDetailResultProgress.from_dict(d.pop("progress"))

        def _parse_span_notes_source_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        span_notes_source_id = _parse_span_notes_source_id(
            d.pop("span_notes_source_id", UNSET)
        )

        def _parse_next_item_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        next_item_id = _parse_next_item_id(d.pop("next_item_id", UNSET))

        def _parse_prev_item_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        prev_item_id = _parse_prev_item_id(d.pop("prev_item_id", UNSET))

        queue_annotate_detail_result = cls(
            item=item,
            queue=queue,
            labels=labels,
            annotations=annotations,
            review_comments=review_comments,
            review_threads=review_threads,
            existing_notes=existing_notes,
            span_notes=span_notes,
            progress=progress,
            span_notes_source_id=span_notes_source_id,
            next_item_id=next_item_id,
            prev_item_id=prev_item_id,
        )

        queue_annotate_detail_result.additional_properties = d
        return queue_annotate_detail_result

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
