from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AutomationRuleEvaluateResult")


@_attrs_define
class AutomationRuleEvaluateResult:
    """
    Attributes:
        matched (int):
        added (int):
        duplicates (int):
        truncated (bool | Unset):
        error (str | Unset):
    """

    matched: int
    added: int
    duplicates: int
    truncated: bool | Unset = UNSET
    error: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        matched = self.matched

        added = self.added

        duplicates = self.duplicates

        truncated = self.truncated

        error = self.error

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "matched": matched,
                "added": added,
                "duplicates": duplicates,
            }
        )
        if truncated is not UNSET:
            field_dict["truncated"] = truncated
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        matched = d.pop("matched")

        added = d.pop("added")

        duplicates = d.pop("duplicates")

        truncated = d.pop("truncated", UNSET)

        error = d.pop("error", UNSET)

        automation_rule_evaluate_result = cls(
            matched=matched,
            added=added,
            duplicates=duplicates,
            truncated=truncated,
            error=error,
        )

        automation_rule_evaluate_result.additional_properties = d
        return automation_rule_evaluate_result

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
