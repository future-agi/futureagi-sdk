from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateDatasetFromExperimentRequest")


@_attrs_define
class CreateDatasetFromExperimentRequest:
    """
    Attributes:
        name (str | Unset):
        model_type (str | Unset):
    """

    name: str | Unset = UNSET
    model_type: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        model_type = self.model_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if model_type is not UNSET:
            field_dict["model_type"] = model_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        model_type = d.pop("model_type", UNSET)

        create_dataset_from_experiment_request = cls(
            name=name,
            model_type=model_type,
        )

        create_dataset_from_experiment_request.additional_properties = d
        return create_dataset_from_experiment_request

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
