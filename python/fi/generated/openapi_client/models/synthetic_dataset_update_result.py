from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.synthetic_dataset_update_data import SyntheticDatasetUpdateData


T = TypeVar("T", bound="SyntheticDatasetUpdateResult")


@_attrs_define
class SyntheticDatasetUpdateResult:
    """
    Attributes:
        message (str):
        data (SyntheticDatasetUpdateData):
    """

    message: str
    data: SyntheticDatasetUpdateData
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        data = self.data.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "data": data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.synthetic_dataset_update_data import SyntheticDatasetUpdateData

        d = dict(src_dict)
        message = d.pop("message")

        data = SyntheticDatasetUpdateData.from_dict(d.pop("data"))

        synthetic_dataset_update_result = cls(
            message=message,
            data=data,
        )

        synthetic_dataset_update_result.additional_properties = d
        return synthetic_dataset_update_result

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
