from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.sdk_standalone_eval_result_item_evaluations_item import (
        SDKStandaloneEvalResultItemEvaluationsItem,
    )


T = TypeVar("T", bound="SDKStandaloneEvalResultItem")


@_attrs_define
class SDKStandaloneEvalResultItem:
    """
    Attributes:
        evaluations (list[SDKStandaloneEvalResultItemEvaluationsItem]):
    """

    evaluations: list[SDKStandaloneEvalResultItemEvaluationsItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        evaluations = []
        for evaluations_item_data in self.evaluations:
            evaluations_item = evaluations_item_data.to_dict()
            evaluations.append(evaluations_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "evaluations": evaluations,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sdk_standalone_eval_result_item_evaluations_item import (
            SDKStandaloneEvalResultItemEvaluationsItem,
        )

        d = dict(src_dict)
        evaluations = []
        _evaluations = d.pop("evaluations")
        for evaluations_item_data in _evaluations:
            evaluations_item = SDKStandaloneEvalResultItemEvaluationsItem.from_dict(
                evaluations_item_data
            )

            evaluations.append(evaluations_item)

        sdk_standalone_eval_result_item = cls(
            evaluations=evaluations,
        )

        sdk_standalone_eval_result_item.additional_properties = d
        return sdk_standalone_eval_result_item

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
