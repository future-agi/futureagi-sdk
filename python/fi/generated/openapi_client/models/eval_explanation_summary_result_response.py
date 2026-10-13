from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.eval_explanation_cluster import EvalExplanationCluster


T = TypeVar("T", bound="EvalExplanationSummaryResultResponse")


@_attrs_define
class EvalExplanationSummaryResultResponse:
    """ """

    additional_properties: dict[str, list[EvalExplanationCluster]] = _attrs_field(
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
        from ..models.eval_explanation_cluster import EvalExplanationCluster

        d = dict(src_dict)
        eval_explanation_summary_result_response = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():
            additional_property = []
            _additional_property = prop_dict
            for additional_property_item_data in _additional_property:
                additional_property_item = EvalExplanationCluster.from_dict(
                    additional_property_item_data
                )

                additional_property.append(additional_property_item)

            additional_properties[prop_name] = additional_property

        eval_explanation_summary_result_response.additional_properties = (
            additional_properties
        )
        return eval_explanation_summary_result_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> list[EvalExplanationCluster]:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: list[EvalExplanationCluster]) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
