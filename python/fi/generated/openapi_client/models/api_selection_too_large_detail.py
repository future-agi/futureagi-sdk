from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.api_selection_too_large_detail_type import ApiSelectionTooLargeDetailType

T = TypeVar("T", bound="ApiSelectionTooLargeDetail")


@_attrs_define
class ApiSelectionTooLargeDetail:
    """
    Attributes:
        type_ (ApiSelectionTooLargeDetailType):
        message (str):
        total_matching (int):
        cap (int):
    """

    type_: ApiSelectionTooLargeDetailType
    message: str
    total_matching: int
    cap: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        message = self.message

        total_matching = self.total_matching

        cap = self.cap

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "message": message,
                "total_matching": total_matching,
                "cap": cap,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = ApiSelectionTooLargeDetailType(d.pop("type"))

        message = d.pop("message")

        total_matching = d.pop("total_matching")

        cap = d.pop("cap")

        api_selection_too_large_detail = cls(
            type_=type_,
            message=message,
            total_matching=total_matching,
            cap=cap,
        )

        api_selection_too_large_detail.additional_properties = d
        return api_selection_too_large_detail

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
