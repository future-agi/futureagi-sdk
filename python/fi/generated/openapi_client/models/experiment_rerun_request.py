from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ExperimentRerunRequest")


@_attrs_define
class ExperimentRerunRequest:
    """
    Attributes:
        experiment_ids (list[UUID]):
        use_temporal (bool | Unset):  Default: True.
        max_concurrent_rows (int | Unset):
    """

    experiment_ids: list[UUID]
    use_temporal: bool | Unset = True
    max_concurrent_rows: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        experiment_ids = []
        for experiment_ids_item_data in self.experiment_ids:
            experiment_ids_item = str(experiment_ids_item_data)
            experiment_ids.append(experiment_ids_item)

        use_temporal = self.use_temporal

        max_concurrent_rows = self.max_concurrent_rows

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "experiment_ids": experiment_ids,
            }
        )
        if use_temporal is not UNSET:
            field_dict["use_temporal"] = use_temporal
        if max_concurrent_rows is not UNSET:
            field_dict["max_concurrent_rows"] = max_concurrent_rows

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        experiment_ids = []
        _experiment_ids = d.pop("experiment_ids")
        for experiment_ids_item_data in _experiment_ids:
            experiment_ids_item = UUID(experiment_ids_item_data)

            experiment_ids.append(experiment_ids_item)

        use_temporal = d.pop("use_temporal", UNSET)

        max_concurrent_rows = d.pop("max_concurrent_rows", UNSET)

        experiment_rerun_request = cls(
            experiment_ids=experiment_ids,
            use_temporal=use_temporal,
            max_concurrent_rows=max_concurrent_rows,
        )

        experiment_rerun_request.additional_properties = d
        return experiment_rerun_request

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
