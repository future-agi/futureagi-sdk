from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="QueueItemNavigationRequest")


@_attrs_define
class QueueItemNavigationRequest:
    """
    Attributes:
        exclude (list[str] | Unset):
        exclude_review_status (str | Unset):
        include_completed (bool | Unset):  Default: False.
    """

    exclude: list[str] | Unset = UNSET
    exclude_review_status: str | Unset = UNSET
    include_completed: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        exclude: list[str] | Unset = UNSET
        if not isinstance(self.exclude, Unset):
            exclude = self.exclude

        exclude_review_status = self.exclude_review_status

        include_completed = self.include_completed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if exclude is not UNSET:
            field_dict["exclude"] = exclude
        if exclude_review_status is not UNSET:
            field_dict["exclude_review_status"] = exclude_review_status
        if include_completed is not UNSET:
            field_dict["include_completed"] = include_completed

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        exclude = cast(list[str], d.pop("exclude", UNSET))

        exclude_review_status = d.pop("exclude_review_status", UNSET)

        include_completed = d.pop("include_completed", UNSET)

        queue_item_navigation_request = cls(
            exclude=exclude,
            exclude_review_status=exclude_review_status,
            include_completed=include_completed,
        )

        queue_item_navigation_request.additional_properties = d
        return queue_item_navigation_request

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
