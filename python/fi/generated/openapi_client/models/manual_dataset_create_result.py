from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ManualDatasetCreateResult")


@_attrs_define
class ManualDatasetCreateResult:
    """
    Attributes:
        message (str):
        dataset_id (UUID):
        rows_created (int):
        columns_created (int):
    """

    message: str
    dataset_id: UUID
    rows_created: int
    columns_created: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        dataset_id = str(self.dataset_id)

        rows_created = self.rows_created

        columns_created = self.columns_created

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "dataset_id": dataset_id,
                "rows_created": rows_created,
                "columns_created": columns_created,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message")

        dataset_id = UUID(d.pop("dataset_id"))

        rows_created = d.pop("rows_created")

        columns_created = d.pop("columns_created")

        manual_dataset_create_result = cls(
            message=message,
            dataset_id=dataset_id,
            rows_created=rows_created,
            columns_created=columns_created,
        )

        manual_dataset_create_result.additional_properties = d
        return manual_dataset_create_result

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
