from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ReviewLabelCommentRequest")


@_attrs_define
class ReviewLabelCommentRequest:
    """
    Attributes:
        label_id (UUID | Unset):
        target_annotator_id (UUID | Unset):
        comment (str | Unset):
    """

    label_id: UUID | Unset = UNSET
    target_annotator_id: UUID | Unset = UNSET
    comment: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        label_id: str | Unset = UNSET
        if not isinstance(self.label_id, Unset):
            label_id = str(self.label_id)

        target_annotator_id: str | Unset = UNSET
        if not isinstance(self.target_annotator_id, Unset):
            target_annotator_id = str(self.target_annotator_id)

        comment = self.comment

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if label_id is not UNSET:
            field_dict["label_id"] = label_id
        if target_annotator_id is not UNSET:
            field_dict["target_annotator_id"] = target_annotator_id
        if comment is not UNSET:
            field_dict["comment"] = comment

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
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

        comment = d.pop("comment", UNSET)

        review_label_comment_request = cls(
            label_id=label_id,
            target_annotator_id=target_annotator_id,
            comment=comment,
        )

        review_label_comment_request.additional_properties = d
        return review_label_comment_request

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
