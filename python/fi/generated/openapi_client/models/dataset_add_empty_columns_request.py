from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DatasetAddEmptyColumnsRequest")


@_attrs_define
class DatasetAddEmptyColumnsRequest:
    """
    Attributes:
        num_cols (int | Unset):  Default: 0.
    """

    num_cols: int | Unset = 0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        num_cols = self.num_cols

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if num_cols is not UNSET:
            field_dict["num_cols"] = num_cols

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        num_cols = d.pop("num_cols", UNSET)

        dataset_add_empty_columns_request = cls(
            num_cols=num_cols,
        )

        dataset_add_empty_columns_request.additional_properties = d
        return dataset_add_empty_columns_request

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
