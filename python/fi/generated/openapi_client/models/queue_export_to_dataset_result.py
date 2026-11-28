from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="QueueExportToDatasetResult")


@_attrs_define
class QueueExportToDatasetResult:
    """
    Attributes:
        dataset_id (UUID):
        dataset_name (str):
        rows_created (int):
        columns (list[str]):
    """

    dataset_id: UUID
    dataset_name: str
    rows_created: int
    columns: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dataset_id = str(self.dataset_id)

        dataset_name = self.dataset_name

        rows_created = self.rows_created

        columns = self.columns

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "rows_created": rows_created,
                "columns": columns,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        dataset_id = UUID(d.pop("dataset_id"))

        dataset_name = d.pop("dataset_name")

        rows_created = d.pop("rows_created")

        columns = cast(list[str], d.pop("columns"))

        queue_export_to_dataset_result = cls(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            rows_created=rows_created,
            columns=columns,
        )

        queue_export_to_dataset_result.additional_properties = d
        return queue_export_to_dataset_result

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
