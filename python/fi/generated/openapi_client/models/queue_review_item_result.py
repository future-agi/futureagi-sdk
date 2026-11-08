from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.queue_review_item_result_next_item import (
        QueueReviewItemResultNextItem,
    )
    from ..models.queue_review_item_result_review_comments_item import (
        QueueReviewItemResultReviewCommentsItem,
    )
    from ..models.queue_review_item_result_review_threads_item import (
        QueueReviewItemResultReviewThreadsItem,
    )


T = TypeVar("T", bound="QueueReviewItemResult")


@_attrs_define
class QueueReviewItemResult:
    """
    Attributes:
        reviewed_item_id (UUID):
        action (str):
        next_item (QueueReviewItemResultNextItem):
        review_comments (list[QueueReviewItemResultReviewCommentsItem]):
        review_threads (list[QueueReviewItemResultReviewThreadsItem]):
    """

    reviewed_item_id: UUID
    action: str
    next_item: QueueReviewItemResultNextItem
    review_comments: list[QueueReviewItemResultReviewCommentsItem]
    review_threads: list[QueueReviewItemResultReviewThreadsItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        reviewed_item_id = str(self.reviewed_item_id)

        action = self.action

        next_item = self.next_item.to_dict()

        review_comments = []
        for review_comments_item_data in self.review_comments:
            review_comments_item = review_comments_item_data.to_dict()
            review_comments.append(review_comments_item)

        review_threads = []
        for review_threads_item_data in self.review_threads:
            review_threads_item = review_threads_item_data.to_dict()
            review_threads.append(review_threads_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "reviewed_item_id": reviewed_item_id,
                "action": action,
                "next_item": next_item,
                "review_comments": review_comments,
                "review_threads": review_threads,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_review_item_result_next_item import (
            QueueReviewItemResultNextItem,
        )
        from ..models.queue_review_item_result_review_comments_item import (
            QueueReviewItemResultReviewCommentsItem,
        )
        from ..models.queue_review_item_result_review_threads_item import (
            QueueReviewItemResultReviewThreadsItem,
        )

        d = dict(src_dict)
        reviewed_item_id = UUID(d.pop("reviewed_item_id"))

        action = d.pop("action")

        next_item = QueueReviewItemResultNextItem.from_dict(d.pop("next_item"))

        review_comments = []
        _review_comments = d.pop("review_comments")
        for review_comments_item_data in _review_comments:
            review_comments_item = QueueReviewItemResultReviewCommentsItem.from_dict(
                review_comments_item_data
            )

            review_comments.append(review_comments_item)

        review_threads = []
        _review_threads = d.pop("review_threads")
        for review_threads_item_data in _review_threads:
            review_threads_item = QueueReviewItemResultReviewThreadsItem.from_dict(
                review_threads_item_data
            )

            review_threads.append(review_threads_item)

        queue_review_item_result = cls(
            reviewed_item_id=reviewed_item_id,
            action=action,
            next_item=next_item,
            review_comments=review_comments,
            review_threads=review_threads,
        )

        queue_review_item_result.additional_properties = d
        return queue_review_item_result

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
