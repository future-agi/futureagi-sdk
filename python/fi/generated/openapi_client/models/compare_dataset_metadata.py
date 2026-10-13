from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="CompareDatasetMetadata")


@_attrs_define
class CompareDatasetMetadata:
    """
    Attributes:
        compare_id (UUID):
        total_rows (int):
        total_pages (int):
    """

    compare_id: UUID
    total_rows: int
    total_pages: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        compare_id = str(self.compare_id)

        total_rows = self.total_rows

        total_pages = self.total_pages

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "compare_id": compare_id,
                "total_rows": total_rows,
                "total_pages": total_pages,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        compare_id = UUID(d.pop("compare_id"))

        total_rows = d.pop("total_rows")

        total_pages = d.pop("total_pages")

        compare_dataset_metadata = cls(
            compare_id=compare_id,
            total_rows=total_rows,
            total_pages=total_pages,
        )

        compare_dataset_metadata.additional_properties = d
        return compare_dataset_metadata

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
