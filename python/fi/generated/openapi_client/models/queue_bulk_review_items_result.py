from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.queue_bulk_review_items_result_action import (
    QueueBulkReviewItemsResultAction,
)

if TYPE_CHECKING:
    from ..models.queue_bulk_review_items_error import QueueBulkReviewItemsError


T = TypeVar("T", bound="QueueBulkReviewItemsResult")


@_attrs_define
class QueueBulkReviewItemsResult:
    """
    Attributes:
        reviewed (int):
        reviewed_item_ids (list[UUID]):
        errors (list[QueueBulkReviewItemsError]):
        action (QueueBulkReviewItemsResultAction):
    """

    reviewed: int
    reviewed_item_ids: list[UUID]
    errors: list[QueueBulkReviewItemsError]
    action: QueueBulkReviewItemsResultAction
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        reviewed = self.reviewed

        reviewed_item_ids = []
        for reviewed_item_ids_item_data in self.reviewed_item_ids:
            reviewed_item_ids_item = str(reviewed_item_ids_item_data)
            reviewed_item_ids.append(reviewed_item_ids_item)

        errors = []
        for errors_item_data in self.errors:
            errors_item = errors_item_data.to_dict()
            errors.append(errors_item)

        action = self.action.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "reviewed": reviewed,
                "reviewed_item_ids": reviewed_item_ids,
                "errors": errors,
                "action": action,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_bulk_review_items_error import QueueBulkReviewItemsError

        d = dict(src_dict)
        reviewed = d.pop("reviewed")

        reviewed_item_ids = []
        _reviewed_item_ids = d.pop("reviewed_item_ids")
        for reviewed_item_ids_item_data in _reviewed_item_ids:
            reviewed_item_ids_item = UUID(reviewed_item_ids_item_data)

            reviewed_item_ids.append(reviewed_item_ids_item)

        errors = []
        _errors = d.pop("errors")
        for errors_item_data in _errors:
            errors_item = QueueBulkReviewItemsError.from_dict(errors_item_data)

            errors.append(errors_item)

        action = QueueBulkReviewItemsResultAction(d.pop("action"))

        queue_bulk_review_items_result = cls(
            reviewed=reviewed,
            reviewed_item_ids=reviewed_item_ids,
            errors=errors,
            action=action,
        )

        queue_bulk_review_items_result.additional_properties = d
        return queue_bulk_review_items_result

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
