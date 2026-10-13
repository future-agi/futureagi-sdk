from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.column_type_conversion_result_invalid_values_item import (
        ColumnTypeConversionResultInvalidValuesItem,
    )
    from ..models.column_type_conversion_result_valid_conversion_samples import (
        ColumnTypeConversionResultValidConversionSamples,
    )


T = TypeVar("T", bound="ColumnTypeConversionResult")


@_attrs_define
class ColumnTypeConversionResult:
    """
    Attributes:
        message (str | Unset):
        column_id (UUID | Unset):
        new_data_type (str | Unset):
        status (str | Unset):
        invalid_count (int | Unset):
        invalid_values (list[ColumnTypeConversionResultInvalidValuesItem] | Unset):
        valid_conversion_samples (ColumnTypeConversionResultValidConversionSamples | Unset):
    """

    message: str | Unset = UNSET
    column_id: UUID | Unset = UNSET
    new_data_type: str | Unset = UNSET
    status: str | Unset = UNSET
    invalid_count: int | Unset = UNSET
    invalid_values: list[ColumnTypeConversionResultInvalidValuesItem] | Unset = UNSET
    valid_conversion_samples: (
        ColumnTypeConversionResultValidConversionSamples | Unset
    ) = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        column_id: str | Unset = UNSET
        if not isinstance(self.column_id, Unset):
            column_id = str(self.column_id)

        new_data_type = self.new_data_type

        status = self.status

        invalid_count = self.invalid_count

        invalid_values: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.invalid_values, Unset):
            invalid_values = []
            for invalid_values_item_data in self.invalid_values:
                invalid_values_item = invalid_values_item_data.to_dict()
                invalid_values.append(invalid_values_item)

        valid_conversion_samples: dict[str, Any] | Unset = UNSET
        if not isinstance(self.valid_conversion_samples, Unset):
            valid_conversion_samples = self.valid_conversion_samples.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if message is not UNSET:
            field_dict["message"] = message
        if column_id is not UNSET:
            field_dict["column_id"] = column_id
        if new_data_type is not UNSET:
            field_dict["new_data_type"] = new_data_type
        if status is not UNSET:
            field_dict["status"] = status
        if invalid_count is not UNSET:
            field_dict["invalid_count"] = invalid_count
        if invalid_values is not UNSET:
            field_dict["invalid_values"] = invalid_values
        if valid_conversion_samples is not UNSET:
            field_dict["valid_conversion_samples"] = valid_conversion_samples

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.column_type_conversion_result_invalid_values_item import (
            ColumnTypeConversionResultInvalidValuesItem,
        )
        from ..models.column_type_conversion_result_valid_conversion_samples import (
            ColumnTypeConversionResultValidConversionSamples,
        )

        d = dict(src_dict)
        message = d.pop("message", UNSET)

        _column_id = d.pop("column_id", UNSET)
        column_id: UUID | Unset
        if isinstance(_column_id, Unset):
            column_id = UNSET
        else:
            column_id = UUID(_column_id)

        new_data_type = d.pop("new_data_type", UNSET)

        status = d.pop("status", UNSET)

        invalid_count = d.pop("invalid_count", UNSET)

        _invalid_values = d.pop("invalid_values", UNSET)
        invalid_values: list[ColumnTypeConversionResultInvalidValuesItem] | Unset = (
            UNSET
        )
        if _invalid_values is not UNSET:
            invalid_values = []
            for invalid_values_item_data in _invalid_values:
                invalid_values_item = (
                    ColumnTypeConversionResultInvalidValuesItem.from_dict(
                        invalid_values_item_data
                    )
                )

                invalid_values.append(invalid_values_item)

        _valid_conversion_samples = d.pop("valid_conversion_samples", UNSET)
        valid_conversion_samples: (
            ColumnTypeConversionResultValidConversionSamples | Unset
        )
        if isinstance(_valid_conversion_samples, Unset):
            valid_conversion_samples = UNSET
        else:
            valid_conversion_samples = (
                ColumnTypeConversionResultValidConversionSamples.from_dict(
                    _valid_conversion_samples
                )
            )

        column_type_conversion_result = cls(
            message=message,
            column_id=column_id,
            new_data_type=new_data_type,
            status=status,
            invalid_count=invalid_count,
            invalid_values=invalid_values,
            valid_conversion_samples=valid_conversion_samples,
        )

        column_type_conversion_result.additional_properties = d
        return column_type_conversion_result

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
