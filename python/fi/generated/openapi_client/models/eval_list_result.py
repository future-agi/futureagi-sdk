from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_list_result_evals_item import EvalListResultEvalsItem


T = TypeVar("T", bound="EvalListResult")


@_attrs_define
class EvalListResult:
    """
    Attributes:
        evals (list[EvalListResultEvalsItem]):
        eval_recommendations (list[str] | Unset):
    """

    evals: list[EvalListResultEvalsItem]
    eval_recommendations: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        evals = []
        for evals_item_data in self.evals:
            evals_item = evals_item_data.to_dict()
            evals.append(evals_item)

        eval_recommendations: list[str] | Unset = UNSET
        if not isinstance(self.eval_recommendations, Unset):
            eval_recommendations = self.eval_recommendations

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "evals": evals,
            }
        )
        if eval_recommendations is not UNSET:
            field_dict["eval_recommendations"] = eval_recommendations

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_list_result_evals_item import EvalListResultEvalsItem

        d = dict(src_dict)
        evals = []
        _evals = d.pop("evals")
        for evals_item_data in _evals:
            evals_item = EvalListResultEvalsItem.from_dict(evals_item_data)

            evals.append(evals_item)

        eval_recommendations = cast(list[str], d.pop("eval_recommendations", UNSET))

        eval_list_result = cls(
            evals=evals,
            eval_recommendations=eval_recommendations,
        )

        eval_list_result.additional_properties = d
        return eval_list_result

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
