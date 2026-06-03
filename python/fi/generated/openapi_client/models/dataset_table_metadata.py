from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DatasetTableMetadata")


@_attrs_define
class DatasetTableMetadata:
    """
    Attributes:
        dataset_name (str):
        total_rows (int | Unset):
        total_pages (int | Unset):
        error_messages (list[str] | Unset):
        status (None | str | Unset):
    """

    dataset_name: str
    total_rows: int | Unset = UNSET
    total_pages: int | Unset = UNSET
    error_messages: list[str] | Unset = UNSET
    status: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_name = self.dataset_name

        total_rows = self.total_rows

        total_pages = self.total_pages

        error_messages: list[str] | Unset = UNSET
        if not isinstance(self.error_messages, Unset):
            error_messages = self.error_messages

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        else:
            status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataset_name": dataset_name,
            }
        )
        if total_rows is not UNSET:
            field_dict["total_rows"] = total_rows
        if total_pages is not UNSET:
            field_dict["total_pages"] = total_pages
        if error_messages is not UNSET:
            field_dict["error_messages"] = error_messages
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        dataset_name = d.pop("dataset_name")

        total_rows = d.pop("total_rows", UNSET)

        total_pages = d.pop("total_pages", UNSET)

        error_messages = cast(list[str], d.pop("error_messages", UNSET))

        def _parse_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        dataset_table_metadata = cls(
            dataset_name=dataset_name,
            total_rows=total_rows,
            total_pages=total_pages,
            error_messages=error_messages,
            status=status,
        )

        dataset_table_metadata.additional_properties = d
        return dataset_table_metadata

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
