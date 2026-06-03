from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.persona import Persona


T = TypeVar("T", bound="PersonaDuplicateResponse")


@_attrs_define
class PersonaDuplicateResponse:
    """
    Attributes:
        status (bool | Unset):  Default: True.
        result (Persona | Unset):
    """

    status: bool | Unset = True
    result: Persona | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        result: dict[str, Any] | Unset = UNSET
        if not isinstance(self.result, Unset):
            result = self.result.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if status is not UNSET:
            field_dict["status"] = status
        if result is not UNSET:
            field_dict["result"] = result

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.persona import Persona

        d = dict(src_dict)
        status = d.pop("status", UNSET)

        _result = d.pop("result", UNSET)
        result: Persona | Unset
        if isinstance(_result, Unset):
            result = UNSET
        else:
            result = Persona.from_dict(_result)

        persona_duplicate_response = cls(
            status=status,
            result=result,
        )

        persona_duplicate_response.additional_properties = d
        return persona_duplicate_response

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
