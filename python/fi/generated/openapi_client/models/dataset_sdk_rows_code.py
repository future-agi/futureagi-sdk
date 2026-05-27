from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DatasetSdkRowsCode")


@_attrs_define
class DatasetSdkRowsCode:
    """
    Attributes:
        python_add_row (str):
        python_add_col (str):
        typescript_add_col (str):
        typescript_add_row (str):
        curl_add_col (str):
        curl_add_row (str):
    """

    python_add_row: str
    python_add_col: str
    typescript_add_col: str
    typescript_add_row: str
    curl_add_col: str
    curl_add_row: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        python_add_row = self.python_add_row

        python_add_col = self.python_add_col

        typescript_add_col = self.typescript_add_col

        typescript_add_row = self.typescript_add_row

        curl_add_col = self.curl_add_col

        curl_add_row = self.curl_add_row

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "python_add_row": python_add_row,
                "python_add_col": python_add_col,
                "typescript_add_col": typescript_add_col,
                "typescript_add_row": typescript_add_row,
                "curl_add_col": curl_add_col,
                "curl_add_row": curl_add_row,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        python_add_row = d.pop("python_add_row")

        python_add_col = d.pop("python_add_col")

        typescript_add_col = d.pop("typescript_add_col")

        typescript_add_row = d.pop("typescript_add_row")

        curl_add_col = d.pop("curl_add_col")

        curl_add_row = d.pop("curl_add_row")

        dataset_sdk_rows_code = cls(
            python_add_row=python_add_row,
            python_add_col=python_add_col,
            typescript_add_col=typescript_add_col,
            typescript_add_row=typescript_add_row,
            curl_add_col=curl_add_col,
            curl_add_row=curl_add_row,
        )

        dataset_sdk_rows_code.additional_properties = d
        return dataset_sdk_rows_code

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
