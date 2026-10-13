from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DerivedVariableExtractRequest")


@_attrs_define
class DerivedVariableExtractRequest:
    """
    Attributes:
        version (str):
        column_name (str | Unset):  Default: 'output'.
        output_index (int | Unset):  Default: 0.
        response_format_type (str | Unset):
    """

    version: str
    column_name: str | Unset = "output"
    output_index: int | Unset = 0
    response_format_type: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        version = self.version

        column_name = self.column_name

        output_index = self.output_index

        response_format_type = self.response_format_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "version": version,
            }
        )
        if column_name is not UNSET:
            field_dict["column_name"] = column_name
        if output_index is not UNSET:
            field_dict["output_index"] = output_index
        if response_format_type is not UNSET:
            field_dict["response_format_type"] = response_format_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        version = d.pop("version")

        column_name = d.pop("column_name", UNSET)

        output_index = d.pop("output_index", UNSET)

        response_format_type = d.pop("response_format_type", UNSET)

        derived_variable_extract_request = cls(
            version=version,
            column_name=column_name,
            output_index=output_index,
            response_format_type=response_format_type,
        )

        derived_variable_extract_request.additional_properties = d
        return derived_variable_extract_request

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
