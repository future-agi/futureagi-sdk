from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.eval_config_structure import EvalConfigStructure


T = TypeVar("T", bound="EvalConfigStructureResult")


@_attrs_define
class EvalConfigStructureResult:
    """
    Attributes:
        eval_ (EvalConfigStructure):
    """

    eval_: EvalConfigStructure
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        eval_ = self.eval_.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "eval": eval_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_config_structure import EvalConfigStructure

        d = dict(src_dict)
        eval_ = EvalConfigStructure.from_dict(d.pop("eval"))

        eval_config_structure_result = cls(
            eval_=eval_,
        )

        eval_config_structure_result.additional_properties = d
        return eval_config_structure_result

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
