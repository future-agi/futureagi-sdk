from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.prompt_derived_variables_result_derived_variables import (
        PromptDerivedVariablesResultDerivedVariables,
    )


T = TypeVar("T", bound="PromptDerivedVariablesResult")


@_attrs_define
class PromptDerivedVariablesResult:
    """
    Attributes:
        version (str):
        derived_variables (PromptDerivedVariablesResultDerivedVariables):
    """

    version: str
    derived_variables: PromptDerivedVariablesResultDerivedVariables
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        version = self.version

        derived_variables = self.derived_variables.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "version": version,
                "derived_variables": derived_variables,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.prompt_derived_variables_result_derived_variables import (
            PromptDerivedVariablesResultDerivedVariables,
        )

        d = dict(src_dict)
        version = d.pop("version")

        derived_variables = PromptDerivedVariablesResultDerivedVariables.from_dict(
            d.pop("derived_variables")
        )

        prompt_derived_variables_result = cls(
            version=version,
            derived_variables=derived_variables,
        )

        prompt_derived_variables_result.additional_properties = d
        return prompt_derived_variables_result

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
