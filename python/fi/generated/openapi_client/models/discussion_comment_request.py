from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DiscussionCommentRequest")


@_attrs_define
class DiscussionCommentRequest:
    """
    Attributes:
        comment (str | Unset):
        label_id (UUID | Unset):
        target_annotator_id (UUID | Unset):
        thread_id (UUID | Unset):
        mentioned_user_ids (list[str] | Unset):
    """

    comment: str | Unset = UNSET
    label_id: UUID | Unset = UNSET
    target_annotator_id: UUID | Unset = UNSET
    thread_id: UUID | Unset = UNSET
    mentioned_user_ids: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        comment = self.comment

        label_id: str | Unset = UNSET
        if not isinstance(self.label_id, Unset):
            label_id = str(self.label_id)

        target_annotator_id: str | Unset = UNSET
        if not isinstance(self.target_annotator_id, Unset):
            target_annotator_id = str(self.target_annotator_id)

        thread_id: str | Unset = UNSET
        if not isinstance(self.thread_id, Unset):
            thread_id = str(self.thread_id)

        mentioned_user_ids: list[str] | Unset = UNSET
        if not isinstance(self.mentioned_user_ids, Unset):
            mentioned_user_ids = self.mentioned_user_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if comment is not UNSET:
            field_dict["comment"] = comment
        if label_id is not UNSET:
            field_dict["label_id"] = label_id
        if target_annotator_id is not UNSET:
            field_dict["target_annotator_id"] = target_annotator_id
        if thread_id is not UNSET:
            field_dict["thread_id"] = thread_id
        if mentioned_user_ids is not UNSET:
            field_dict["mentioned_user_ids"] = mentioned_user_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        comment = d.pop("comment", UNSET)

        _label_id = d.pop("label_id", UNSET)
        label_id: UUID | Unset
        if isinstance(_label_id, Unset):
            label_id = UNSET
        else:
            label_id = UUID(_label_id)

        _target_annotator_id = d.pop("target_annotator_id", UNSET)
        target_annotator_id: UUID | Unset
        if isinstance(_target_annotator_id, Unset):
            target_annotator_id = UNSET
        else:
            target_annotator_id = UUID(_target_annotator_id)

        _thread_id = d.pop("thread_id", UNSET)
        thread_id: UUID | Unset
        if isinstance(_thread_id, Unset):
            thread_id = UNSET
        else:
            thread_id = UUID(_thread_id)

        mentioned_user_ids = cast(list[str], d.pop("mentioned_user_ids", UNSET))

        discussion_comment_request = cls(
            comment=comment,
            label_id=label_id,
            target_annotator_id=target_annotator_id,
            thread_id=thread_id,
            mentioned_user_ids=mentioned_user_ids,
        )

        discussion_comment_request.additional_properties = d
        return discussion_comment_request

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
