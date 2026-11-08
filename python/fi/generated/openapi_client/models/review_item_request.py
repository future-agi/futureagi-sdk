from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.review_item_request_action import ReviewItemRequestAction
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.review_label_comment_request import ReviewLabelCommentRequest


T = TypeVar("T", bound="ReviewItemRequest")


@_attrs_define
class ReviewItemRequest:
    """
    Attributes:
        action (ReviewItemRequestAction):
        notes (str | Unset):
        label_comments (list[ReviewLabelCommentRequest] | Unset):
    """

    action: ReviewItemRequestAction
    notes: str | Unset = UNSET
    label_comments: list[ReviewLabelCommentRequest] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        action = self.action.value

        notes = self.notes

        label_comments: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.label_comments, Unset):
            label_comments = []
            for label_comments_item_data in self.label_comments:
                label_comments_item = label_comments_item_data.to_dict()
                label_comments.append(label_comments_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "action": action,
            }
        )
        if notes is not UNSET:
            field_dict["notes"] = notes
        if label_comments is not UNSET:
            field_dict["label_comments"] = label_comments

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.review_label_comment_request import ReviewLabelCommentRequest

        d = dict(src_dict)
        action = ReviewItemRequestAction(d.pop("action"))

        notes = d.pop("notes", UNSET)

        _label_comments = d.pop("label_comments", UNSET)
        label_comments: list[ReviewLabelCommentRequest] | Unset = UNSET
        if _label_comments is not UNSET:
            label_comments = []
            for label_comments_item_data in _label_comments:
                label_comments_item = ReviewLabelCommentRequest.from_dict(
                    label_comments_item_data
                )

                label_comments.append(label_comments_item)

        review_item_request = cls(
            action=action,
            notes=notes,
            label_comments=label_comments,
        )

        review_item_request.additional_properties = d
        return review_item_request

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
