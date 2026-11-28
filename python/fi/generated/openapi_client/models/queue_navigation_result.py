from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.queue_navigation_result_next_item import QueueNavigationResultNextItem


T = TypeVar("T", bound="QueueNavigationResult")


@_attrs_define
class QueueNavigationResult:
    """
    Attributes:
        next_item (QueueNavigationResultNextItem):
        completed_item_id (UUID | Unset):
        skipped_item_id (UUID | Unset):
    """

    next_item: QueueNavigationResultNextItem
    completed_item_id: UUID | Unset = UNSET
    skipped_item_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        next_item = self.next_item.to_dict()

        completed_item_id: str | Unset = UNSET
        if not isinstance(self.completed_item_id, Unset):
            completed_item_id = str(self.completed_item_id)

        skipped_item_id: str | Unset = UNSET
        if not isinstance(self.skipped_item_id, Unset):
            skipped_item_id = str(self.skipped_item_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "next_item": next_item,
            }
        )
        if completed_item_id is not UNSET:
            field_dict["completed_item_id"] = completed_item_id
        if skipped_item_id is not UNSET:
            field_dict["skipped_item_id"] = skipped_item_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_navigation_result_next_item import (
            QueueNavigationResultNextItem,
        )

        d = dict(src_dict)
        next_item = QueueNavigationResultNextItem.from_dict(d.pop("next_item"))

        _completed_item_id = d.pop("completed_item_id", UNSET)
        completed_item_id: UUID | Unset
        if isinstance(_completed_item_id, Unset):
            completed_item_id = UNSET
        else:
            completed_item_id = UUID(_completed_item_id)

        _skipped_item_id = d.pop("skipped_item_id", UNSET)
        skipped_item_id: UUID | Unset
        if isinstance(_skipped_item_id, Unset):
            skipped_item_id = UNSET
        else:
            skipped_item_id = UUID(_skipped_item_id)

        queue_navigation_result = cls(
            next_item=next_item,
            completed_item_id=completed_item_id,
            skipped_item_id=skipped_item_id,
        )

        queue_navigation_result.additional_properties = d
        return queue_navigation_result

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
