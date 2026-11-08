from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.sdk_standalone_eval_v2_result_result import (
        SDKStandaloneEvalV2ResultResult,
    )


T = TypeVar("T", bound="SDKStandaloneEvalV2Result")


@_attrs_define
class SDKStandaloneEvalV2Result:
    """
    Attributes:
        eval_status (str):
        result (SDKStandaloneEvalV2ResultResult):
    """

    eval_status: str
    result: SDKStandaloneEvalV2ResultResult
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        eval_status = self.eval_status

        result = self.result.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "eval_status": eval_status,
                "result": result,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sdk_standalone_eval_v2_result_result import (
            SDKStandaloneEvalV2ResultResult,
        )

        d = dict(src_dict)
        eval_status = d.pop("eval_status")

        result = SDKStandaloneEvalV2ResultResult.from_dict(d.pop("result"))

        sdk_standalone_eval_v2_result = cls(
            eval_status=eval_status,
            result=result,
        )

        sdk_standalone_eval_v2_result.additional_properties = d
        return sdk_standalone_eval_v2_result

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
