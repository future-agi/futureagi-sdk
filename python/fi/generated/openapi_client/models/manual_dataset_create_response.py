from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.manual_dataset_create_result import ManualDatasetCreateResult


T = TypeVar("T", bound="ManualDatasetCreateResponse")


@_attrs_define
class ManualDatasetCreateResponse:
    """
    Attributes:
        status (bool):
        result (ManualDatasetCreateResult):
    """

    status: bool
    result: ManualDatasetCreateResult
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        result = self.result.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
                "result": result,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.manual_dataset_create_result import ManualDatasetCreateResult

        d = dict(src_dict)
        status = d.pop("status")

        result = ManualDatasetCreateResult.from_dict(d.pop("result"))

        manual_dataset_create_response = cls(
            status=status,
            result=result,
        )

        manual_dataset_create_response.additional_properties = d
        return manual_dataset_create_response

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
