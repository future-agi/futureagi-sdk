from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.json_column_schema_entry_sample import JsonColumnSchemaEntrySample


T = TypeVar("T", bound="JsonColumnSchemaEntry")


@_attrs_define
class JsonColumnSchemaEntry:
    """
    Attributes:
        name (str):
        keys (list[str] | Unset):
        sample (JsonColumnSchemaEntrySample | Unset):
        max_array_count (int | Unset):
        max_images_count (int | Unset):
    """

    name: str
    keys: list[str] | Unset = UNSET
    sample: JsonColumnSchemaEntrySample | Unset = UNSET
    max_array_count: int | Unset = UNSET
    max_images_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        keys: list[str] | Unset = UNSET
        if not isinstance(self.keys, Unset):
            keys = self.keys

        sample: dict[str, Any] | Unset = UNSET
        if not isinstance(self.sample, Unset):
            sample = self.sample.to_dict()

        max_array_count = self.max_array_count

        max_images_count = self.max_images_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if keys is not UNSET:
            field_dict["keys"] = keys
        if sample is not UNSET:
            field_dict["sample"] = sample
        if max_array_count is not UNSET:
            field_dict["max_array_count"] = max_array_count
        if max_images_count is not UNSET:
            field_dict["max_images_count"] = max_images_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.json_column_schema_entry_sample import JsonColumnSchemaEntrySample

        d = dict(src_dict)
        name = d.pop("name")

        keys = cast(list[str], d.pop("keys", UNSET))

        _sample = d.pop("sample", UNSET)
        sample: JsonColumnSchemaEntrySample | Unset
        if isinstance(_sample, Unset):
            sample = UNSET
        else:
            sample = JsonColumnSchemaEntrySample.from_dict(_sample)

        max_array_count = d.pop("max_array_count", UNSET)

        max_images_count = d.pop("max_images_count", UNSET)

        json_column_schema_entry = cls(
            name=name,
            keys=keys,
            sample=sample,
            max_array_count=max_array_count,
            max_images_count=max_images_count,
        )

        json_column_schema_entry.additional_properties = d
        return json_column_schema_entry

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
