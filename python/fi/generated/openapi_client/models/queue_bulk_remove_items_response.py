from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.queue_bulk_remove_items_result import QueueBulkRemoveItemsResult


T = TypeVar("T", bound="QueueBulkRemoveItemsResponse")


@_attrs_define
class QueueBulkRemoveItemsResponse:
    """
    Attributes:
        result (QueueBulkRemoveItemsResult):
        status (bool | Unset):  Default: True.
    """

    result: QueueBulkRemoveItemsResult
    status: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = self.result.to_dict()

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "result": result,
            }
        )
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_bulk_remove_items_result import QueueBulkRemoveItemsResult

        d = dict(src_dict)
        result = QueueBulkRemoveItemsResult.from_dict(d.pop("result"))

        status = d.pop("status", UNSET)

        queue_bulk_remove_items_response = cls(
            result=result,
            status=status,
        )

        queue_bulk_remove_items_response.additional_properties = d
        return queue_bulk_remove_items_response

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
