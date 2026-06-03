from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.eval_template_summary_output import EvalTemplateSummaryOutput


T = TypeVar("T", bound="EvalTemplateSummary")


@_attrs_define
class EvalTemplateSummary:
    """
    Attributes:
        name (str):
        id (str):
        total_cells (int):
        output (EvalTemplateSummaryOutput):
    """

    name: str
    id: str
    total_cells: int
    output: EvalTemplateSummaryOutput
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        id = self.id

        total_cells = self.total_cells

        output = self.output.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "id": id,
                "total_cells": total_cells,
                "output": output,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.eval_template_summary_output import EvalTemplateSummaryOutput

        d = dict(src_dict)
        name = d.pop("name")

        id = d.pop("id")

        total_cells = d.pop("total_cells")

        output = EvalTemplateSummaryOutput.from_dict(d.pop("output"))

        eval_template_summary = cls(
            name=name,
            id=id,
            total_cells=total_cells,
            output=output,
        )

        eval_template_summary.additional_properties = d
        return eval_template_summary

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
