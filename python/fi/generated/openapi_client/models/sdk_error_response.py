from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sdk_error_response_errors import SDKErrorResponseErrors


T = TypeVar("T", bound="SDKErrorResponse")


@_attrs_define
class SDKErrorResponse:
    """
    Attributes:
        status (bool):
        result (None | str | Unset):
        message (None | str | Unset):
        errors (SDKErrorResponseErrors | Unset):
    """

    status: bool
    result: None | str | Unset = UNSET
    message: None | str | Unset = UNSET
    errors: SDKErrorResponseErrors | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        result: None | str | Unset
        if isinstance(self.result, Unset):
            result = UNSET
        else:
            result = self.result

        message: None | str | Unset
        if isinstance(self.message, Unset):
            message = UNSET
        else:
            message = self.message

        errors: dict[str, Any] | Unset = UNSET
        if not isinstance(self.errors, Unset):
            errors = self.errors.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
            }
        )
        if result is not UNSET:
            field_dict["result"] = result
        if message is not UNSET:
            field_dict["message"] = message
        if errors is not UNSET:
            field_dict["errors"] = errors

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sdk_error_response_errors import SDKErrorResponseErrors

        d = dict(src_dict)
        status = d.pop("status")

        def _parse_result(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        result = _parse_result(d.pop("result", UNSET))

        def _parse_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        message = _parse_message(d.pop("message", UNSET))

        _errors = d.pop("errors", UNSET)
        errors: SDKErrorResponseErrors | Unset
        if isinstance(_errors, Unset):
            errors = UNSET
        else:
            errors = SDKErrorResponseErrors.from_dict(_errors)

        sdk_error_response = cls(
            status=status,
            result=result,
            message=message,
            errors=errors,
        )

        sdk_error_response.additional_properties = d
        return sdk_error_response

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
