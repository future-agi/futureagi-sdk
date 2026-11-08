from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GroundTruthRoleMapping")


@_attrs_define
class GroundTruthRoleMapping:
    """
    Attributes:
        output (str | Unset):
        explanation (str | Unset):
        expected_output (str | Unset): Legacy alias for `output`.
        reasoning (str | Unset): Legacy alias for `explanation`.
        reason (str | Unset): Legacy alias for `explanation`.
    """

    output: str | Unset = UNSET
    explanation: str | Unset = UNSET
    expected_output: str | Unset = UNSET
    reasoning: str | Unset = UNSET
    reason: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        output = self.output

        explanation = self.explanation

        expected_output = self.expected_output

        reasoning = self.reasoning

        reason = self.reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if output is not UNSET:
            field_dict["output"] = output
        if explanation is not UNSET:
            field_dict["explanation"] = explanation
        if expected_output is not UNSET:
            field_dict["expected_output"] = expected_output
        if reasoning is not UNSET:
            field_dict["reasoning"] = reasoning
        if reason is not UNSET:
            field_dict["reason"] = reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        output = d.pop("output", UNSET)

        explanation = d.pop("explanation", UNSET)

        expected_output = d.pop("expected_output", UNSET)

        reasoning = d.pop("reasoning", UNSET)

        reason = d.pop("reason", UNSET)

        ground_truth_role_mapping = cls(
            output=output,
            explanation=explanation,
            expected_output=expected_output,
            reasoning=reasoning,
            reason=reason,
        )

        ground_truth_role_mapping.additional_properties = d
        return ground_truth_role_mapping

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
