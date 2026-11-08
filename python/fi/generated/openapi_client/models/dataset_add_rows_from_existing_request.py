from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.dataset_add_rows_from_existing_request_column_mapping import (
        DatasetAddRowsFromExistingRequestColumnMapping,
    )


T = TypeVar("T", bound="DatasetAddRowsFromExistingRequest")


@_attrs_define
class DatasetAddRowsFromExistingRequest:
    """
    Attributes:
        source_dataset_id (UUID):
        column_mapping (DatasetAddRowsFromExistingRequestColumnMapping):
    """

    source_dataset_id: UUID
    column_mapping: DatasetAddRowsFromExistingRequestColumnMapping
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source_dataset_id = str(self.source_dataset_id)

        column_mapping = self.column_mapping.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "source_dataset_id": source_dataset_id,
                "column_mapping": column_mapping,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset_add_rows_from_existing_request_column_mapping import (
            DatasetAddRowsFromExistingRequestColumnMapping,
        )

        d = dict(src_dict)
        source_dataset_id = UUID(d.pop("source_dataset_id"))

        column_mapping = DatasetAddRowsFromExistingRequestColumnMapping.from_dict(
            d.pop("column_mapping")
        )

        dataset_add_rows_from_existing_request = cls(
            source_dataset_id=source_dataset_id,
            column_mapping=column_mapping,
        )

        dataset_add_rows_from_existing_request.additional_properties = d
        return dataset_add_rows_from_existing_request

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
