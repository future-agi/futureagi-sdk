from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SyntheticDatasetPayload")


@_attrs_define
class SyntheticDatasetPayload:
    """
    Attributes:
        description (str):
        objective (str):
        patterns (str):
        name (str | Unset):
    """

    description: str
    objective: str
    patterns: str
    name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        description = self.description

        objective = self.objective

        patterns = self.patterns

        name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "description": description,
                "objective": objective,
                "patterns": patterns,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        description = d.pop("description")

        objective = d.pop("objective")

        patterns = d.pop("patterns")

        name = d.pop("name", UNSET)

        synthetic_dataset_payload = cls(
            description=description,
            objective=objective,
            patterns=patterns,
            name=name,
        )

        synthetic_dataset_payload.additional_properties = d
        return synthetic_dataset_payload

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
