from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.eval_usage_feedback import EvalUsageFeedback


T = TypeVar("T", bound="EvalUsageFeedbackCell")


@_attrs_define
class EvalUsageFeedbackCell:
    """
    Attributes:
        cell_value (EvalUsageFeedback | Unset):
    """

    cell_value: EvalUsageFeedback | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cell_value: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cell_value, Unset):
            cell_value = self.cell_value.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cell_value is not UNSET:
            field_dict["cell_value"] = cell_value

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_usage_feedback import EvalUsageFeedback

        d = dict(src_dict)
        _cell_value = d.pop("cell_value", UNSET)
        cell_value: EvalUsageFeedback | Unset
        if isinstance(_cell_value, Unset):
            cell_value = UNSET
        else:
            cell_value = EvalUsageFeedback.from_dict(_cell_value)

        eval_usage_feedback_cell = cls(
            cell_value=cell_value,
        )

        eval_usage_feedback_cell.additional_properties = d
        return eval_usage_feedback_cell

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
