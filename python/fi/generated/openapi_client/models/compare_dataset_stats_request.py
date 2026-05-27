from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.compare_dataset_stats_request_stat_type import (
    CompareDatasetStatsRequestStatType,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="CompareDatasetStatsRequest")


@_attrs_define
class CompareDatasetStatsRequest:
    """
    Attributes:
        base_column_name (str):
        dataset_ids (list[UUID]):
        stat_type (CompareDatasetStatsRequestStatType | Unset):  Default: CompareDatasetStatsRequestStatType.EVALUATION.
    """

    base_column_name: str
    dataset_ids: list[UUID]
    stat_type: CompareDatasetStatsRequestStatType | Unset = (
        CompareDatasetStatsRequestStatType.EVALUATION
    )
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        base_column_name = self.base_column_name

        dataset_ids = []
        for dataset_ids_item_data in self.dataset_ids:
            dataset_ids_item = str(dataset_ids_item_data)
            dataset_ids.append(dataset_ids_item)

        stat_type: str | Unset = UNSET
        if not isinstance(self.stat_type, Unset):
            stat_type = self.stat_type.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "base_column_name": base_column_name,
                "dataset_ids": dataset_ids,
            }
        )
        if stat_type is not UNSET:
            field_dict["stat_type"] = stat_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        base_column_name = d.pop("base_column_name")

        dataset_ids = []
        _dataset_ids = d.pop("dataset_ids")
        for dataset_ids_item_data in _dataset_ids:
            dataset_ids_item = UUID(dataset_ids_item_data)

            dataset_ids.append(dataset_ids_item)

        _stat_type = d.pop("stat_type", UNSET)
        stat_type: CompareDatasetStatsRequestStatType | Unset
        if isinstance(_stat_type, Unset):
            stat_type = UNSET
        else:
            stat_type = CompareDatasetStatsRequestStatType(_stat_type)

        compare_dataset_stats_request = cls(
            base_column_name=base_column_name,
            dataset_ids=dataset_ids,
            stat_type=stat_type,
        )

        compare_dataset_stats_request.additional_properties = d
        return compare_dataset_stats_request

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
