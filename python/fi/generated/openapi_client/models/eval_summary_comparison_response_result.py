from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.eval_template_summary import EvalTemplateSummary


T = TypeVar("T", bound="EvalSummaryComparisonResponseResult")


@_attrs_define
class EvalSummaryComparisonResponseResult:
    """ """

    additional_properties: dict[str, list[EvalTemplateSummary]] = _attrs_field(
        init=False, factory=dict
    )

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = []
            for additional_property_item_data in prop:
                additional_property_item = additional_property_item_data.to_dict()
                field_dict[prop_name].append(additional_property_item)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_template_summary import EvalTemplateSummary

        d = dict(src_dict)
        eval_summary_comparison_response_result = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():
            additional_property = []
            _additional_property = prop_dict
            for additional_property_item_data in _additional_property:
                additional_property_item = EvalTemplateSummary.from_dict(
                    additional_property_item_data
                )

                additional_property.append(additional_property_item)

            additional_properties[prop_name] = additional_property

        eval_summary_comparison_response_result.additional_properties = (
            additional_properties
        )
        return eval_summary_comparison_response_result

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> list[EvalTemplateSummary]:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: list[EvalTemplateSummary]) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
