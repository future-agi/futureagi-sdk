from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sdk_standalone_eval_input_additional_property import (
        SDKStandaloneEvalInputAdditionalProperty,
    )


T = TypeVar("T", bound="SDKStandaloneEvalInput")


@_attrs_define
class SDKStandaloneEvalInput:
    """
    Attributes:
        input_ (str | Unset):
        max_tokens (int | Unset):
    """

    input_: str | Unset = UNSET
    max_tokens: int | Unset = UNSET
    additional_properties: dict[str, SDKStandaloneEvalInputAdditionalProperty] = (
        _attrs_field(init=False, factory=dict)
    )

    def to_dict(self) -> dict[str, Any]:
        input_ = self.input_

        max_tokens = self.max_tokens

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = prop.to_dict()

        field_dict.update({})
        if input_ is not UNSET:
            field_dict["input"] = input_
        if max_tokens is not UNSET:
            field_dict["max_tokens"] = max_tokens

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sdk_standalone_eval_input_additional_property import (
            SDKStandaloneEvalInputAdditionalProperty,
        )

        d = dict(src_dict)
        input_ = d.pop("input", UNSET)

        max_tokens = d.pop("max_tokens", UNSET)

        sdk_standalone_eval_input = cls(
            input_=input_,
            max_tokens=max_tokens,
        )

        additional_properties = {}
        for prop_name, prop_dict in d.items():
            additional_property = SDKStandaloneEvalInputAdditionalProperty.from_dict(
                prop_dict
            )

            additional_properties[prop_name] = additional_property

        sdk_standalone_eval_input.additional_properties = additional_properties
        return sdk_standalone_eval_input

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> SDKStandaloneEvalInputAdditionalProperty:
        return self.additional_properties[key]

    def __setitem__(
        self, key: str, value: SDKStandaloneEvalInputAdditionalProperty
    ) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
