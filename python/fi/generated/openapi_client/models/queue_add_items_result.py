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
        total_matching_is_lower_bound (bool | Unset):
        has_more (bool | Unset):
        next_cursor (None | str | Unset):
        next_cursor_fingerprint (None | str | Unset):
    """

    added: int
    duplicates: int
    errors: list[str]
    queue_status: str
    total_matching: int | Unset = UNSET
    total_matching_is_lower_bound: bool | Unset = UNSET
    has_more: bool | Unset = UNSET
    next_cursor: None | str | Unset = UNSET
    next_cursor_fingerprint: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        added = self.added

        duplicates = self.duplicates

        errors = self.errors

        queue_status = self.queue_status

        total_matching = self.total_matching

        total_matching_is_lower_bound = self.total_matching_is_lower_bound

        has_more = self.has_more

        next_cursor: None | str | Unset
        if isinstance(self.next_cursor, Unset):
            next_cursor = UNSET
        else:
            next_cursor = self.next_cursor

        next_cursor_fingerprint: None | str | Unset
        if isinstance(self.next_cursor_fingerprint, Unset):
            next_cursor_fingerprint = UNSET
        else:
            next_cursor_fingerprint = self.next_cursor_fingerprint

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
        if total_matching_is_lower_bound is not UNSET:
            field_dict["total_matching_is_lower_bound"] = total_matching_is_lower_bound
        if has_more is not UNSET:
            field_dict["has_more"] = has_more
        if next_cursor is not UNSET:
            field_dict["next_cursor"] = next_cursor
        if next_cursor_fingerprint is not UNSET:
            field_dict["next_cursor_fingerprint"] = next_cursor_fingerprint

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        added = d.pop("added")

        duplicates = d.pop("duplicates")

        errors = cast(list[str], d.pop("errors"))

        queue_status = d.pop("queue_status")

        total_matching = d.pop("total_matching", UNSET)

        total_matching_is_lower_bound = d.pop("total_matching_is_lower_bound", UNSET)

        has_more = d.pop("has_more", UNSET)

        def _parse_next_cursor(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        next_cursor = _parse_next_cursor(d.pop("next_cursor", UNSET))

        def _parse_next_cursor_fingerprint(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        next_cursor_fingerprint = _parse_next_cursor_fingerprint(
            d.pop("next_cursor_fingerprint", UNSET)
        )

        queue_add_items_result = cls(
            added=added,
            duplicates=duplicates,
            errors=errors,
            queue_status=queue_status,
            total_matching=total_matching,
            total_matching_is_lower_bound=total_matching_is_lower_bound,
            has_more=has_more,
            next_cursor=next_cursor,
            next_cursor_fingerprint=next_cursor_fingerprint,
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
