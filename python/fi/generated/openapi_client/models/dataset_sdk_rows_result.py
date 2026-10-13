from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.dataset import Dataset
    from ..models.dataset_sdk_rows_code import DatasetSdkRowsCode
    from ..models.dataset_sdk_rows_result_api_keys import DatasetSdkRowsResultApiKeys


T = TypeVar("T", bound="DatasetSdkRowsResult")


@_attrs_define
class DatasetSdkRowsResult:
    """
    Attributes:
        api_keys (DatasetSdkRowsResultApiKeys):
        dataset (Dataset):
        code (DatasetSdkRowsCode):
    """

    api_keys: DatasetSdkRowsResultApiKeys
    dataset: Dataset
    code: DatasetSdkRowsCode
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        api_keys = self.api_keys.to_dict()

        dataset = self.dataset.to_dict()

        code = self.code.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "api_keys": api_keys,
                "dataset": dataset,
                "code": code,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.dataset import Dataset
        from ..models.dataset_sdk_rows_code import DatasetSdkRowsCode
        from ..models.dataset_sdk_rows_result_api_keys import (
            DatasetSdkRowsResultApiKeys,
        )

        d = dict(src_dict)
        api_keys = DatasetSdkRowsResultApiKeys.from_dict(d.pop("api_keys"))

        dataset = Dataset.from_dict(d.pop("dataset"))

        code = DatasetSdkRowsCode.from_dict(d.pop("code"))

        dataset_sdk_rows_result = cls(
            api_keys=api_keys,
            dataset=dataset,
            code=code,
        )

        dataset_sdk_rows_result.additional_properties = d
        return dataset_sdk_rows_result

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
