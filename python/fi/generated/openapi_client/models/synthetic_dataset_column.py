from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.synthetic_dataset_column_property import (
        SyntheticDatasetColumnProperty,
    )


T = TypeVar("T", bound="SyntheticDatasetColumn")


@_attrs_define
class SyntheticDatasetColumn:
    """
    Attributes:
        name (str):
        data_type (str):
        description (str):
        property_ (SyntheticDatasetColumnProperty):
        skip (bool | Unset):
        is_new (bool | Unset):
    """

    name: str
    data_type: str
    description: str
    property_: SyntheticDatasetColumnProperty
    skip: bool | Unset = UNSET
    is_new: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        data_type = self.data_type

        description = self.description

        property_ = self.property_.to_dict()

        skip = self.skip

        is_new = self.is_new

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "data_type": data_type,
                "description": description,
                "property": property_,
            }
        )
        if skip is not UNSET:
            field_dict["skip"] = skip
        if is_new is not UNSET:
            field_dict["is_new"] = is_new

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.synthetic_dataset_column_property import (
            SyntheticDatasetColumnProperty,
        )

        d = dict(src_dict)
        name = d.pop("name")

        data_type = d.pop("data_type")

        description = d.pop("description")

        property_ = SyntheticDatasetColumnProperty.from_dict(d.pop("property"))

        skip = d.pop("skip", UNSET)

        is_new = d.pop("is_new", UNSET)

        synthetic_dataset_column = cls(
            name=name,
            data_type=data_type,
            description=description,
            property_=property_,
            skip=skip,
            is_new=is_new,
        )

        synthetic_dataset_column.additional_properties = d
        return synthetic_dataset_column

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
