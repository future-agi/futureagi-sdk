from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="DatasetListItem")


@_attrs_define
class DatasetListItem:
    """
    Attributes:
        id (UUID):
        name (str):
        number_of_datapoints (int):
        number_of_experiments (int):
        number_of_optimisations (int):
        derived_datasets (int):
        created_at (str):
        dataset_type (str):
    """

    id: UUID
    name: str
    number_of_datapoints: int
    number_of_experiments: int
    number_of_optimisations: int
    derived_datasets: int
    created_at: str
    dataset_type: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        number_of_datapoints = self.number_of_datapoints

        number_of_experiments = self.number_of_experiments

        number_of_optimisations = self.number_of_optimisations

        derived_datasets = self.derived_datasets

        created_at = self.created_at

        dataset_type = self.dataset_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "number_of_datapoints": number_of_datapoints,
                "number_of_experiments": number_of_experiments,
                "number_of_optimisations": number_of_optimisations,
                "derived_datasets": derived_datasets,
                "created_at": created_at,
                "dataset_type": dataset_type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        number_of_datapoints = d.pop("number_of_datapoints")

        number_of_experiments = d.pop("number_of_experiments")

        number_of_optimisations = d.pop("number_of_optimisations")

        derived_datasets = d.pop("derived_datasets")

        created_at = d.pop("created_at")

        dataset_type = d.pop("dataset_type")

        dataset_list_item = cls(
            id=id,
            name=name,
            number_of_datapoints=number_of_datapoints,
            number_of_experiments=number_of_experiments,
            number_of_optimisations=number_of_optimisations,
            derived_datasets=derived_datasets,
            created_at=created_at,
            dataset_type=dataset_type,
        )

        dataset_list_item.additional_properties = d
        return dataset_list_item

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
