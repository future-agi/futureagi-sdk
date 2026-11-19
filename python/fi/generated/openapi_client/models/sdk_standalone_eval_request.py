from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sdk_standalone_eval_input import SDKStandaloneEvalInput
    from ..models.sdk_standalone_eval_request_config import (
        SDKStandaloneEvalRequestConfig,
    )


T = TypeVar("T", bound="SDKStandaloneEvalRequest")


@_attrs_define
class SDKStandaloneEvalRequest:
    """
    Attributes:
        inputs (list[SDKStandaloneEvalInput]):
        config (SDKStandaloneEvalRequestConfig):
        protect_flash (bool | Unset):  Default: False.
    """

    inputs: list[SDKStandaloneEvalInput]
    config: SDKStandaloneEvalRequestConfig
    protect_flash: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        inputs = []
        for inputs_item_data in self.inputs:
            inputs_item = inputs_item_data.to_dict()
            inputs.append(inputs_item)

        config = self.config.to_dict()

        protect_flash = self.protect_flash

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "inputs": inputs,
                "config": config,
            }
        )
        if protect_flash is not UNSET:
            field_dict["protect_flash"] = protect_flash

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sdk_standalone_eval_input import SDKStandaloneEvalInput
        from ..models.sdk_standalone_eval_request_config import (
            SDKStandaloneEvalRequestConfig,
        )

        d = dict(src_dict)
        inputs = []
        _inputs = d.pop("inputs")
        for inputs_item_data in _inputs:
            inputs_item = SDKStandaloneEvalInput.from_dict(inputs_item_data)

            inputs.append(inputs_item)

        config = SDKStandaloneEvalRequestConfig.from_dict(d.pop("config"))

        protect_flash = d.pop("protect_flash", UNSET)

        sdk_standalone_eval_request = cls(
            inputs=inputs,
            config=config,
            protect_flash=protect_flash,
        )

        sdk_standalone_eval_request.additional_properties = d
        return sdk_standalone_eval_request

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
