from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.comparison_selection_metadata_equals import (
        ComparisonSelectionMetadataEquals,
    )


T = TypeVar("T", bound="ComparisonSelection")


@_attrs_define
class ComparisonSelection:
    """
    Attributes:
        total_plan_count (int):
        selected_count (int):
        metadata_equals (ComparisonSelectionMetadataEquals):
        split_name (None | str):
    """

    total_plan_count: int
    selected_count: int
    metadata_equals: ComparisonSelectionMetadataEquals
    split_name: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_plan_count = self.total_plan_count

        selected_count = self.selected_count

        metadata_equals = self.metadata_equals.to_dict()

        split_name: None | str
        split_name = self.split_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total_plan_count": total_plan_count,
                "selected_count": selected_count,
                "metadata_equals": metadata_equals,
                "split_name": split_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.comparison_selection_metadata_equals import (
            ComparisonSelectionMetadataEquals,
        )

        d = dict(src_dict)
        total_plan_count = d.pop("total_plan_count")

        selected_count = d.pop("selected_count")

        metadata_equals = ComparisonSelectionMetadataEquals.from_dict(
            d.pop("metadata_equals")
        )

        def _parse_split_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        split_name = _parse_split_name(d.pop("split_name"))

        comparison_selection = cls(
            total_plan_count=total_plan_count,
            selected_count=selected_count,
            metadata_equals=metadata_equals,
            split_name=split_name,
        )

        comparison_selection.additional_properties = d
        return comparison_selection

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
