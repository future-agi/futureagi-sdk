from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.compare_eval_list_result_evals_item import (
        CompareEvalListResultEvalsItem,
    )


T = TypeVar("T", bound="CompareEvalListResult")


@_attrs_define
class CompareEvalListResult:
    """
    Attributes:
        evals (list[CompareEvalListResultEvalsItem]):
    """

    evals: list[CompareEvalListResultEvalsItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        evals = []
        for evals_item_data in self.evals:
            evals_item = evals_item_data.to_dict()
            evals.append(evals_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "evals": evals,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.compare_eval_list_result_evals_item import (
            CompareEvalListResultEvalsItem,
        )

        d = dict(src_dict)
        evals = []
        _evals = d.pop("evals")
        for evals_item_data in _evals:
            evals_item = CompareEvalListResultEvalsItem.from_dict(evals_item_data)

            evals.append(evals_item)

        compare_eval_list_result = cls(
            evals=evals,
        )

        compare_eval_list_result.additional_properties = d
        return compare_eval_list_result

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
