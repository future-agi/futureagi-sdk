from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DatasetRowDiffRequest")


@_attrs_define
class DatasetRowDiffRequest:
    """
    Attributes:
        experiment_id (UUID):
        column_ids (list[UUID]):
        row_ids (list[UUID]):
        compare_column_ids (list[UUID]):
    """

    experiment_id: UUID
    column_ids: list[UUID]
    row_ids: list[UUID]
    compare_column_ids: list[UUID]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        experiment_id = str(self.experiment_id)

        column_ids = []
        for column_ids_item_data in self.column_ids:
            column_ids_item = str(column_ids_item_data)
            column_ids.append(column_ids_item)

        row_ids = []
        for row_ids_item_data in self.row_ids:
            row_ids_item = str(row_ids_item_data)
            row_ids.append(row_ids_item)

        compare_column_ids = []
        for compare_column_ids_item_data in self.compare_column_ids:
            compare_column_ids_item = str(compare_column_ids_item_data)
            compare_column_ids.append(compare_column_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "experiment_id": experiment_id,
                "column_ids": column_ids,
                "row_ids": row_ids,
                "compare_column_ids": compare_column_ids,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        experiment_id = UUID(d.pop("experiment_id"))

        column_ids = []
        _column_ids = d.pop("column_ids")
        for column_ids_item_data in _column_ids:
            column_ids_item = UUID(column_ids_item_data)

            column_ids.append(column_ids_item)

        row_ids = []
        _row_ids = d.pop("row_ids")
        for row_ids_item_data in _row_ids:
            row_ids_item = UUID(row_ids_item_data)

            row_ids.append(row_ids_item)

        compare_column_ids = []
        _compare_column_ids = d.pop("compare_column_ids")
        for compare_column_ids_item_data in _compare_column_ids:
            compare_column_ids_item = UUID(compare_column_ids_item_data)

            compare_column_ids.append(compare_column_ids_item)

        dataset_row_diff_request = cls(
            experiment_id=experiment_id,
            column_ids=column_ids,
            row_ids=row_ids,
            compare_column_ids=compare_column_ids,
        )

        dataset_row_diff_request.additional_properties = d
        return dataset_row_diff_request

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
