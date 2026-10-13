from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.queue_discussion_result_comment import QueueDiscussionResultComment
    from ..models.queue_discussion_result_review_comments_item import (
        QueueDiscussionResultReviewCommentsItem,
    )
    from ..models.queue_discussion_result_review_threads_item import (
        QueueDiscussionResultReviewThreadsItem,
    )
    from ..models.queue_discussion_result_thread import QueueDiscussionResultThread


T = TypeVar("T", bound="QueueDiscussionResult")


@_attrs_define
class QueueDiscussionResult:
    """
    Attributes:
        review_comments (list[QueueDiscussionResultReviewCommentsItem]):
        review_threads (list[QueueDiscussionResultReviewThreadsItem]):
        comment (QueueDiscussionResultComment | Unset):
        thread (QueueDiscussionResultThread | Unset):
    """

    review_comments: list[QueueDiscussionResultReviewCommentsItem]
    review_threads: list[QueueDiscussionResultReviewThreadsItem]
    comment: QueueDiscussionResultComment | Unset = UNSET
    thread: QueueDiscussionResultThread | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        review_comments = []
        for review_comments_item_data in self.review_comments:
            review_comments_item = review_comments_item_data.to_dict()
            review_comments.append(review_comments_item)

        review_threads = []
        for review_threads_item_data in self.review_threads:
            review_threads_item = review_threads_item_data.to_dict()
            review_threads.append(review_threads_item)

        comment: dict[str, Any] | Unset = UNSET
        if not isinstance(self.comment, Unset):
            comment = self.comment.to_dict()

        thread: dict[str, Any] | Unset = UNSET
        if not isinstance(self.thread, Unset):
            thread = self.thread.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "review_comments": review_comments,
                "review_threads": review_threads,
            }
        )
        if comment is not UNSET:
            field_dict["comment"] = comment
        if thread is not UNSET:
            field_dict["thread"] = thread

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_discussion_result_comment import (
            QueueDiscussionResultComment,
        )
        from ..models.queue_discussion_result_review_comments_item import (
            QueueDiscussionResultReviewCommentsItem,
        )
        from ..models.queue_discussion_result_review_threads_item import (
            QueueDiscussionResultReviewThreadsItem,
        )
        from ..models.queue_discussion_result_thread import QueueDiscussionResultThread

        d = dict(src_dict)
        review_comments = []
        _review_comments = d.pop("review_comments")
        for review_comments_item_data in _review_comments:
            review_comments_item = QueueDiscussionResultReviewCommentsItem.from_dict(
                review_comments_item_data
            )

            review_comments.append(review_comments_item)

        review_threads = []
        _review_threads = d.pop("review_threads")
        for review_threads_item_data in _review_threads:
            review_threads_item = QueueDiscussionResultReviewThreadsItem.from_dict(
                review_threads_item_data
            )

            review_threads.append(review_threads_item)

        _comment = d.pop("comment", UNSET)
        comment: QueueDiscussionResultComment | Unset
        if isinstance(_comment, Unset):
            comment = UNSET
        else:
            comment = QueueDiscussionResultComment.from_dict(_comment)

        _thread = d.pop("thread", UNSET)
        thread: QueueDiscussionResultThread | Unset
        if isinstance(_thread, Unset):
            thread = UNSET
        else:
            thread = QueueDiscussionResultThread.from_dict(_thread)

        queue_discussion_result = cls(
            review_comments=review_comments,
            review_threads=review_threads,
            comment=comment,
            thread=thread,
        )

        queue_discussion_result.additional_properties = d
        return queue_discussion_result

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
