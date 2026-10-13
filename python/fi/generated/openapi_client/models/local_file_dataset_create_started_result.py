from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="LocalFileDatasetCreateStartedResult")


@_attrs_define
class LocalFileDatasetCreateStartedResult:
    """
    Attributes:
        message (str):
        dataset_id (UUID):
        dataset_name (str):
        processing_status (str):
        estimated_rows (int):
        estimated_columns (int):
        dataset_model_type (None | str | Unset):
    """

    message: str
    dataset_id: UUID
    dataset_name: str
    processing_status: str
    estimated_rows: int
    estimated_columns: int
    dataset_model_type: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        dataset_id = str(self.dataset_id)

        dataset_name = self.dataset_name

        processing_status = self.processing_status

        estimated_rows = self.estimated_rows

        estimated_columns = self.estimated_columns

        dataset_model_type: None | str | Unset
        if isinstance(self.dataset_model_type, Unset):
            dataset_model_type = UNSET
        else:
            dataset_model_type = self.dataset_model_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "processing_status": processing_status,
                "estimated_rows": estimated_rows,
                "estimated_columns": estimated_columns,
            }
        )
        if dataset_model_type is not UNSET:
            field_dict["dataset_model_type"] = dataset_model_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message")

        dataset_id = UUID(d.pop("dataset_id"))

        dataset_name = d.pop("dataset_name")

        processing_status = d.pop("processing_status")

        estimated_rows = d.pop("estimated_rows")

        estimated_columns = d.pop("estimated_columns")

        def _parse_dataset_model_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        dataset_model_type = _parse_dataset_model_type(
            d.pop("dataset_model_type", UNSET)
        )

        local_file_dataset_create_started_result = cls(
            message=message,
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            processing_status=processing_status,
            estimated_rows=estimated_rows,
            estimated_columns=estimated_columns,
            dataset_model_type=dataset_model_type,
        )

        local_file_dataset_create_started_result.additional_properties = d
        return local_file_dataset_create_started_result

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
