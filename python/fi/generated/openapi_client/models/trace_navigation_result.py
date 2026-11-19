from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="TraceNavigationResult")


@_attrs_define
class TraceNavigationResult:
    """
    Attributes:
        next_trace_id (None | str):
        previous_trace_id (None | str):
    """

    next_trace_id: None | str
    previous_trace_id: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        next_trace_id: None | str
        next_trace_id = self.next_trace_id

        previous_trace_id: None | str
        previous_trace_id = self.previous_trace_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "next_trace_id": next_trace_id,
                "previous_trace_id": previous_trace_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_next_trace_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        next_trace_id = _parse_next_trace_id(d.pop("next_trace_id"))

        def _parse_previous_trace_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        previous_trace_id = _parse_previous_trace_id(d.pop("previous_trace_id"))

        trace_navigation_result = cls(
            next_trace_id=next_trace_id,
            previous_trace_id=previous_trace_id,
        )

        trace_navigation_result.additional_properties = d
        return trace_navigation_result

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
