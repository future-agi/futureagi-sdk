from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.bulk_review_items_request_action import BulkReviewItemsRequestAction
from ..types import UNSET, Unset

T = TypeVar("T", bound="BulkReviewItemsRequest")


@_attrs_define
class BulkReviewItemsRequest:
    """
    Attributes:
        item_ids (list[UUID]):
        action (BulkReviewItemsRequestAction):
        notes (str | Unset):
    """

    item_ids: list[UUID]
    action: BulkReviewItemsRequestAction
    notes: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        item_ids = []
        for item_ids_item_data in self.item_ids:
            item_ids_item = str(item_ids_item_data)
            item_ids.append(item_ids_item)

        action = self.action.value

        notes = self.notes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "item_ids": item_ids,
                "action": action,
            }
        )
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        item_ids = []
        _item_ids = d.pop("item_ids")
        for item_ids_item_data in _item_ids:
            item_ids_item = UUID(item_ids_item_data)

            item_ids.append(item_ids_item)

        action = BulkReviewItemsRequestAction(d.pop("action"))

        notes = d.pop("notes", UNSET)

        bulk_review_items_request = cls(
            item_ids=item_ids,
            action=action,
            notes=notes,
        )

        bulk_review_items_request.additional_properties = d
        return bulk_review_items_request

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
