from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.eval_rollup_scope import EvalRollupScope
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_rollup_eval import EvalRollupEval


T = TypeVar("T", bound="EvalRollup")


@_attrs_define
class EvalRollup:
    """
    Attributes:
        scope (EvalRollupScope):
        evals (list[EvalRollupEval]):
        error (bool | Unset):
    """

    scope: EvalRollupScope
    evals: list[EvalRollupEval]
    error: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        scope = self.scope.value

        evals = []
        for evals_item_data in self.evals:
            evals_item = evals_item_data.to_dict()
            evals.append(evals_item)

        error = self.error

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "scope": scope,
                "evals": evals,
            }
        )
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_rollup_eval import EvalRollupEval

        d = dict(src_dict)
        scope = EvalRollupScope(d.pop("scope"))

        evals = []
        _evals = d.pop("evals")
        for evals_item_data in _evals:
            evals_item = EvalRollupEval.from_dict(evals_item_data)

            evals.append(evals_item)

        error = d.pop("error", UNSET)

        eval_rollup = cls(
            scope=scope,
            evals=evals,
            error=error,
        )

        eval_rollup.additional_properties = d
        return eval_rollup

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
