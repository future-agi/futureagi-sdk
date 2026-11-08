from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.sdk_standalone_eval_result_item import SDKStandaloneEvalResultItem


T = TypeVar("T", bound="SDKStandaloneEvalResponse")


@_attrs_define
class SDKStandaloneEvalResponse:
    """
    Attributes:
        status (bool):
        result (list[SDKStandaloneEvalResultItem]):
    """

    status: bool
    result: list[SDKStandaloneEvalResultItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        result = []
        for result_item_data in self.result:
            result_item = result_item_data.to_dict()
            result.append(result_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
                "result": result,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sdk_standalone_eval_result_item import SDKStandaloneEvalResultItem

        d = dict(src_dict)
        status = d.pop("status")

        result = []
        _result = d.pop("result")
        for result_item_data in _result:
            result_item = SDKStandaloneEvalResultItem.from_dict(result_item_data)

            result.append(result_item)

        sdk_standalone_eval_response = cls(
            status=status,
            result=result,
        )

        sdk_standalone_eval_response.additional_properties = d
        return sdk_standalone_eval_response

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
