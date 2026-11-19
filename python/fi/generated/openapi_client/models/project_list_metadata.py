from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ProjectListMetadata")


@_attrs_define
class ProjectListMetadata:
    """
    Attributes:
        total_rows (int):
        page_number (int):
        page_size (int):
        total_pages (int):
    """

    total_rows: int
    page_number: int
    page_size: int
    total_pages: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_rows = self.total_rows

        page_number = self.page_number

        page_size = self.page_size

        total_pages = self.total_pages

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total_rows": total_rows,
                "page_number": page_number,
                "page_size": page_size,
                "total_pages": total_pages,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        total_rows = d.pop("total_rows")

        page_number = d.pop("page_number")

        page_size = d.pop("page_size")

        total_pages = d.pop("total_pages")

        project_list_metadata = cls(
            total_rows=total_rows,
            page_number=page_number,
            page_size=page_size,
            total_pages=total_pages,
        )

        project_list_metadata.additional_properties = d
        return project_list_metadata

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
