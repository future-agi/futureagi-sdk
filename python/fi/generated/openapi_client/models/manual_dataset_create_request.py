from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ManualDatasetCreateRequest")


@_attrs_define
class ManualDatasetCreateRequest:
    """
    Attributes:
        dataset_name (str):
        number_of_rows (int | Unset):  Default: 1.
        number_of_columns (int | Unset):  Default: 1.
    """

    dataset_name: str
    number_of_rows: int | Unset = 1
    number_of_columns: int | Unset = 1
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_name = self.dataset_name

        number_of_rows = self.number_of_rows

        number_of_columns = self.number_of_columns

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataset_name": dataset_name,
            }
        )
        if number_of_rows is not UNSET:
            field_dict["number_of_rows"] = number_of_rows
        if number_of_columns is not UNSET:
            field_dict["number_of_columns"] = number_of_columns

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        dataset_name = d.pop("dataset_name")

        number_of_rows = d.pop("number_of_rows", UNSET)

        number_of_columns = d.pop("number_of_columns", UNSET)

        manual_dataset_create_request = cls(
            dataset_name=dataset_name,
            number_of_rows=number_of_rows,
            number_of_columns=number_of_columns,
        )

        manual_dataset_create_request.additional_properties = d
        return manual_dataset_create_request

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
