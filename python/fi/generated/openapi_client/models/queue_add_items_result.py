from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="QueueAddItemsResult")


@_attrs_define
class QueueAddItemsResult:
    """
    Attributes:
        added (int):
        duplicates (int):
        errors (list[str]):
        queue_status (str):
        total_matching (int | Unset):
    """

    added: int
    duplicates: int
    errors: list[str]
    queue_status: str
    total_matching: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        added = self.added

        duplicates = self.duplicates

        errors = self.errors

        queue_status = self.queue_status

        total_matching = self.total_matching

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "added": added,
                "duplicates": duplicates,
                "errors": errors,
                "queue_status": queue_status,
            }
        )
        if total_matching is not UNSET:
            field_dict["total_matching"] = total_matching

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        added = d.pop("added")

        duplicates = d.pop("duplicates")

        errors = cast(list[str], d.pop("errors"))

        queue_status = d.pop("queue_status")

        total_matching = d.pop("total_matching", UNSET)

        queue_add_items_result = cls(
            added=added,
            duplicates=duplicates,
            errors=errors,
            queue_status=queue_status,
            total_matching=total_matching,
        )

        queue_add_items_result.additional_properties = d
        return queue_add_items_result

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
