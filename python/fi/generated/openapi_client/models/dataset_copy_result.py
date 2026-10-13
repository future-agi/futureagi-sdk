from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DatasetCopyResult")


@_attrs_define
class DatasetCopyResult:
    """
    Attributes:
        message (str):
        dataset_id (UUID):
        dataset_name (str):
    """

    message: str
    dataset_id: UUID
    dataset_name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        dataset_id = str(self.dataset_id)

        dataset_name = self.dataset_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message")

        dataset_id = UUID(d.pop("dataset_id"))

        dataset_name = d.pop("dataset_name")

        dataset_copy_result = cls(
            message=message,
            dataset_id=dataset_id,
            dataset_name=dataset_name,
        )

        dataset_copy_result.additional_properties = d
        return dataset_copy_result

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
